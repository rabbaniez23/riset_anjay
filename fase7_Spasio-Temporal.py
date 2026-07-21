"""
FASE 7: SPATIO-TEMPORAL -- 6 Visualisasi Flagship
===============================================
  C2  -- 4 Musim Panel Map (flagship)
  C1  -- 12 Panel Monthly KDE (flagship)
  C3  -- Yearly Evolution Panel (flagship)
  C6  -- Persistent Hotspot Map (flagship)
  C7  -- Hotspot Emergence Map
  F1  -- Active Fishing Month Map (flagship)

Strategi:
- Peta spasial menggunakan pixel_grid_L2.csv sebagai ocean-mask backdrop
- Data temporal dari monthly_aggregated.csv dan yearly_aggregated.csv
- Aktivitas WPP divisualisasikan sebagai bubble di atas backdrop peta

Input:
  pixel_grid_L2.csv       -> ocean backdrop + C6/C7
  monthly_aggregated.csv  -> C1, C2, F1
  yearly_aggregated.csv   -> C3, C7

Output: output/fase7/*.png
"""

import matplotlib
matplotlib.use('Agg')

import os, sys, time, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.cm as cm
import seaborn as sns

warnings.filterwarnings('ignore')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ============================================================
# KONFIGURASI
# ============================================================
BASE     = r"e:\UNIVERSITAS PENDIDIKAN INDONESIA\PENELITIAN\FISHING GROUND PATTERN\riset_viirs"
OUT_DIR  = os.path.join(BASE, "output")
F7_DIR   = os.path.join(OUT_DIR, "fase7")
os.makedirs(F7_DIR, exist_ok=True)

GRID_L2  = os.path.join(OUT_DIR, "pixel_grid_L2.csv")
MONTHLY  = os.path.join(OUT_DIR, "monthly_aggregated.csv")
YEARLY   = os.path.join(OUT_DIR, "yearly_aggregated.csv")

# Koordinat dan batas tiap WPP (pusat geografis, untuk bubble di peta)
WPP_META = {
    'WPP571': {'lat': -1.0,  'lon': 100.5, 'label': 'WPP 571\n(Samudera Hindia\n& Selat Malaka)'},
    'WPP572': {'lat': -1.5,  'lon': 106.5, 'label': 'WPP 572\n(Selat Karimata\n& Laut Natuna)'},
    'WPP573': {'lat': -2.5,  'lon': 112.0, 'label': 'WPP 573\n(Laut Jawa)'},
    'WPP711': {'lat':  4.0,  'lon': 107.0, 'label': 'WPP 711\n(Selat Malaka\n& Laut Andaman)'},
    'WPP712': {'lat': -5.0,  'lon': 112.0, 'label': 'WPP 712\n(Laut Jawa)'},
    'WPP713': {'lat': -3.0,  'lon': 122.0, 'label': 'WPP 713\n(Laut Flores\n& Banda)'},
    'WPP714': {'lat': -2.5,  'lon': 131.5, 'label': 'WPP 714\n(Laut Banda &\nMaluku)'},
    'WPP715': {'lat': -6.0,  'lon': 123.5, 'label': 'WPP 715\n(Laut Maluku\n& Halmahera)'},
    'WPP716': {'lat': -6.5,  'lon': 132.0, 'label': 'WPP 716\n(Laut Sulawesi)'},
    'WPP717': {'lat': -2.0,  'lon': 138.0, 'label': 'WPP 717\n(Samudra\nPasifik)'},
    'WPP718': {'lat': -6.0,  'lon': 136.0, 'label': 'WPP 718\n(Laut Arafura\n& Timor)'},
}

MONTH_NAMES = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'Mei',6:'Jun',
               7:'Jul',8:'Agu',9:'Sep',10:'Okt',11:'Nov',12:'Des'}

