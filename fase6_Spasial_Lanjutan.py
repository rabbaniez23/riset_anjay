"""
FASE 6: SPASIAL LANJUTAN -- 6 Visualisasi
===============================================
  B1  -- Getis-Ord Gi* Hotspot Analysis
  V5  -- Local Moran's I (LISA Map)
  B4  -- Centroid Movement Analysis
  B6  -- Global Moran's I Temporal Trend
  G2  -- EEZ vs Non-EEZ Analysis
  G3  -- MPA Overlap Analysis

Semua indeks spasial (Gi*, Moran's I) dihitung MANUAL menggunakan
scipy.spatial.cKDTree sebagai pengganti libpysal/esda.

Input:
  pixel_grid_L2.csv     -> B1, V5, B4, B8, G2
  pixel_grid_all.csv    -> G2 (perbandingan EEZ vs non-EEZ)
  yearly_aggregated.csv -> B4 (centroid per tahun), B6

Output: output/fase6/*.png
"""

import matplotlib
matplotlib.use('Agg')

import os, sys, time, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
from scipy.spatial import cKDTree
from scipy import stats

warnings.filterwarnings('ignore')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ============================================================
# KONFIGURASI
# ============================================================
BASE      = r"e:\UNIVERSITAS PENDIDIKAN INDONESIA\PENELITIAN\FISHING GROUND PATTERN\riset_viirs"
OUT_DIR   = os.path.join(BASE, "output")
F6_DIR    = os.path.join(OUT_DIR, "fase6")
os.makedirs(F6_DIR, exist_ok=True)

GRID_L2   = os.path.join(OUT_DIR, "pixel_grid_L2.csv")
GRID_ALL  = os.path.join(OUT_DIR, "pixel_grid_all.csv")
YEARLY    = os.path.join(OUT_DIR, "yearly_aggregated.csv")
MONTHLY   = os.path.join(OUT_DIR, "monthly_aggregated.csv")

plt.rcParams.update({
    'font.size': 10, 'font.family': 'DejaVu Sans',
    'axes.titlesize': 11, 'axes.labelsize': 10,
    'figure.dpi': 150, 'savefig.dpi': 180,
    'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
})

OCEAN_BG = '#0B1D2A'   # warna laut gelap
MAP_XLIM  = (94, 142)
MAP_YLIM  = (-12, 7)

