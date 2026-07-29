"""
visualisasi_v2.py
------------------
Visualisasi VIIRS VBD — Versi 2 (Revisi berdasarkan komentar dosen)

Berisi 5 section utama:
  1. Spasial Lokasi Berdasarkan Density
  2. Perbandingan Kepadatan Antar WPP
  3. Evolusi Tren Jangka Panjang
  4. Pengelompokan Berdasarkan Statistik
  5. Stabilitas Jangka Panjang

Input  : ../output/filtered_data.csv (dari process_viirs_wpp.py)
Output : output/<section>/*.png

Jalankan: python visualisasi_v2.py
"""

import os
import re
import warnings
import io
import zipfile
import requests
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.lines import Line2D
from scipy import stats
from scipy.stats import gaussian_kde
import seaborn as sns

warnings.filterwarnings('ignore')

# ─── Pyshp / Shapely (opsional, untuk peta) ───────────────────────────────────
try:
    import shapefile
    from shapely.geometry import shape
    from shapely.ops import unary_union
    HAS_SHAPE = True
except ImportError:
    HAS_SHAPE = False
    print("INFO: pyshp/shapely tidak terinstall. Visualisasi peta akan dilewati.")

# ─── Path ─────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR   = os.path.join(BASE_DIR, '..')
CLEANED_CSV  = os.path.join(BASE_DIR, 'output', 'cleaned_data', 'viirs_clean_all.csv')
FILTERED_CSV = os.path.join(PARENT_DIR, 'output', 'filtered_data.csv')
SHP_DIR      = os.path.join(PARENT_DIR, 'shp&shx')

OUT_BASE = os.path.join(BASE_DIR, 'output')
OUT_DIRS = {
    '01_spasial':        os.path.join(OUT_BASE, '01_spasial'),
    '02_kepadatan_wpp':  os.path.join(OUT_BASE, '02_kepadatan_wpp'),
    '03_tren':           os.path.join(OUT_BASE, '03_tren'),
    '04_pengelompokan':  os.path.join(OUT_BASE, '04_pengelompokan'),
    '05_stabilitas':     os.path.join(OUT_BASE, '05_stabilitas'),
}
for d in OUT_DIRS.values():
    os.makedirs(d, exist_ok=True)

# ─── Style Global ─────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':    'DejaVu Sans',
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'legend.fontsize': 9,
    'figure.dpi':     150,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
})
SAVE_DPI = 200

# ─── Warna WPP ────────────────────────────────────────────────────────────────
WPP_CODES = ['571', '572', '573', '711', '712', '713', '714', '715', '716', '717', '718']
CMAP_TAB  = plt.get_cmap('tab20')
WPP_COLOR = {c: CMAP_TAB(i / len(WPP_CODES)) for i, c in enumerate(WPP_CODES)}


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: Peta (shapefile)
# ══════════════════════════════════════════════════════════════════════════════
def get_indonesia_basemap():
    extract_dir = os.path.join(PARENT_DIR, 'output', 'ne_countries')
    if not HAS_SHAPE:
        return []
    if not os.path.exists(extract_dir):
        print("Mengunduh basemap Indonesia dari Natural Earth...")
        url = "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip"
        try:
            r = requests.get(url, timeout=60)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                z.extractall(extract_dir)
        except Exception as e:
            print(f"  Gagal unduh basemap: {e}")
            return []
    shp_files = [f for f in os.listdir(extract_dir) if f.endswith('.shp')]
    if not shp_files:
        return []
    shp_path = os.path.join(extract_dir, shp_files[0]).replace('.shp', '')
    sf = shapefile.Reader(shp_path)
    fields = [f[0] for f in sf.fields[1:]]
    polys = []
    for rec, sh in zip(sf.records(), sf.shapes()):
        rec_dict = dict(zip(fields, rec))
        name = rec_dict.get('ADMIN', '') or rec_dict.get('NAME', '') or ''
        if 'Indonesia' in str(name):
            polys.append(shape(sh))
    return polys


def load_wpp_geoms():
    if not HAS_SHAPE or not os.path.exists(SHP_DIR):
        return {}
    wpp_geoms = {}
    for fn in sorted(os.listdir(SHP_DIR)):
        if not fn.endswith('.shp'):
            continue
        m = re.search(r'WPP-RI\s+(\d+)', fn)
        code = m.group(1) if m else fn.replace('.shp', '')
        fp = os.path.join(SHP_DIR, fn)
        try:
            sf = shapefile.Reader(shp=fp)
            shapes_list = [shape(s) for s in sf.shapes() if s.shapeType != 0]
            if shapes_list:
                wpp_geoms[code] = shapes_list[0] if len(shapes_list) == 1 else unary_union(shapes_list)
        except:
            pass
    return wpp_geoms


def draw_land(ax, polys, dark_mode=False):
    """Gambar daratan Indonesia. dark_mode=True untuk background gelap."""
    face = '#3a3a3a' if dark_mode else '#C8D6AF'
    edge = '#555555' if dark_mode else '#888888'
    for geom in polys:
        geom = geom.simplify(0.05, preserve_topology=True)
        ps = [geom] if geom.geom_type == 'Polygon' else list(geom.geoms)
        for poly in ps:
            x, y = poly.exterior.xy
            ax.add_patch(MplPolygon(np.column_stack((x, y)),
                                    facecolor=face, edgecolor=edge,
                                    linewidth=0.4, zorder=4))