SEASON_DEF = {
    'Musim Barat\n(DJF: Des–Feb)':   [12, 1, 2],
    'Pancaroba I\n(MAM: Mar–Mei)':   [3,  4, 5],
    'Musim Timur\n(JJA: Jun–Agu)':   [6,  7, 8],
    'Pancaroba II\n(SON: Sep–Nov)':   [9, 10, 11],
}

plt.rcParams.update({
    'font.size': 9, 'font.family': 'DejaVu Sans',
    'axes.titlesize': 10, 'axes.labelsize': 9,
    'figure.dpi': 120, 'savefig.dpi': 180,
    'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
})

t0 = time.time()
print("=" * 68)
print("FASE 7: SPATIO-TEMPORAL -- 6 Visualisasi Flagship")
print("=" * 68)


# ============================================================
# HELPERS
# ============================================================
def load_ocean_mask(n=60_000):
    """Load subsample pixel_grid_L2 untuk backdrop peta."""
    df = pd.read_csv(GRID_L2, usecols=['lat_grid','lon_grid'],
                     dtype={'lat_grid':'float32','lon_grid':'float32'})
    if len(df) > n:
        df = df.sample(n=n, random_state=42)
    return df

def draw_ocean(ax, mask_df, color='#D6EAF8', s=0.08, alpha=0.25):
    """Gambar backdrop 'laut' dari titik-titik grid."""
    ax.scatter(mask_df['lon_grid'], mask_df['lat_grid'],
               c=color, s=s, alpha=alpha, rasterized=True)

def format_map(ax, title='', xlim=(94,142), ylim=(-12,7)):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect('equal', adjustable='box')
    if title:
        ax.set_title(title, pad=6, fontweight='bold', fontsize=9)
    ax.tick_params(labelsize=7)
    ax.grid(True, color='#BDC3C7', linestyle=':', alpha=0.4)
    ax.set_facecolor('#F0F4F8')

def wpp_bubbles(ax, wpp_data, cmap='YlOrRd', vmin=None, vmax=None,
                size_scale=6000, edgecolor='#555', label_col=None):
    """Plot bubble per WPP di atas peta.
    wpp_data: dict {wpp_code: value} atau Series.
    """
    values = []
    lons, lats, vals, labels = [], [], [], []
    for wpp, meta in WPP_META.items():
        v = wpp_data.get(wpp, 0) if hasattr(wpp_data, 'get') else wpp_data.get(wpp, 0)
        values.append(v)
        lons.append(meta['lon'])
        lats.append(meta['lat'])
        vals.append(v)
        labels.append(wpp)

    vals  = np.array(vals, dtype=float)
    if vmin is None: vmin = vals.min()
    if vmax is None: vmax = max(vals.max(), 1)

    norm  = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap_ = cm.get_cmap(cmap)
    colors = [cmap_(norm(v)) for v in vals]

    # Normalisasi ukuran bubble
    sz_norm = (vals - vmin) / (vmax - vmin + 1e-9)
    sizes   = 30 + sz_norm * size_scale

    sc = ax.scatter(lons, lats, c=colors, s=sizes,
                    edgecolors=edgecolor, linewidths=0.5, alpha=0.85, zorder=5)
    return sc, norm, cmap_


def load_monthly_clean():
    df = pd.read_csv(MONTHLY)
    return df[(df['month'] > 0) & (df['is_partial_year'] == 0) &
              df['wpp'].isin(WPP_META.keys())].copy()