def format_map(ax, title):
    ax.set_xlim(*MAP_XLIM)
    ax.set_ylim(*MAP_YLIM)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title(title, pad=10, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.grid(True, color='gray', linestyle=':', alpha=0.4)

t0 = time.time()
print("=" * 68)
print("FASE 6: SPASIAL LANJUTAN -- 6 Visualisasi")
print("=" * 68)


# ============================================================
# HELPER: Subsample grid secara uniform (untuk efisiensi)
# ============================================================
def load_grid(n=None):
    """Memuat pixel_grid_L2 dengan subsampling opsional."""
    df = pd.read_csv(GRID_L2, dtype={
        'lat_grid': 'float32', 'lon_grid': 'float32',
        'freq_days': 'float32', 'log_rad_mean': 'float32',
        'is_L4': 'int8', 'is_L5': 'int8', 'is_L6': 'int8'
    })
    if n and len(df) > n:
        df = df.sample(n=n, random_state=42).reset_index(drop=True)
    return df


# ============================================================
# B1: GETIS-ORD Gi* HOTSPOT ANALYSIS
# ============================================================
def vis_B1():
    print("\n[1/6] B1 -- Getis-Ord Gi* Hotspot Analysis...")
    t = time.time()

    # Subsample 80k piksel (seimbang antara akurasi dan kecepatan)
    df = load_grid(n=80_000)
    df = df.dropna(subset=['lon_grid', 'lat_grid', 'freq_days'])

    coords  = df[['lon_grid', 'lat_grid']].values
    values  = df['freq_days'].values.astype(np.float64)

    n       = len(values)
    xbar    = values.mean()
    s       = values.std()

    # Bangun KDTree dengan radius tetangga = 2° (~220 km)
    tree    = cKDTree(coords)
    radius  = 2.0

    gi_star = np.zeros(n, dtype=np.float64)

    # Batch agar lebih cepat
    batch   = 2000
    for start in range(0, n, batch):
        end  = min(start + batch, n)
        pts  = coords[start:end]
        idxs = tree.query_ball_point(pts, r=radius)
        for k, neighbors in enumerate(idxs):
            if len(neighbors) < 2:
                gi_star[start + k] = 0.0
                continue
            xi    = values[neighbors]
            wi_j  = np.ones(len(neighbors))          # bobot biner sederhana
            W     = wi_j.sum()
            S1    = np.sum(xi * wi_j)
            S2    = np.sum(wi_j**2)

            num   = S1 - xbar * W
            denom = s * np.sqrt((n * S2 - W**2) / (n - 1))
            gi_star[start + k] = num / denom if denom != 0 else 0.0

    df['Gi_star'] = gi_star

    # Kategorikan: |z| > 2.58 = 99% CI, > 1.96 = 95% CI
    def gi_cat(z):
        if z > 2.58:   return 'Hot Spot 99%'
        if z > 1.96:   return 'Hot Spot 95%'
        if z < -2.58:  return 'Cold Spot 99%'
        if z < -1.96:  return 'Cold Spot 95%'
        return 'Not Significant'

    df['category'] = df['Gi_star'].apply(gi_cat)

    fig, ax = plt.subplots(figsize=(14, 6))

    # Base map abu-abu
    ax.scatter(df['lon_grid'], df['lat_grid'], color='#BDC3C7', s=0.1, alpha=0.3)

    palette = {
        'Hot Spot 99%':  '#E74C3C',
        'Hot Spot 95%':  '#F1948A',
        'Not Significant': '#95A5A6',
        'Cold Spot 95%': '#85C1E9',
        'Cold Spot 99%': '#2980B9',
    }
    for cat, color in palette.items():
        sub = df[df['category'] == cat]
        if len(sub) == 0: continue
        s_size = 2 if '99%' in cat else 0.8
        ax.scatter(sub['lon_grid'], sub['lat_grid'], color=color, s=s_size,
                   alpha=0.9, label=f'{cat} (n={len(sub):,})')

    format_map(ax, 'B1 · Getis-Ord Gi* Hotspot Analysis\nKlaster Statistik Area Penangkapan Ikan Tinggi (Hot) vs Rendah (Cold)')
    leg = ax.legend(loc='lower left', markerscale=8, fontsize=8,
                    facecolor='white', framealpha=0.9)

    out = os.path.join(F6_DIR, 'B1_getis_ord_gi_star.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# V5: LOCAL MORAN'S I (LISA MAP)
# ============================================================
def vis_V5():
    print("\n[2/6] V5 -- Local Moran's I (LISA Map)...")
    t = time.time()

    df = load_grid(n=60_000)
    df = df.dropna(subset=['lon_grid', 'lat_grid', 'freq_days'])

    coords  = df[['lon_grid', 'lat_grid']].values
    values  = df['freq_days'].values.astype(np.float64)
    n       = len(values)

    # Z-standarisasi nilai
    z_vals  = (values - values.mean()) / values.std()

    # KDTree k-nearest neighbors (k=8 tetangga)
    tree    = cKDTree(coords)
    K       = 8
    dists, idxs = tree.query(coords, k=K+1)  # +1 karena titik itu sendiri selalu masuk
    idxs    = idxs[:, 1:]                     # hapus self

    # Hitung Local Moran's I untuk setiap titik
    li      = np.zeros(n)
    lag_z   = np.zeros(n)   # spatial lag (rata-rata nilai tetangga)
    for i in range(n):
        neighbors = idxs[i]
        lag_z[i]  = z_vals[neighbors].mean()
        li[i]     = z_vals[i] * lag_z[i]

    # Klasifikasi LISA (4 kuadran): HH, LL, HL, LH
    def lisa_type(zi, lag_zi):
        if zi > 0 and lag_zi > 0: return 'HH (High-High)'
        if zi < 0 and lag_zi < 0: return 'LL (Low-Low)'
        if zi > 0 and lag_zi < 0: return 'HL (High-Low)'
        return 'LH (Low-High)'

    df['LISA'] = [lisa_type(z_vals[i], lag_z[i]) for i in range(n)]
    df['LI']   = li

    palette = {
        'HH (High-High)': '#E74C3C',   # merah (kluster tinggi)
        'LL (Low-Low)':   '#2980B9',   # biru (kluster rendah)
        'HL (High-Low)':  '#F39C12',   # oranye (outlier tinggi)
        'LH (Low-High)':  '#1ABC9C',   # hijau (outlier rendah)
    }

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('V5 · Local Moran\'s I — LISA Map\nKlaster Spasial dan Outlier Aktivitas Penangkapan Ikan (k=8 Tetangga)',
                 fontsize=12, fontweight='bold', y=1.02)

    # Panel kiri: Peta LISA
    ax = axes[0]
    ax.scatter(df['lon_grid'], df['lat_grid'], color='#BDC3C7', s=0.08, alpha=0.2)
    for cat, color in palette.items():
        sub = df[df['LISA'] == cat]
        if len(sub) == 0: continue
        ax.scatter(sub['lon_grid'], sub['lat_grid'], color=color, s=0.8,
                   alpha=0.9, label=f'{cat} (n={len(sub):,})')
    format_map(ax, 'Peta Tipe LISA (Spatial Cluster & Outlier)')
    ax.legend(loc='lower left', markerscale=8, fontsize=8, facecolor='white')

    # Panel kanan: Moran Scatter Plot
    ax2 = axes[1]
    ax2.set_facecolor('#FAFAFA')
    for cat, color in palette.items():
        sub = df[df['LISA'] == cat]
        ax2.scatter(z_vals[sub.index], lag_z[sub.index], color=color,
                    alpha=0.5, s=3, label=cat)
    ax2.axhline(0, color='black', linewidth=1)
    ax2.axvline(0, color='black', linewidth=1)
    ax2.set_xlabel('Standarisasi Nilai (z_i)', fontsize=10)
    ax2.set_ylabel('Spatial Lag — Rata-rata Tetangga (W·z_i)', fontsize=10)
    ax2.set_title('Moran Scatter Plot (z vs Spatial Lag)', fontsize=10)
    ax2.grid(True, alpha=0.3)

    # Tambahkan label kuadran
    for txt, xy in [('HH', (1.5, 1.5)), ('LL', (-1.5, -1.5)),
                    ('HL', (1.5, -1.5)), ('LH', (-1.5, 1.5))]:
        ax2.text(xy[0], xy[1], txt, fontsize=12, fontweight='bold', alpha=0.3,
                 ha='center', va='center')

    plt.tight_layout()
    out = os.path.join(F6_DIR, 'V5_lisa_map.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# B4: CENTROID MOVEMENT ANALYSIS
# ============================================================
def vis_B4():
    print("\n[3/6] B4 -- Centroid Movement Analysis...")
    t = time.time()

    df = pd.read_csv(YEARLY)
    df = df[df['is_partial_year'] == 0]

    # Centroid terbobot = rata-rata lat/lon * bobot detection_count
    # Diperlukan kolom lat_centroid & lon_centroid per WPP
    # Kalkulasi dari posisi tengah bounding box WPP (empiris)
    WPP_CENTER = {
        'WPP571': (-1.0, 100.5), 'WPP572': (-1.5, 106.5), 'WPP573': (-2.5, 112.0),
        'WPP711': (4.0, 107.0),  'WPP712': (-5.0, 112.0), 'WPP713': (-3.0, 122.0),
        'WPP714': (-2.5, 131.5), 'WPP715': (-6.0, 123.5), 'WPP716': (-6.5, 132.0),
        'WPP717': (-2.0, 138.0), 'WPP718': (-6.0, 136.0),
    }
    df['lat_c'] = df['wpp'].map({k: v[0] for k, v in WPP_CENTER.items()})
    df['lon_c'] = df['wpp'].map({k: v[1] for k, v in WPP_CENTER.items()})
    df = df.dropna(subset=['lat_c', 'lon_c'])

    # Centroid nasional per tahun (weighted mean)
    yearly_cent = df.groupby('year').apply(
        lambda x: pd.Series({
            'lat_centroid': np.average(x['lat_c'], weights=x['detection_count']),
            'lon_centroid': np.average(x['lon_c'], weights=x['detection_count']),
            'total': x['detection_count'].sum()
        })
    ).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('B4 · Analisis Pergerakan Centroid Aktivitas Penangkapan Ikan (Nasional)\n'
                 'Apakah Episentrum Penangkapan Bergeser Seiring Waktu?',
                 fontsize=12, fontweight='bold', y=1.02)

    # Panel kiri: Peta pergerakan centroid
    ax = axes[0]
    ax.set_facecolor('#EAF4FF')
    ax.scatter(df['lon_c'], df['lat_c'],
               color='#BDC3C7', s=50, alpha=0.3, zorder=1, label='Posisi WPP')

    lats = yearly_cent['lat_centroid'].values
    lons = yearly_cent['lon_centroid'].values
    years = yearly_cent['year'].values

    cmap = plt.cm.plasma
    norm = mcolors.Normalize(vmin=years.min(), vmax=years.max())

    # Garis jejak
    for i in range(len(lons) - 1):
        c = cmap(norm(years[i]))
        ax.annotate('', xy=(lons[i+1], lats[i+1]), xytext=(lons[i], lats[i]),
                    arrowprops=dict(arrowstyle='->', color=c, lw=2))

    sc = ax.scatter(lons, lats, c=years, cmap='plasma', s=80, zorder=3, edgecolors='black', linewidths=0.5)
    for i, yr in enumerate(years):
        ax.annotate(str(yr), (lons[i], lats[i]), textcoords='offset points',
                    xytext=(4, 4), fontsize=7)

    plt.colorbar(sc, ax=ax, label='Tahun')
    ax.set_xlim(96, 140)
    ax.set_ylim(-10, 6)
    ax.set_aspect('equal')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.grid(True, alpha=0.3)
    ax.set_title('Trajektori Pergerakan Centroid Nasional (2012–2025)', fontsize=10)

    # Panel kanan: Tren Lat & Lon centroid per tahun
    ax2 = axes[1]
    ax2.set_facecolor('#FAFAFA')
    ax2.plot(years, lons, marker='o', color='#2980B9', linewidth=2, label='Longitude Centroid')
    ax2_r = ax2.twinx()
    ax2_r.plot(years, lats, marker='s', color='#E74C3C', linewidth=2, linestyle='--', label='Latitude Centroid')
    ax2.set_xlabel('Tahun')
    ax2.set_ylabel('Longitude (°E)', color='#2980B9')
    ax2_r.set_ylabel('Latitude (°)', color='#E74C3C')
    ax2.set_title('Tren Koordinat Centroid Nasional per Tahun', fontsize=10)
    ax2.grid(True, alpha=0.3)
    # Combined legend
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_r.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='lower right', fontsize=9)

    plt.tight_layout()
    out = os.path.join(F6_DIR, 'B4_centroid_movement.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# B6: GLOBAL MORAN'S I TEMPORAL TREND
# ============================================================
def vis_B6():
    print("\n[4/6] B6 -- Global Moran's I Temporal Trend...")
    t = time.time()

    monthly = pd.read_csv(MONTHLY)
    monthly = monthly[monthly['is_partial_year'] == 0]

    WPP_CENTER = {
        'WPP571': (-1.0, 100.5), 'WPP572': (-1.5, 106.5), 'WPP573': (-2.5, 112.0),
        'WPP711': (4.0, 107.0),  'WPP712': (-5.0, 112.0), 'WPP713': (-3.0, 122.0),
        'WPP714': (-2.5, 131.5), 'WPP715': (-6.0, 123.5), 'WPP716': (-6.5, 132.0),
        'WPP717': (-2.0, 138.0), 'WPP718': (-6.0, 136.0),
    }
    monthly = monthly[monthly['wpp'].isin(WPP_CENTER)]
    monthly['lat_c'] = monthly['wpp'].map({k: v[0] for k, v in WPP_CENTER.items()})
    monthly['lon_c'] = monthly['wpp'].map({k: v[1] for k, v in WPP_CENTER.items()})

    def global_morans_i(vals, coords):
        n = len(vals)
        if n < 3:
            return np.nan
        z = vals - vals.mean()
        # Bobot W = 1/distance
        from scipy.spatial.distance import cdist
        D = cdist(coords, coords)
        np.fill_diagonal(D, np.inf)
        W = 1.0 / D
        W_sum = W.sum()
        # I = (n / W_sum) * (z @ W @ z) / (z @ z)
        numerator = z @ (W @ z)
        denom     = z @ z
        if denom == 0:
            return 0.0
        return (n / W_sum) * (numerator / denom)

    # Hitung I per tahun
    results = []
    for year in sorted(monthly['year'].unique()):
        sub = monthly[monthly['year'] == year].groupby('wpp').agg(
            det=('detection_count', 'mean'),
            lat=('lat_c', 'first'),
            lon=('lon_c', 'first')
        ).reset_index().dropna()
        if len(sub) < 3:
            continue
        vals   = sub['det'].values
        coords = sub[['lat', 'lon']].values
        I = global_morans_i(vals, coords)
        results.append({'year': year, 'morans_I': I})

    res_df = pd.DataFrame(results)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle('B6 · Tren Global Moran\'s I Tahunan\n'
                 'Seberapa Kuat Pengelompokan Spasial Berubah dari Tahun ke Tahun?',
                 fontsize=12, fontweight='bold', y=0.98)

    ax.plot(res_df['year'], res_df['morans_I'], marker='o', color='#8E44AD', linewidth=2.5)
    ax.axhline(0, color='black', linewidth=1, linestyle='--', label='I=0 (Acak Sempurna)')
    ax.fill_between(res_df['year'], 0, res_df['morans_I'],
                    where=(res_df['morans_I'] > 0), alpha=0.2, color='#E74C3C', label='Positif (Kluster)')
    ax.fill_between(res_df['year'], 0, res_df['morans_I'],
                    where=(res_df['morans_I'] < 0), alpha=0.2, color='#2980B9', label='Negatif (Dispersi)')

    # Anotasi nilai I
    for _, row in res_df.iterrows():
        ax.text(row['year'], row['morans_I'] + 0.005, f"{row['morans_I']:.2f}",
                ha='center', va='bottom', fontsize=8)

    ax.set_xlabel('Tahun')
    ax.set_ylabel("Global Moran's I")
    ax.set_xticks(res_df['year'])
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)

    plt.tight_layout()
    out = os.path.join(F6_DIR, 'B6_global_morans_i.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# G2: EEZ vs NON-EEZ ANALYSIS
# ============================================================
def vis_G2():
    print("\n[5/6] G2 -- EEZ vs Non-EEZ Analysis...")
    t = time.time()

    # pixel_grid_all memiliki seluruh piksel (termasuk luar EEZ)
    dfall = pd.read_csv(GRID_ALL, usecols=['lat_grid', 'lon_grid', 'freq_days', 'wpp_dominant'],
                        dtype={'lat_grid': 'float32', 'lon_grid': 'float32',
                               'freq_days': 'float32'})

    # Tandai EEZ vs non-EEZ
    dfall['is_eez'] = dfall['wpp_dominant'].notna() & (dfall['wpp_dominant'] != 'Unknown')

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('G2 · Analisis EEZ vs Non-EEZ\nPerbandingan Distribusi Aktivitas di Dalam dan di Luar Zona Ekonomi Eksklusif Indonesia',
                 fontsize=12, fontweight='bold', y=1.02)

    # Panel 1: Peta sebaran EEZ vs non-EEZ
    ax = axes[0]
    eez     = dfall[dfall['is_eez']]
    non_eez = dfall[~dfall['is_eez']]
    ax.scatter(non_eez['lon_grid'], non_eez['lat_grid'], c='#E74C3C', s=0.2, alpha=0.3, label=f'Non-EEZ (n={len(non_eez):,})')
    ax.scatter(eez['lon_grid'], eez['lat_grid'], c='#27AE60', s=0.2, alpha=0.3, label=f'EEZ Indonesia (n={len(eez):,})')
    ax.set_xlim(*MAP_XLIM); ax.set_ylim(*MAP_YLIM)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('Sebaran Spasial EEZ vs Non-EEZ', fontsize=10)
    ax.legend(loc='lower left', markerscale=10, fontsize=8)

    # Panel 2: Distribusi freq_days EEZ vs non-EEZ (KDE)
    ax2 = axes[1]
    ax2.set_facecolor('#FAFAFA')
    sample_eez = eez['freq_days'].dropna().sample(min(50_000, len(eez)), random_state=42)
    sample_ne  = non_eez['freq_days'].dropna().sample(min(50_000, len(non_eez)), random_state=42)
    ax2.hist(np.log1p(sample_eez), bins=60, color='#27AE60', alpha=0.6, density=True, label='EEZ')
    ax2.hist(np.log1p(sample_ne),  bins=60, color='#E74C3C', alpha=0.6, density=True, label='Non-EEZ')
    ax2.set_xlabel('log(1 + Frekuensi Hari Deteksi)')
    ax2.set_ylabel('Densitas Probabilitas')
    ax2.set_title('Distribusi Frekuensi Deteksi:\nEEZ vs Non-EEZ', fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    # Panel 3: Bar chart statistik ringkas
    ax3 = axes[2]
    ax3.set_facecolor('#FAFAFA')
    stats_data = {
        'Total Piksel': [len(eez), len(non_eez)],
        'Median Hari': [eez['freq_days'].median(), non_eez['freq_days'].median()],
        'Mean Hari': [eez['freq_days'].mean(), non_eez['freq_days'].mean()],
    }
    x = np.arange(3)
    w = 0.35
    bars1 = ax3.bar(x - w/2, [stats_data[k][0] for k in stats_data], w, label='EEZ', color='#27AE60', alpha=0.8)
    bars2 = ax3.bar(x + w/2, [stats_data[k][1] for k in stats_data], w, label='Non-EEZ', color='#E74C3C', alpha=0.8)
    ax3.set_yscale('log')
    ax3.set_xticks(x)
    ax3.set_xticklabels(stats_data.keys(), rotation=15, ha='right')
    ax3.set_ylabel('Nilai (log scale)')
    ax3.set_title('Statistik Ringkas: EEZ vs Non-EEZ', fontsize=10)
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    out = os.path.join(F6_DIR, 'G2_eez_vs_non_eez.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# G3: MPA OVERLAP ANALYSIS (Simulasi berbasis Koordinat Resmi)
# ============================================================
def vis_G3():
    print("\n[6/6] G3 -- MPA Overlap Analysis...")
    t = time.time()

    # Koordinat bounding-box MPA/KKP terbesar Indonesia (sumber: UNEP-WCMC & KKP)
    MPAS = [
        {'name': 'Kawasan Konservasi\nLaut Natuna',      'lon_c': 106.1, 'lat_c': 3.5,  'r_lon': 1.5, 'r_lat': 1.2},
        {'name': 'KKP Banda &\nLaut Seram',              'lon_c': 128.5, 'lat_c': -4.5, 'r_lon': 2.5, 'r_lat': 2.0},
        {'name': 'TWAL Selat\nMakassar',                 'lon_c': 117.5, 'lat_c': -1.5, 'r_lon': 1.2, 'r_lat': 1.5},
        {'name': 'KKP Cendrawasih\n(Papua)',             'lon_c': 134.5, 'lat_c': -2.0, 'r_lon': 1.5, 'r_lat': 1.0},
        {'name': 'KKP Kepulauan\nAnambas',               'lon_c': 105.8, 'lat_c': 3.0,  'r_lon': 0.6, 'r_lat': 0.5},
        {'name': 'TNKJ Karimun\nJawa',                   'lon_c': 110.4, 'lat_c': -5.8, 'r_lon': 0.5, 'r_lat': 0.4},
        {'name': 'Taman Nasional\nBunaken',              'lon_c': 124.7, 'lat_c': 1.6,  'r_lon': 0.4, 'r_lat': 0.3},
    ]

    df = load_grid(n=100_000)
    df = df.dropna(subset=['lon_grid', 'lat_grid', 'freq_days'])

    # Tandai piksel yang berada di dalam bounding box MPA manapun
    df['in_mpa'] = False
    df['mpa_name'] = 'Di Luar MPA'
    for mpa in MPAS:
        mask = (
            (df['lon_grid'] >= mpa['lon_c'] - mpa['r_lon']) &
            (df['lon_grid'] <= mpa['lon_c'] + mpa['r_lon']) &
            (df['lat_grid'] >= mpa['lat_c'] - mpa['r_lat']) &
            (df['lat_grid'] <= mpa['lat_c'] + mpa['r_lat'])
        )
        df.loc[mask, 'in_mpa']   = True
        df.loc[mask, 'mpa_name'] = mpa['name']

    in_mpa     = df[df['in_mpa']]
    out_mpa_df = df[~df['in_mpa']]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('G3 · MPA Overlap Analysis\n'
                 'Tumpang-Tindih Aktivitas Penangkapan Ikan dengan Kawasan Konservasi Laut (KKP)',
                 fontsize=12, fontweight='bold', y=1.02)

    # Panel kiri: Peta tumpang tindih
    ax = axes[0]
    ax.scatter(out_mpa_df['lon_grid'], out_mpa_df['lat_grid'],
               c='#2C3E50', s=0.08, alpha=0.2, label='Di Luar MPA')

    if len(in_mpa) > 0:
        sc = ax.scatter(in_mpa['lon_grid'], in_mpa['lat_grid'],
                        c=in_mpa['freq_days'], cmap='hot_r', s=1.5, alpha=0.9,
                        vmin=22, label='Overlap dgn MPA')
        plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.02, label='Hari Deteksi')

    # Gambar batas MPA
    from matplotlib.patches import Ellipse
    for mpa in MPAS:
        ell = Ellipse((mpa['lon_c'], mpa['lat_c']),
                      2*mpa['r_lon'], 2*mpa['r_lat'],
                      fill=False, edgecolor='cyan', linewidth=1.5, linestyle='--', zorder=5)
        ax.add_patch(ell)
        ax.text(mpa['lon_c'], mpa['lat_c'] + mpa['r_lat'] + 0.15,
                mpa['name'], fontsize=7, ha='center', color='cyan')

    format_map(ax, 'Tumpang-Tindih Fishing Grounds dan MPA Indonesia')
    ax.legend(loc='lower left', markerscale=8, fontsize=8)

    # Panel kanan: Statistik tingkat penetrasi
    ax2 = axes[1]
    ax2.set_facecolor('#FAFAFA')

    mpa_stats = in_mpa.groupby('mpa_name').agg(
        n_pixels=('freq_days', 'count'),
        median_freq=('freq_days', 'median'),
        mean_freq=('freq_days', 'mean')
    ).reset_index().sort_values('n_pixels', ascending=True)

    ax2.barh(mpa_stats['mpa_name'], mpa_stats['n_pixels'], color='#E74C3C', alpha=0.8)
    ax2.set_xlabel('Jumlah Piksel L2 yang Overlap')
    ax2.set_title('Tingkat Penetrasi Penangkapan\ndi Area MPA (n Piksel Terdeteksi)', fontsize=10)
    ax2.grid(True, alpha=0.3, axis='x')

    for i, (_, row) in enumerate(mpa_stats.iterrows()):
        ax2.text(row['n_pixels'] + 5, i, f"Med={row['median_freq']:.0f}hr",
                 va='center', fontsize=8)

    plt.tight_layout()
    out = os.path.join(F6_DIR, 'G3_mpa_overlap.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    results = {}
    results['B1'] = vis_B1()
    results['V5'] = vis_V5()
    results['B4'] = vis_B4()
    results['B6'] = vis_B6()
    results['G2'] = vis_G2()
    results['G3'] = vis_G3()

    elapsed = time.time() - t0
    print()
    print("=" * 68)
    print(f"FASE 6 SELESAI -- {elapsed:.0f} detik")
    print("=" * 68)
    for code, path in results.items():
        status = "OK" if path else "SKIP"
        print(f"  [{status}] {code}: {os.path.basename(path) if path else '-'}")
    print(f"\nSemua gambar di: {F6_DIR}")
    print("=" * 68)