def draw_wpp(ax, wpp_geoms, dark_mode=False):
    """Gambar batas WPP. dark_mode=True untuk tema gelap."""
    line_color  = '#88CCEE' if dark_mode else '#333333'
    label_color = '#FFFFFF' if dark_mode else '#111111'
    label_bg    = '#00000060' if dark_mode else '#FFFFFF99'
    for code, geom in wpp_geoms.items():
        geom = geom.simplify(0.05, preserve_topology=True)
        color = WPP_COLOR.get(code, 'gray')
        ps = [geom] if geom.geom_type == 'Polygon' else list(geom.geoms)
        for poly in ps:
            x, y = poly.exterior.xy
            ax.plot(x, y, color=line_color, linewidth=0.7, zorder=6, alpha=0.7)
            if not dark_mode:
                ax.add_patch(MplPolygon(np.column_stack((x, y)),
                                        facecolor=color, alpha=0.12,
                                        edgecolor='none', zorder=2))
        cx, cy = geom.centroid.x, geom.centroid.y
        ax.text(cx, cy, code, fontsize=8, ha='center', va='center',
                color=label_color, fontweight='bold', zorder=7,
                bbox=dict(boxstyle='round,pad=0.2', fc=label_bg,
                          alpha=0.75 if dark_mode else 0.6, ec='none'))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: SPASIAL LOKASI BERDASARKAN DENSITY