# ============================================================
# C2: 4 MUSIM PANEL MAP
# ============================================================
def vis_C2():
    print("\n[1/6] C2 -- 4 Musim Panel Map...")
    t = time.time()

    df   = load_monthly_clean()
    mask = load_ocean_mask()

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        'C2 · Panel Musiman: Distribusi Spasial Aktivitas Penangkapan Ikan\n'
        'Perbandingan 4 Musim – Musim Barat (DJF) | Pancaroba I (MAM) | Musim Timur (JJA) | Pancaroba II (SON)',
        fontsize=11, fontweight='bold', y=0.98)
    axes = axes.flatten()

    all_vals = []
    season_data = {}
    for season_name, months in SEASON_DEF.items():
        sub = df[df['month'].isin(months)].groupby('wpp')['detection_count'].sum()
        season_data[season_name] = sub
        all_vals.extend(sub.values)

    vmax = np.percentile(all_vals, 95)

    for i, (season_name, months) in enumerate(SEASON_DEF.items()):
        ax = axes[i]
        draw_ocean(ax, mask)
        sub = season_data[season_name]
        sc, norm, cmap_ = wpp_bubbles(ax, sub.to_dict(), cmap='YlOrRd',
                                       vmin=0, vmax=vmax, size_scale=5000)
        format_map(ax, title=season_name)

        # Colorbar per panel
        sm = cm.ScalarMappable(cmap=cmap_, norm=norm)
        sm.set_array([])
        cb = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
        cb.ax.tick_params(labelsize=7)
        cb.set_label('Total Deteksi', fontsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out = os.path.join(F7_DIR, 'C2_4season_panel.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# C1: 12 PANEL MONTHLY KDE
# ============================================================
def vis_C1():
    print("\n[2/6] C1 -- 12 Panel Monthly KDE...")
    t = time.time()

    df   = load_monthly_clean()
    mask = load_ocean_mask(n=30_000)

    fig, axes = plt.subplots(3, 4, figsize=(20, 12))
    fig.suptitle(
        'C1 · Peta Distribusi Bulanan Aktivitas Penangkapan Ikan (Rata-rata 2012–2025)\n'
        '12 Panel Bulanan – Deteksi Kapal per WPP per Bulan',
        fontsize=12, fontweight='bold', y=0.99)
    axes = axes.flatten()

    monthly_mean = df.groupby(['month','wpp'])['detection_count'].mean()
    vmax = monthly_mean.max() * 0.8

    for i, month in enumerate(range(1, 13)):
        ax = axes[i]
        draw_ocean(ax, mask, s=0.06, alpha=0.2)
        sub = monthly_mean[month] if month in monthly_mean.index else {}
        sc, norm, cmap_ = wpp_bubbles(ax, sub.to_dict() if hasattr(sub,'to_dict') else {},
                                       cmap='plasma', vmin=0, vmax=vmax, size_scale=4000)
        format_map(ax, title=f'{MONTH_NAMES[month]}')
        ax.set_xlabel('')
        ax.set_ylabel('')

    # Colorbar bersama
    sm = cm.ScalarMappable(cmap='plasma', norm=mcolors.Normalize(0, vmax))
    sm.set_array([])
    fig.subplots_adjust(right=0.92, top=0.95)
    cbar_ax = fig.add_axes([0.94, 0.1, 0.015, 0.8])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label('Rata-rata Deteksi per Bulan', fontsize=10)

    out = os.path.join(F7_DIR, 'C1_12month_panel.png')
    plt.savefig(out, facecolor='white', bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# C3: YEARLY EVOLUTION PANEL
# ============================================================
def vis_C3():
    print("\n[3/6] C3 -- Yearly Evolution Panel...")
    t = time.time()

    df = pd.read_csv(YEARLY)
    df = df[(df['is_partial_year'] == 0) & df['wpp'].isin(WPP_META.keys())]
    mask = load_ocean_mask(n=25_000)

    years = sorted(df['year'].unique())
    # Buat layout 2×7 (14 tahun)
    n_years = len(years)
    ncols = 7
    nrows = int(np.ceil(n_years / ncols))

    vmax = df.groupby(['year','wpp'])['detection_count'].sum().quantile(0.90)

    fig, axes = plt.subplots(nrows, ncols, figsize=(22, nrows * 4))
    fig.suptitle(
        'C3 · Evolusi Tahunan Distribusi Spasial Aktivitas Penangkapan Ikan\n'
        'Perubahan Pola 2012–2025 per Wilayah Pengelolaan Perikanan (WPP)',
        fontsize=13, fontweight='bold', y=0.99)
    axes = axes.flatten() if nrows > 1 else axes

    for i, year in enumerate(years):
        ax = axes[i]
        draw_ocean(ax, mask, s=0.05, alpha=0.15)
        sub = df[df['year'] == year].groupby('wpp')['detection_count'].sum()
        wpp_bubbles(ax, sub.to_dict(), cmap='YlOrRd',
                    vmin=0, vmax=vmax, size_scale=3500)
        format_map(ax, title=str(year))
        ax.set_xlabel('')
        ax.set_ylabel('')

    # Hapus panel kosong
    for j in range(len(years), len(axes)):
        axes[j].set_visible(False)

    sm = cm.ScalarMappable(cmap='YlOrRd', norm=mcolors.Normalize(0, vmax))
    sm.set_array([])
    fig.subplots_adjust(right=0.91, top=0.94)
    cbar_ax = fig.add_axes([0.93, 0.05, 0.012, 0.85])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label('Total Deteksi per Tahun', fontsize=10)

    out = os.path.join(F7_DIR, 'C3_yearly_evolution.png')
    plt.savefig(out, facecolor='white', bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# C6: PERSISTENT HOTSPOT MAP
# ============================================================
def vis_C6():
    print("\n[4/6] C6 -- Persistent Hotspot Map...")
    t = time.time()

    df = pd.read_csv(GRID_L2, dtype={'lat_grid':'float32','lon_grid':'float32',
                                     'freq_days':'float32','is_L4':'int8',
                                     'is_L5':'int8','is_L6':'int8'})

    fig, ax = plt.subplots(figsize=(15, 7))

    # Layer 1: Background L2 (semua area persistent)
    l2_bg = df.sample(n=min(80_000, len(df)), random_state=42)
    ax.scatter(l2_bg['lon_grid'], l2_bg['lat_grid'],
               c='#D6EAF8', s=0.08, alpha=0.3, rasterized=True, label='L2/L3 (Moderate Persistent)')

    # Layer 2: L4 (High — top 25%)
    l4 = df[(df['is_L4']==1) & (df['is_L5']==0)]
    ax.scatter(l4['lon_grid'], l4['lat_grid'],
               c='#F4D03F', s=0.5, alpha=0.7, label=f'L4 High Persistent (n={len(l4):,})')

    # Layer 3: L5 (Very High — top 5%)
    l5 = df[(df['is_L5']==1) & (df['is_L6']==0)]
    ax.scatter(l5['lon_grid'], l5['lat_grid'],
               c='#E67E22', s=1.5, alpha=0.85, label=f'L5 Very High Persistent (n={len(l5):,})')

    # Layer 4: L6 (Extreme — top 0.5%)
    l6 = df[df['is_L6']==1]
    ax.scatter(l6['lon_grid'], l6['lat_grid'],
               c='#E74C3C', s=4.0, alpha=1.0, label=f'L6 Extreme Persistent (n={len(l6):,})')

    format_map(ax, title=(
        'C6 · Persistent Hotspot Map – Daerah Penangkapan Ikan Paling Konsisten (2012–2025)\n'
        'Klasifikasi L4 (High) hingga L6 (Extreme Persistent Fishing Grounds)'))
    ax.set_facecolor('#0D2137')  # Laut gelap agar warna lebih pop

    leg = ax.legend(loc='lower left', markerscale=12, fontsize=8,
                    facecolor='white', edgecolor='#555', framealpha=0.9)

    out = os.path.join(F7_DIR, 'C6_persistent_hotspot.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# C7: HOTSPOT EMERGENCE MAP
# ============================================================
def vis_C7():
    print("\n[5/6] C7 -- Hotspot Emergence Map...")
    t = time.time()

    df = pd.read_csv(YEARLY)
    df = df[(df['is_partial_year'] == 0) & df['wpp'].isin(WPP_META.keys())]
    mask = load_ocean_mask(n=30_000)

    # Periode awal (2012–2016) vs periode akhir (2020–2025)
    early  = df[df['year'].between(2012,2016)].groupby('wpp')['detection_count'].mean()
    late   = df[df['year'].between(2020,2025)].groupby('wpp')['detection_count'].mean()

    change = ((late - early) / (early + 1)) * 100  # % perubahan
    change = change.reindex(list(WPP_META.keys()), fill_value=0)

    # Buat kategori: Emerging (>+15%), Stable (±15%), Declining (<-15%)
    def cat(v):
        if v > 15:  return 'Emerging (>+15%)'
        if v < -15: return 'Declining (<-15%)'
        return 'Stable (±15%)'

    change_df = change.reset_index()
    change_df.columns = ['wpp','pct_change']
    change_df['category'] = change_df['pct_change'].apply(cat)

    fig, axes = plt.subplots(1, 2, figsize=(17, 7))
    fig.suptitle(
        'C7 · Hotspot Emergence Map – Perubahan Intensitas Penangkapan Ikan\n'
        'Perbandingan Periode Awal (2012–2016) vs Periode Akhir (2020–2025)',
        fontsize=11, fontweight='bold', y=1.01)

    # Panel kiri: Peta perubahan
    ax = axes[0]
    draw_ocean(ax, mask)
    palette = {'Emerging (>+15%)':'#E74C3C', 'Stable (±15%)':'#95A5A6',
               'Declining (<-15%)':'#2980B9'}

    for _, row in change_df.iterrows():
        meta = WPP_META[row['wpp']]
        color = palette[row['category']]
        size  = 200 + abs(row['pct_change']) * 12
        ax.scatter(meta['lon'], meta['lat'], c=color, s=size,
                   edgecolors='black', linewidths=0.8, zorder=5, alpha=0.85)
        ax.text(meta['lon'], meta['lat'] - 0.8, f"{row['pct_change']:+.0f}%",
                ha='center', fontsize=7.5, fontweight='bold',
                color='#1A1A2E', zorder=6)
        ax.text(meta['lon'], meta['lat'] + 0.8, row['wpp'],
                ha='center', fontsize=6.5, color='#555', zorder=6)

    format_map(ax, 'Peta Perubahan Intensitas WPP (%)')
    for cat, color in palette.items():
        ax.scatter([], [], c=color, s=150, label=cat, edgecolors='black', linewidths=0.5)
    ax.legend(loc='lower left', fontsize=8, facecolor='white', framealpha=0.9)

    # Panel kanan: Barplot % perubahan per WPP
    ax2 = axes[1]
    ax2.set_facecolor('#FAFAFA')
    sorted_df = change_df.sort_values('pct_change', ascending=True)
    colors = [palette[c] for c in sorted_df['category']]
    bars = ax2.barh(sorted_df['wpp'], sorted_df['pct_change'], color=colors, alpha=0.85,
                    edgecolor='#555', linewidth=0.5)
    ax2.axvline(0, color='black', linewidth=1.5, linestyle='--')
    ax2.axvline(15,  color='#E74C3C', linewidth=1, linestyle=':', alpha=0.7)
    ax2.axvline(-15, color='#2980B9', linewidth=1, linestyle=':', alpha=0.7)
    ax2.set_xlabel('Perubahan Rata-rata Deteksi (%)', fontsize=9)
    ax2.set_title('Persentase Perubahan per WPP\n(2012–2016 → 2020–2025)', fontsize=9)
    ax2.grid(True, axis='x', alpha=0.3)
    for bar, (_, row) in zip(bars, sorted_df.iterrows()):
        offset = 1 if row['pct_change'] >= 0 else -3
        ax2.text(row['pct_change'] + offset, bar.get_y() + bar.get_height()/2,
                 f"{row['pct_change']:+.0f}%", va='center', fontsize=8)

    plt.tight_layout()
    out = os.path.join(F7_DIR, 'C7_hotspot_emergence.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# F1: ACTIVE FISHING MONTH MAP
# ============================================================
def vis_F1():
    print("\n[6/6] F1 -- Active Fishing Month Map...")
    t = time.time()

    df   = load_monthly_clean()
    mask = load_ocean_mask(n=40_000)

    # Hitung bulan puncak per WPP (rata-rata multi-tahun)
    monthly_mean = df.groupby(['wpp','month'])['detection_count'].mean().reset_index()
    peak_month   = monthly_mean.loc[monthly_mean.groupby('wpp')['detection_count'].idxmax()]
    peak_month   = peak_month.set_index('wpp')

    # Hitung bulan minimum per WPP
    trough_month = monthly_mean.loc[monthly_mean.groupby('wpp')['detection_count'].idxmin()]
    trough_month = trough_month.set_index('wpp')

    # Colormap siklus per bulan (circular colormap)
    cmap_circ = cm.get_cmap('hsv', 12)
    month_colors = {m: cmap_circ(m / 12.0) for m in range(1, 13)}

    fig, axes = plt.subplots(1, 2, figsize=(17, 7))
    fig.suptitle(
        'F1 · Active Fishing Month Map – Kalender Musim Puncak Penangkapan per WPP\n'
        'Bulan dengan Aktivitas Tertinggi (Kiri) dan Terendah (Kanan) Rata-rata 2012–2025',
        fontsize=11, fontweight='bold', y=1.01)

    for panel_idx, (title, data, suffix) in enumerate([
        ('Peak Fishing Month (Aktivitas Tertinggi)', peak_month, 'peak'),
        ('Trough Fishing Month (Aktivitas Terendah)', trough_month, 'trough'),
    ]):
        ax = axes[panel_idx]
        draw_ocean(ax, mask)

        for wpp, meta in WPP_META.items():
            if wpp not in data.index:
                continue
            row   = data.loc[wpp]
            m     = int(row['month'])
            count = row['detection_count']
            color = month_colors[m]
            size  = 150 + (count / monthly_mean['detection_count'].max()) * 3000

            ax.scatter(meta['lon'], meta['lat'], c=[color], s=size,
                       edgecolors='black', linewidths=0.8, zorder=5, alpha=0.88)
            ax.text(meta['lon'], meta['lat'] - 0.8, MONTH_NAMES[m],
                    ha='center', fontsize=8, fontweight='bold',
                    color='#1A1A2E', zorder=6)
            ax.text(meta['lon'], meta['lat'] + 0.9, wpp.replace('WPP',''),
                    ha='center', fontsize=6.5, color='#555', zorder=6)

        format_map(ax, title=title)

        # Legenda bulan (color strip)
        for m in range(1, 13):
            ax.scatter([], [], c=[month_colors[m]], s=80,
                       label=MONTH_NAMES[m], edgecolors='black', linewidths=0.3)
        leg = ax.legend(loc='lower left', ncol=4, fontsize=7,
                        facecolor='white', framealpha=0.9, title='Bulan', title_fontsize=7)

    plt.tight_layout()
    out = os.path.join(F7_DIR, 'F1_active_month_map.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    results = {}
    results['C2'] = vis_C2()
    results['C1'] = vis_C1()
    results['C3'] = vis_C3()
    results['C6'] = vis_C6()
    results['C7'] = vis_C7()
    results['F1'] = vis_F1()

    elapsed = time.time() - t0
    print()
    print("=" * 68)
    print(f"FASE 7 SELESAI -- {elapsed:.0f} detik")
    print("=" * 68)
    for code, path in results.items():
        status = "OK" if path else "SKIP"
        print(f"  [{status}] {code}: {os.path.basename(path) if path else '-'}")
    print(f"\nSemua gambar di: {F7_DIR}")
    print("=" * 68)