# Komentar dosen: "semakin gelap semakin dikit" — bagus
# Perbaikan: label WPP lebih jelas, anotasi wilayah padat (Laut Jawa)
# ══════════════════════════════════════════════════════════════════════════════
def section1_spasial(df, wpp_geoms, indonesia_polys):
    print("\n=== SECTION 1: Spasial Lokasi Berdasarkan Density ===")
    from scipy.ndimage import gaussian_filter

    # ─── 1a: DARK-THEME SMOOTH KDE HEATMAP ───────────────────────────────────
    # Style seperti referensi: background gelap, plasma colormap, contour lines
    fig, ax = plt.subplots(figsize=(20, 10))
    fig.patch.set_facecolor('#0a0a18')      # frame luar gelap
    ax.set_facecolor('#080c18')             # laut = biru-hitam sangat gelap

    df_coords = df[['Lon_DNB', 'Lat_DNB']].dropna()
    lons = df_coords['Lon_DNB'].values
    lats = df_coords['Lat_DNB'].values

    # Grid lebih halus (0.25° resolusi)
    lon_bins = np.arange(90, 145.25, 0.25)
    lat_bins = np.arange(-12, 12.25, 0.25)
    H, xedges, yedges = np.histogram2d(lons, lats, bins=[lon_bins, lat_bins])
    H = H.T  # (lat, lon)

    # Gaussian smoothing untuk efek blur mulus seperti KDE
    H_smooth = gaussian_filter(H.astype(float), sigma=2.5)

    # Buat extent untuk imshow
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

    # ── Render heatmap dengan plasma colormap ──
    # Nilai 0 → transparan (laut hitam tetap terlihat)
    H_plot = np.where(H_smooth > 0.05, H_smooth, np.nan)
    vmax = np.nanpercentile(H_smooth, 99.5)  # robustness dari outlier ekstrem
    vmin_plot = 0.05

    im = ax.imshow(
        H_plot,
        extent=extent,
        origin='lower',
        cmap='plasma',              # ungu → oranye → kuning-hijau di puncak
        norm=mcolors.PowerNorm(gamma=0.45, vmin=vmin_plot, vmax=vmax),
        aspect='auto',
        interpolation='bilinear',   # bilinear interpolation → lebih smooth
        alpha=0.92,
        zorder=5
    )

    # ── Contour lines di atas heatmap ──
    # Hanya di area yang cukup padat
    lon_centers = (xedges[:-1] + xedges[1:]) / 2
    lat_centers = (yedges[:-1] + yedges[1:]) / 2
    LON, LAT = np.meshgrid(lon_centers, lat_centers)

    levels = np.percentile(H_smooth[H_smooth > 0.5],
                           [60, 75, 88, 95, 99]) if H_smooth.max() > 0.5 else None
    if levels is not None and len(np.unique(levels)) > 2:
        ct = ax.contour(LON, LAT, H_smooth,
                        levels=levels,
                        colors=['#00FFFF'],  # cyan contour
                        linewidths=0.55, alpha=0.55, zorder=8)

    # ── Daratan: warna abu-abu gelap ──
    if indonesia_polys:
        draw_land(ax, indonesia_polys, dark_mode=True)

    # ── Batas WPP: garis cyan tipis + label putih ──
    if wpp_geoms:
        draw_wpp(ax, wpp_geoms, dark_mode=True)

    # ── Colorbar ──
    cbar = plt.colorbar(im, ax=ax, shrink=0.55, pad=0.01,
                        fraction=0.025)
    cbar.set_label('Kepadatan Deteksi Kapal (Smoothed)',
                   fontsize=10, color='white')
    cbar.ax.yaxis.set_tick_params(color='white', labelcolor='white')
    cbar.outline.set_edgecolor('white')
    cbar.set_ticks([])
    cbar.ax.text(0.5, -0.02, 'Sedikit', transform=cbar.ax.transAxes,
                 ha='center', va='top', color='white', fontsize=8)
    cbar.ax.text(0.5, 1.02, 'Banyak', transform=cbar.ax.transAxes,
                 ha='center', va='bottom', color='white', fontsize=8)

    # ── Anotasi Laut Jawa ──
    ax.annotate(
        'Laut Jawa (WPP 712)\nTeknologi nelayan lebih maju\n→ densitas deteksi tertinggi',
        xy=(110.5, -5.8), xytext=(99, -1.5),
        fontsize=8.5, color='#FFFF88', fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='#FFFF88', lw=1.4),
        bbox=dict(boxstyle='round,pad=0.5', fc='#000000AA', alpha=0.85,
                  ec='#FFFF88', linewidth=1.2),
        zorder=12
    )

    # ── Sumbu & judul ──
    ax.set_xlim(90, 145)
    ax.set_ylim(-12, 12)
    ax.set_xlabel('Bujur (Longitude)°', fontsize=11, color='#AAAACC')
    ax.set_ylabel('Lintang (Latitude)°', fontsize=11, color='#AAAACC')
    ax.tick_params(colors='#AAAACC')
    for spine in ax.spines.values():
        spine.set_edgecolor('#334466')

    d_min = pd.to_datetime(df['Date'].min()).strftime('%Y-%m-%d') if pd.notnull(df['Date'].min()) else '2012-04-01'
    d_max = pd.to_datetime(df['Date'].max()).strftime('%Y-%m-%d') if pd.notnull(df['Date'].max()) else '2026-05-31'
    ax.set_title(
        'Peta Kepadatan Deteksi Kapal VIIRS di Perairan Indonesia\n'
        f'(n={len(df):,} deteksi  |  Data Cleaned 15 Tahun  |  {d_min} s/d {d_max})',
        fontsize=13, fontweight='bold', color='white', pad=14
    )

    ax.grid(True, linestyle='--', alpha=0.12, color='#445566', zorder=1)

    out = os.path.join(OUT_DIRS['01_spasial'], 's1a_density_heatmap.png')
    plt.tight_layout()
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Tersimpan: {out}")

    # --- 1b: Scatter plot sebaran per WPP ---
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_facecolor('#D6EAF8')
    if indonesia_polys:
        draw_land(ax, indonesia_polys, dark_mode=False)
    if wpp_geoms:
        draw_wpp(ax, wpp_geoms, dark_mode=False)

    df_in  = df[df['WPP_RI'] != 'Outside']
    df_out = df[df['WPP_RI'] == 'Outside']

    if not df_out.empty:
        ax.scatter(df_out['Lon_DNB'], df_out['Lat_DNB'],
                   c='#CCCCCC', s=2, alpha=0.2, label='Luar WPP-RI', zorder=6, rasterized=True)

    for code in WPP_CODES:
        sub = df_in[df_in['WPP_RI'] == code]
        if not sub.empty:
            ax.scatter(sub['Lon_DNB'], sub['Lat_DNB'],
                       c=[WPP_COLOR[code]], s=4, alpha=0.6,
                       label=f'WPP {code} (n={len(sub):,})', zorder=7, rasterized=True)

    ax.set_xlim(90, 145)
    ax.set_ylim(-12, 12)
    ax.set_xlabel('Bujur (Longitude)°', fontsize=11)
    ax.set_ylabel('Lintang (Latitude)°', fontsize=11)
    ax.set_title('Sebaran Titik Deteksi Kapal VIIRS per WPP-RI', fontsize=13, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.3, zorder=1)
    ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=8, framealpha=0.9)

    out = os.path.join(OUT_DIRS['01_spasial'], 's1b_scatter_per_wpp.png')
    plt.tight_layout()
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: PERBANDINGAN KEPADATAN ANTAR WPP
# Komentar dosen:
# - Pareto: definisikan garis merah dengan jelas dalam diagram
# - Jika arti diagram sama, jadikan satu gambar saja
# ══════════════════════════════════════════════════════════════════════════════
def section2_kepadatan_wpp(df):
    print("\n=== SECTION 2: Perbandingan Kepadatan Antar WPP ===")

    wpp_in = df[df['WPP_RI'].isin(WPP_CODES)]
    counts = wpp_in.groupby('WPP_RI').size().reset_index(name='count')
    counts = counts.sort_values('count', ascending=False).reset_index(drop=True)
    counts['pct'] = counts['count'] / counts['count'].sum() * 100
    counts['cum_pct'] = counts['pct'].cumsum()

    # Gabungkan bar chart + pareto dalam SATU gambar (sesuai saran dosen)
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # --- Panel Kiri: Bar Chart ---
    ax1 = axes[0]
    colors = [WPP_COLOR.get(c, 'gray') for c in counts['WPP_RI']]
    bars = ax1.bar(counts['WPP_RI'], counts['count'], color=colors,
                   edgecolor='white', linewidth=0.5)
    ax1.set_xlabel('WPP-RI', fontsize=11)
    ax1.set_ylabel('Jumlah Deteksi Kapal', fontsize=11)
    ax1.set_title('Jumlah Deteksi per WPP-RI', fontsize=13, fontweight='bold')
    ax1.tick_params(axis='x', rotation=0)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    ax1.grid(axis='y', linestyle='--', alpha=0.4)

    for bar, val in zip(bars, counts['count']):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                 f'{val/1000:.1f}K', ha='center', va='bottom', fontsize=8)

    # --- Panel Kanan: Diagram Pareto ---
    ax2 = axes[1]
    ax2_twin = ax2.twinx()

    bars2 = ax2.bar(counts['WPP_RI'], counts['pct'], color=colors,
                    edgecolor='white', linewidth=0.5, alpha=0.85)
    ax2.set_xlabel('WPP-RI', fontsize=11)
    ax2.set_ylabel('Persentase Kontribusi (%)', fontsize=11)
    ax2.set_title('Diagram Pareto Kontribusi WPP-RI', fontsize=13, fontweight='bold')

    # Garis kumulatif — diperjelas sesuai komentar dosen
    line_cum = ax2_twin.plot(
        counts['WPP_RI'], counts['cum_pct'],
        color='#C0392B', linewidth=2.5, marker='D', markersize=7,
        markerfacecolor='white', markeredgecolor='#C0392B', markeredgewidth=2,
        label='Kumulatif (%)',  # ← label legend yang diminta dosen
        zorder=10
    )
    ax2_twin.set_ylim(0, 110)
    ax2_twin.set_ylabel('Persentase Kumulatif (%)', fontsize=11, color='#C0392B')
    ax2_twin.tick_params(axis='y', labelcolor='#C0392B')

    # Garis threshold 80%
    idx_80 = counts[counts['cum_pct'] >= 80].index[0] if (counts['cum_pct'] >= 80).any() else None
    if idx_80 is not None:
        ax2_twin.axhline(80, color='#C0392B', linestyle=':', linewidth=1.2, alpha=0.7)
        ax2_twin.text(len(counts)-0.5, 81, '80%', color='#C0392B', fontsize=9)

    # Legend gabungan yang jelas
    legend_elements = [
        mpatches.Patch(color='#4472C4', alpha=0.85, label='Kontribusi per WPP (%)'),
        Line2D([0], [0], color='#C0392B', linewidth=2.5, marker='D',
               markerfacecolor='white', markeredgecolor='#C0392B',
               label='Kumulatif (%) — Pareto line'),
        Line2D([0], [0], color='#C0392B', linestyle=':', linewidth=1.2,
               label='Threshold 80% (Hukum Pareto)')
    ]
    ax2_twin.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.9)

    ax2.grid(axis='y', linestyle='--', alpha=0.4)
    for bar, pct in zip(bars2, counts['pct']):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 f'{pct:.1f}%', ha='center', va='bottom', fontsize=8)

    fig.suptitle('Analisis Kepadatan Deteksi Kapal Antar WPP-RI (Data VIIRS)',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    out = os.path.join(OUT_DIRS['02_kepadatan_wpp'], 's2_pareto_kepadatan_wpp.png')
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: EVOLUSI TREN JANGKA PANJANG
# Komentar dosen:
# - Gambar 1: garis putus-putus harus ada legend, informasi kurang jelas
# - Gambar 2&3: scale up agar semua WPP terlihat fluktuasi (sharey=False)
# ══════════════════════════════════════════════════════════════════════════════
def section3_tren(df):
    print("\n=== SECTION 3: Evolusi Tren Jangka Panjang ===")

    wpp_in = [c for c in WPP_CODES if c in df['WPP_RI'].values]
    if not wpp_in:
        print("  Tidak ada data WPP, skip.")
        return

    annual = (df[df['WPP_RI'].isin(wpp_in)]
              .groupby(['Year', 'WPP_RI'], observed=True).size().reset_index(name='count'))

    # --- 3a: Tren Tahunan Per WPP (dengan legend yang jelas) ---
    ncols = 3
    nrows = int(np.ceil(len(wpp_in) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 4.5 * nrows),
                             sharey=False)  # ← sharey=False agar semua fluktuasi terlihat
    axes = np.array(axes).flatten()

    # Legend elements — diperjelas sesuai komentar dosen
    legend_elements = [
        Line2D([0], [0], color='#E03B3B', linewidth=1.8, marker='o',
               markersize=6, linestyle='-', label='Jumlah deteksi aktual per tahun'),
        Line2D([0], [0], color='black', linewidth=1.2, linestyle='--',
               label='Garis tren regresi linear (y = ax + b)'),
    ]

    for i, code in enumerate(wpp_in):
        ax = axes[i]
        sub = annual[annual['WPP_RI'] == code].sort_values('Year')
        x, y = sub['Year'].values, sub['count'].values

        ax.plot(x, y, 'o-', color='#E03B3B', linewidth=1.8, markersize=6,
                label='Jumlah deteksi aktual')

        if len(x) >= 2:
            slope, intercept, r, p, se = stats.linregress(x, y)
            x_line = np.array([x.min(), x.max()])
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line, 'k--', linewidth=1.4,
                    label=f'Regresi: y = {slope:.0f}x + {intercept:.0f}')

            trend_dir = '↑ Meningkat' if slope > 0 else '↓ Menurun'
            sig = '(p<0.05 signifikan)' if p < 0.05 else '(p≥0.05)'
            ax.text(0.04, 0.96,
                    f'R² = {r**2:.3f}  |  p = {p:.3f}\n{trend_dir} {sig}',
                    transform=ax.transAxes, fontsize=8, va='top', ha='left',
                    bbox=dict(boxstyle='round,pad=0.3', fc='#FFF9C4', alpha=0.9, ec='#CCC'))

        ax.set_title(f'WPP-RI {code}', fontsize=11, fontweight='bold')
        ax.set_xlabel('Tahun')
        ax.set_ylabel('Jumlah Deteksi')
        ax.grid(True, linestyle='--', alpha=0.35)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))

    # Sembunyikan subplot kosong
    for j in range(len(wpp_in), len(axes)):
        axes[j].set_visible(False)

    # Legend global di bawah gambar (bukan per subplot)
    fig.legend(handles=legend_elements, loc='lower center',
               ncol=2, fontsize=10, framealpha=0.95,
               bbox_to_anchor=(0.5, -0.03))

    fig.suptitle('Evolusi Tren Tahunan Deteksi Kapal per WPP-RI (VIIRS QF_Detect=1)',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    out = os.path.join(OUT_DIRS['03_tren'], 's3a_tren_tahunan_per_wpp.png')
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out}")

    # --- 3b: Tren Bulanan Per WPP (scale up, sharey=False) ---
    monthly = (df[df['WPP_RI'].isin(wpp_in)]
               .groupby(['Year', 'Month', 'WPP_RI'], observed=True).size().reset_index(name='count'))
    years = sorted(monthly['Year'].unique())
    cmap_yr = plt.get_cmap('plasma')
    yr_colors = {yr: cmap_yr(i / max(len(years)-1, 1)) for i, yr in enumerate(years)}

    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 4.5 * nrows),
                             sharey=False)  # ← sharey=False: tiap WPP punya skala sendiri
    axes = np.array(axes).flatten()

    for i, code in enumerate(wpp_in):
        ax = axes[i]
        sub_wpp = monthly[monthly['WPP_RI'] == code]
        for yr in years:
            sub_yr = sub_wpp[sub_wpp['Year'] == yr].sort_values('Month')
            if not sub_yr.empty:
                ax.plot(sub_yr['Month'], sub_yr['count'], 'o-',
                        color=yr_colors[yr], linewidth=1.3, markersize=4, label=str(yr))
        ax.set_title(f'WPP-RI {code}', fontsize=11, fontweight='bold')
        ax.set_xlabel('Bulan')
        ax.set_ylabel('Jumlah Deteksi')
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(['Jan','Feb','Mar','Apr','Mei','Jun',
                            'Jul','Agu','Sep','Okt','Nov','Des'], fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.35)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
        ax.legend(fontsize=7, ncol=2)

    for j in range(len(wpp_in), len(axes)):
        axes[j].set_visible(False)

    # Colorbar untuk tahun
    sm = plt.cm.ScalarMappable(cmap='plasma',
                                norm=plt.Normalize(vmin=min(years), vmax=max(years)))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes[:len(wpp_in)], shrink=0.5, pad=0.01)
    cbar.set_label('Tahun', fontsize=10)

    fig.suptitle('Pola Musiman Bulanan Deteksi Kapal per WPP-RI\n'
                 '(Y-axis independen per WPP agar fluktuasi tiap wilayah terlihat)',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    out = os.path.join(OUT_DIRS['03_tren'], 's3b_pola_bulanan_per_wpp.png')
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out}")

    # --- 3c: Agregat semua WPP (overview) ---
    all_monthly = (df[df['WPP_RI'].isin(wpp_in)]
                   .groupby(['Year', 'Month'], observed=True).size().reset_index(name='count'))
    all_monthly['YearMonth'] = pd.to_datetime(
        all_monthly[['Year', 'Month']].rename(columns={'Year': 'year', 'Month': 'month'}).assign(day=1))

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.fill_between(all_monthly['YearMonth'], all_monthly['count'],
                    alpha=0.3, color='#2980B9')
    ax.plot(all_monthly['YearMonth'], all_monthly['count'],
            color='#1A5276', linewidth=1.5, label='Total deteksi bulanan')

    # Rolling average 3 bulan
    rolling = all_monthly['count'].rolling(window=3, center=True).mean()
    ax.plot(all_monthly['YearMonth'], rolling,
            color='#E74C3C', linewidth=2.5, linestyle='--',
            label='Moving average 3 bulan')

    ax.set_xlabel('Waktu', fontsize=11)
    ax.set_ylabel('Jumlah Deteksi', fontsize=11)
    ax.set_title('Tren Jangka Panjang Total Deteksi Kapal — Semua WPP-RI',
                 fontsize=13, fontweight='bold')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    ax.grid(True, linestyle='--', alpha=0.35)

    # Legend jelas: garis putus = moving average
    ax.legend(fontsize=10, framealpha=0.95)

    out = os.path.join(OUT_DIRS['03_tren'], 's3c_tren_agregat_all_wpp.png')
    plt.tight_layout()
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: PENGELOMPOKAN BERDASARKAN STATISTIK
# Komentar dosen:
# - Jelaskan fungsi grafik
# - Light distribution: mention literaturnya agar tidak plagiat
# ══════════════════════════════════════════════════════════════════════════════
def section4_pengelompokan(df):
    print("\n=== SECTION 4: Pengelompokan Berdasarkan Statistik ===")

    wpp_in = [c for c in WPP_CODES if c in df['WPP_RI'].values]

    # --- 4a: Distribusi Cahaya (Rad_DNB) dengan referensi literatur ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Panel kiri: histogram distribusi cahaya — ALL WPP
    ax = axes[0]
    rad = df['Rad_DNB'].dropna().clip(lower=0)
    log_rad = np.log1p(rad)

    ax.hist(log_rad, bins=80, color='#2E86C1', alpha=0.7,
            edgecolor='white', linewidth=0.4)

    # Annotasi kelas kapal berdasarkan radiance (Elvidge et al., 2015)
    thresholds = [
        (0, np.log1p(3),   '#27AE60', 'Kapal kecil\n(Rad ≤ 3 nW)'),
        (np.log1p(3), np.log1p(30), '#E67E22', 'Kapal sedang\n(3–30 nW)'),
        (np.log1p(30), log_rad.max(), '#C0392B', 'Kapal besar\n(> 30 nW)'),
    ]
    for xmin, xmax, color, label in thresholds:
        ax.axvspan(xmin, xmax, alpha=0.15, color=color, label=label)

    ax.axvline(np.log1p(3), color='#27AE60', linestyle='--', linewidth=1.5)
    ax.axvline(np.log1p(30), color='#C0392B', linestyle='--', linewidth=1.5)

    ax.set_xlabel('log(1 + Rad_DNB) [nW/cm²/sr]', fontsize=11)
    ax.set_ylabel('Frekuensi Deteksi', fontsize=11)
    ax.set_title(
        'Distribusi Intensitas Cahaya Seluruh Kapal\n'
        'Fungsi: Mengklasifikasikan ukuran kapal berdasarkan kecerahan lampu',
        fontsize=11, fontweight='bold'
    )

    # Caption literatur (sesuai permintaan dosen)
    ax.text(0.01, 0.01,
            'Klasifikasi berdasarkan:\nElvidge et al. (2015) "Methods for Global Survey\n'
            'of Natural Gas Flaring from Visible Infrared Imaging\nRadiometer Suite Data"\n'
            '& NOAA VBD Algorithm Theoretical Basis Document (2017)',
            transform=ax.transAxes, fontsize=7,
            va='bottom', ha='left',
            bbox=dict(boxstyle='round,pad=0.4', fc='#F0F0F0', alpha=0.9, ec='gray'))
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.35)

    # Panel kanan: Box plot radiance per WPP
    ax2 = axes[1]
    data_box = [df[df['WPP_RI'] == c]['Rad_DNB'].dropna().clip(0, 200).values
                for c in wpp_in]
    bp = ax2.boxplot(data_box,
                     patch_artist=True, notch=False,
                     medianprops=dict(color='red', linewidth=2))
    ax2.set_xticks(range(1, len(wpp_in) + 1))
    ax2.set_xticklabels([f'WPP\n{c}' for c in wpp_in], fontsize=9)

    for patch, code in zip(bp['boxes'], wpp_in):
        patch.set_facecolor(WPP_COLOR.get(code, 'gray'))
        patch.set_alpha(0.7)

    ax2.set_xlabel('WPP-RI', fontsize=11)
    ax2.set_ylabel('Radiance DNB [nW/cm²/sr]', fontsize=11)
    ax2.set_title(
        'Sebaran Intensitas Cahaya per WPP-RI\n'
        'Fungsi: Membandingkan karakteristik cahaya kapal antar wilayah',
        fontsize=11, fontweight='bold'
    )
    ax2.set_ylim(0, 100)  # Clip outlier ekstrem untuk keterbacaan
    ax2.grid(axis='y', linestyle='--', alpha=0.35)
    ax2.text(0.01, 0.99,
             'Garis merah = median radiance per WPP\nBox = IQR (25–75 persentil)',
             transform=ax2.transAxes, fontsize=8, va='top',
             bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.9))

    fig.suptitle('Analisis Statistik Distribusi Cahaya Kapal VIIRS\n'
                 '(Sumber: NOAA VIIRS Boat Detection / VBD Algorithm)',
                 fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout()
    out = os.path.join(OUT_DIRS['04_pengelompokan'], 's4a_distribusi_cahaya.png')
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out}")

    # --- 4b: Statistik Deskriptif per WPP (tabel visual) ---
    stats_list = []
    for code in wpp_in:
        sub = df[df['WPP_RI'] == code]['Rad_DNB'].dropna()
        if len(sub) < 10:
            continue
        stats_list.append({
            'WPP': f'WPP-RI {code}',
            'n': len(sub),
            'Mean': sub.mean(),
            'Median': sub.median(),
            'Std': sub.std(),
            'Q25': sub.quantile(0.25),
            'Q75': sub.quantile(0.75),
            'Max': sub.max()
        })

    df_stats = pd.DataFrame(stats_list)

    fig, ax = plt.subplots(figsize=(14, len(df_stats)*0.7 + 2))
    ax.axis('off')
    table = ax.table(
        cellText=df_stats.round(2).values,
        colLabels=df_stats.columns,
        cellLoc='center', loc='center',
        colColours=['#2C3E50'] * len(df_stats.columns)
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.8)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(color='white', fontweight='bold')
            cell.set_facecolor('#2C3E50')
        elif row % 2 == 0:
            cell.set_facecolor('#EBF5FB')
        else:
            cell.set_facecolor('white')

    ax.set_title('Tabel Statistik Deskriptif Radiance (Rad_DNB) per WPP-RI\n'
                 '(semua nilai dalam satuan nW/cm²/sr)',
                 fontsize=12, fontweight='bold', pad=20)

    out = os.path.join(OUT_DIRS['04_pengelompokan'], 's4b_tabel_statistik_wpp.png')
    plt.tight_layout()
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: STABILITAS JANGKA PANJANG
# Komentar dosen:
# - Gambar 1: tinjauan bisa ALL atau 2 tahun terakhir
# - Gambar 2: poin CFA dibikin gradasi warna agar koordinat lebih jelas
# ══════════════════════════════════════════════════════════════════════════════
def section5_stabilitas(df):
    print("\n=== SECTION 5: Stabilitas Jangka Panjang ===")

    wpp_in = [c for c in WPP_CODES if c in df['WPP_RI'].values]

    # --- 5a: Koefisien Variasi per WPP — ALL vs 2 tahun terakhir ---
    annual = (df[df['WPP_RI'].isin(wpp_in)]
              .groupby(['Year', 'WPP_RI']).size().reset_index(name='count'))

    all_years  = sorted(annual['Year'].unique())
    last2_years = all_years[-2:] if len(all_years) >= 2 else all_years

    def compute_cv(data_sub, years_subset):
        cv_data = []
        for code in wpp_in:
            sub = data_sub[(data_sub['WPP_RI'] == code) &
                           (data_sub['Year'].isin(years_subset))]
            if len(sub) >= 2:
                cv = sub['count'].std() / sub['count'].mean() * 100
                mean_val = sub['count'].mean()
                cv_data.append({'WPP': code, 'CV': cv, 'Mean': mean_val})
        return pd.DataFrame(cv_data)

    cv_all   = compute_cv(annual, all_years)
    cv_last2 = compute_cv(annual, last2_years)

    # Plot: 2 panel (ALL vs 2 tahun terakhir) dalam satu gambar
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    for ax, cv_df, title, period in zip(
        axes,
        [cv_all, cv_last2],
        ['Semua Tahun', f'{last2_years[0]}–{last2_years[-1]} (2 Tahun Terakhir)'],
        ['all', 'last2']
    ):
        if cv_df.empty:
            ax.text(0.5, 0.5, 'Data tidak cukup', ha='center', va='center')
            continue

        colors = [WPP_COLOR.get(c, 'gray') for c in cv_df['WPP']]
        bars = ax.barh(cv_df['WPP'], cv_df['CV'], color=colors, edgecolor='white')

        # Warna berdasarkan stabilitas (CV rendah = stabil = hijau, CV tinggi = merah)
        for bar, cv_val in zip(bars, cv_df['CV']):
            color = '#27AE60' if cv_val < 25 else ('#E67E22' if cv_val < 50 else '#C0392B')
            bar.set_facecolor(color)

        ax.axvline(25, color='#27AE60', linestyle='--', linewidth=1.2,
                   label='CV < 25%: Stabil')
        ax.axvline(50, color='#E67E22', linestyle='--', linewidth=1.2,
                   label='CV > 50%: Tidak stabil')

        ax.set_xlabel('Koefisien Variasi — CV (%)', fontsize=11)
        ax.set_ylabel('WPP-RI', fontsize=11)
        ax.set_title(f'Stabilitas Deteksi: {title}\n'
                     'CV rendah = pola stabil, CV tinggi = fluktuatif',
                     fontsize=11, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(axis='x', linestyle='--', alpha=0.4)

        for bar, cv_val in zip(bars, cv_df['CV']):
            ax.text(cv_val + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{cv_val:.1f}%', va='center', fontsize=9)

    fig.suptitle('Analisis Stabilitas Jangka Panjang per WPP-RI\n'
                 '(Koefisien Variasi: CV = Std/Mean × 100%)',
                 fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout()
    out = os.path.join(OUT_DIRS['05_stabilitas'], 's5a_stabilitas_cv_wpp.png')
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out}")

    # --- 5b: Core Fishing Area (CFA) dengan gradasi warna ---
    # CFA = grid cell 0.5° dengan kepadatan tinggi + deteksi konsisten lintas tahun
    df['lon_grid'] = (df['Lon_DNB'] // 0.5) * 0.5 + 0.25
    df['lat_grid'] = (df['Lat_DNB'] // 0.5) * 0.5 + 0.25

    # Hitung: count total dan jumlah tahun yang punya deteksi (konsistensi)
    grid_stats = (df[df['WPP_RI'].isin(wpp_in)]
                  .groupby(['lon_grid', 'lat_grid'])
                  .agg(total=('Rad_DNB', 'count'),
                       years_active=('Year', 'nunique'),
                       mean_rad=('Rad_DNB', 'mean'))
                  .reset_index())

    # Filter CFA: minimal 5 tahun aktif dan deteksi tinggi
    min_years = max(3, len(all_years) // 3)
    cfa = grid_stats[grid_stats['years_active'] >= min_years].copy()
    cfa['score'] = cfa['total'] * cfa['years_active']  # skor konsistensi
    cfa = cfa.nlargest(100, 'score')  # Top 100 CFA

    if cfa.empty:
        print("  CFA kosong setelah filter, merendahkan threshold...")
        cfa = grid_stats.nlargest(50, 'total')
        cfa['score'] = cfa['total']

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_facecolor('#D6EAF8')

    indonesia_polys = get_indonesia_basemap()
    wpp_geoms = load_wpp_geoms()
    if indonesia_polys:
        draw_land(ax, indonesia_polys, dark_mode=False)
    if wpp_geoms:
        draw_wpp(ax, wpp_geoms, dark_mode=False)

    # Scatter CFA dengan GRADASI WARNA (sesuai komentar dosen)
    norm = plt.Normalize(vmin=cfa['score'].min(), vmax=cfa['score'].max())
    sc = ax.scatter(cfa['lon_grid'], cfa['lat_grid'],
                    c=cfa['score'], cmap='YlOrRd', norm=norm,
                    s=cfa['score'] / cfa['score'].max() * 200 + 30,
                    alpha=0.85, edgecolors='#333333', linewidths=0.5,
                    zorder=10, label='Core Fishing Area (CFA)')

    # Colorbar untuk koordinat yang jelas
    cbar = plt.colorbar(sc, ax=ax, shrink=0.6, pad=0.01)
    cbar.set_label('Skor Konsistensi CFA\n(total deteksi × tahun aktif)',
                   fontsize=10)

    # Label rank untuk Top 10 CFA
    top10 = cfa.head(10)
    for _, row in top10.iterrows():
        ax.annotate(f"#{int(top10.index.get_loc(_))+1}",
                    xy=(row['lon_grid'], row['lat_grid']),
                    xytext=(3, 3), textcoords='offset points',
                    fontsize=7, fontweight='bold', color='#1A1A1A',
                    zorder=11)

    ax.set_xlim(90, 145)
    ax.set_ylim(-12, 12)
    ax.set_xlabel('Bujur (Longitude)°', fontsize=11)
    ax.set_ylabel('Lintang (Latitude)°', fontsize=11)
    ax.set_title(
        f'Core Fishing Area (CFA) — {len(cfa)} Zona Penangkapan Utama\n'
        f'(Filter: ≥{min_years} tahun aktif | Gradasi warna = konsistensi & intensitas)',
        fontsize=13, fontweight='bold'
    )
    ax.grid(True, linestyle='--', alpha=0.3, zorder=1)

    # Tambah legend ukuran titik
    for size_val, label in [(30, 'Sedang'), (130, 'Tinggi'), (230, 'Sangat Tinggi')]:
        ax.scatter([], [], c='#E74C3C', s=size_val, alpha=0.7,
                   edgecolors='#333333', linewidths=0.5,
                   label=f'Intensitas: {label}')
    ax.legend(loc='upper left', bbox_to_anchor=(1.12, 1), fontsize=9, framealpha=0.9)

    out = os.path.join(OUT_DIRS['05_stabilitas'], 's5b_cfa_gradasi_warna.png')
    plt.tight_layout()
    plt.savefig(out, dpi=SAVE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Tersimpan: {out}")


def load_all_cleaned_data():
    clean_dir = os.path.join(BASE_DIR, 'output', 'cleaned_data')
    if not os.path.exists(clean_dir):
        return None
    year_dirs = sorted([d for d in os.listdir(clean_dir) if os.path.isdir(os.path.join(clean_dir, d)) and d.isdigit()])
    if not year_dirs:
        return None
    
    print(f"Membaca 15 tahun data ({len(year_dirs)} folder)...")
    
    dfs = []
    usecols = ['Lat_DNB', 'Lon_DNB', 'Rad_DNB', 'QF_Detect', 'Year', 'Month', 'Day', 'WPP_RI', 'Date']
    dtypes = {
        'Lat_DNB': 'float32', 
        'Lon_DNB': 'float32', 
        'Rad_DNB': 'float32', 
        'QF_Detect': 'float32', 
        'Year': 'int16', 
        'Month': 'int8', 
        'Day': 'int8',
        'WPP_RI': 'category',
        'Date': 'object'
    }

    for yr in year_dirs:
        csv_path = os.path.join(clean_dir, yr, f'viirs_clean_{yr}.csv')
        if os.path.exists(csv_path):
            df_yr = pd.read_csv(csv_path, usecols=usecols, dtype=dtypes)
            dfs.append(df_yr)

    if not dfs:
        return None

    df = pd.concat(dfs, ignore_index=True)
    df['Date'] = pd.to_datetime(df['Date'])

    return df


def main():
    df = load_all_cleaned_data()

    if df is None:
        target_csv = CLEANED_CSV if os.path.exists(CLEANED_CSV) else FILTERED_CSV
        if not os.path.exists(target_csv):
            print(f"ERROR: File data tidak ditemukan:\n  {target_csv}")
            return

        print(f"Memuat fallback data: {target_csv}")
        dtypes = {
            'Lat_DNB': 'float32',
            'Lon_DNB': 'float32',
            'Rad_DNB': 'float32',
            'QF_Detect': 'float32',
            'Land_Mask': 'float32',
            'Year': 'float32',
            'Month': 'float32',
            'Day': 'float32'
        }
        usecols = ['Lat_DNB', 'Lon_DNB', 'Rad_DNB', 'Date', 'QF_Detect', 'WPP_RI', 'Year', 'Month', 'Day']
        first_row = pd.read_csv(target_csv, nrows=1)
        avail_cols = [c for c in usecols if c in first_row.columns]
        df = pd.read_csv(target_csv, usecols=avail_cols, dtype={k: v for k, v in dtypes.items() if k in avail_cols})

        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        elif 'Date_Mscan' in df.columns:
            df['Date'] = pd.to_datetime(df['Date_Mscan'], errors='coerce')

        if 'Year' not in df.columns or df['Year'].isnull().all():
            df['Year'] = df['Date'].dt.year
            df['Month'] = df['Date'].dt.month

        df = df.dropna(subset=['Year', 'Month'])
        df['Year'] = df['Year'].astype(int)
        df['Month'] = df['Month'].astype(int)

    # Assign WPP_RI jika belum ada di CSV
    if 'WPP_RI' not in df.columns:
        print("Melakukan spatial join WPP-RI via STRtree...")
        import shapely
        from shapely.strtree import STRtree
        wpp_geoms_dict = load_wpp_geoms()
        if wpp_geoms_dict:
            codes_list = list(wpp_geoms_dict.keys())
            geoms_list = list(wpp_geoms_dict.values())
            tree = STRtree(geoms_list)
            pts = shapely.points(df['Lon_DNB'].values, df['Lat_DNB'].values)
            res = tree.query(pts, predicate='intersects')
            wpp_arr = ['Outside'] * len(df)
            for pt_idx, geom_idx in zip(res[0], res[1]):
                wpp_arr[pt_idx] = codes_list[geom_idx]
            df['WPP_RI'] = pd.Categorical(wpp_arr)
        else:
            df['WPP_RI'] = 'Outside'
    else:
        df['WPP_RI'] = df['WPP_RI'].astype('category')

    d_min_str = df['Date'].min().strftime('%Y-%m-%d') if pd.notnull(df['Date'].min()) else str(df['Year'].min())
    d_max_str = df['Date'].max().strftime('%Y-%m-%d') if pd.notnull(df['Date'].max()) else str(df['Year'].max())

    print(f"Total baris    : {len(df):,}")
    print(f"Rentang tanggal: {d_min_str} s/d {d_max_str}")
    print(f"Kolom tersedia : {list(df.columns)}")
    print(f"Distribusi WPP :\n{df['WPP_RI'].value_counts()}")

    # Load geodata
    wpp_geoms = load_wpp_geoms()
    indonesia_polys = get_indonesia_basemap()

    # Jalankan semua section
    section1_spasial(df, wpp_geoms, indonesia_polys)
    section2_kepadatan_wpp(df)
    section3_tren(df)
    section4_pengelompokan(df)
    section5_stabilitas(df)

    print("\n" + "="*60)
    print("[SELESAI] Semua visualisasi tersimpan di:")
    for key, path in OUT_DIRS.items():
        files = [f for f in os.listdir(path) if f.endswith('.png')] if os.path.exists(path) else []
        print(f"  {path}  ({len(files)} gambar)")
    print("="*60)


if __name__ == '__main__':
    main()
