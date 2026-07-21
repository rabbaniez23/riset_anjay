"""
FASE 5: SPASIAL DASAR -- 5 Visualisasi
===============================================
  B3  -- Fishnet Grid Aggregation (Frekuensi Deteksi)
  V1  -- KDE / Density Map (Titik-titik panas utama nasional)
  B8  -- Radiance Density Map (Kecerahan Rata-Rata)
  G6  -- Rasterized VBD (Fokus pada L4/L5 Fishing Grounds)
  B9  -- WPP Pseudo-Choropleth (Batas Wilayah berbasis Data)

Input (dari Fase 0 output/):
  pixel_grid_L2.csv -> L2 (>=22 hari) grid 0.01 derajat

Output: output/fase5/*.png
"""

import matplotlib
matplotlib.use('Agg')

import os, sys, time, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ============================================================
# KONFIGURASI
# ============================================================
BASE      = r"e:\UNIVERSITAS PENDIDIKAN INDONESIA\PENELITIAN\FISHING GROUND PATTERN\riset_viirs"
OUT_DIR   = os.path.join(BASE, "output")
F5_DIR    = os.path.join(OUT_DIR, "fase5")
os.makedirs(F5_DIR, exist_ok=True)

GRID_FILE = os.path.join(OUT_DIR, "pixel_grid_L2.csv")

plt.rcParams.update({
    'font.size': 10, 'font.family': 'DejaVu Sans',
    'axes.titlesize': 12, 'axes.labelsize': 10,
    'figure.dpi': 150, 'savefig.dpi': 200,
    'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
    'axes.facecolor': '#0B1D2A' # Latar belakang gelap (Ocean)
})

t0 = time.time()
print("=" * 68)
print("FASE 5: SPASIAL DASAR -- 5 Visualisasi")
print("=" * 68)

def format_map(ax, title):
    """Memberikan format seragam untuk peta spasial."""
    ax.set_aspect('equal', adjustable='box')
    ax.set_title(title, pad=15, color='black', fontweight='bold')
    ax.set_xlabel('Longitude', color='black')
    ax.set_ylabel('Latitude', color='black')
    # Batas EEZ Indonesia kasaran
    ax.set_xlim(94, 142)
    ax.set_ylim(-12, 7)
    
    # Warna grid & ticks
    ax.grid(True, color='#2C3E50', linestyle=':', alpha=0.5)
    ax.tick_params(colors='black')
    for spine in ax.spines.values():
        spine.set_color('#2C3E50')
        spine.set_linewidth(1)

# ============================================================
# B3: FISHNET GRID AGGREGATION (Frekuensi)
# ============================================================
def vis_B3():
    print("\n[1/5] B3 -- Fishnet Grid Aggregation (Frequency)...")
    t = time.time()
    
    df = pd.read_csv(GRID_FILE, usecols=['lat_grid', 'lon_grid', 'freq_days'])
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Scatter plot dengan ukuran piksel (s=0.5) menyerupai raster
    sc = ax.scatter(df['lon_grid'], df['lat_grid'], c=df['freq_days'], 
                    cmap='viridis', s=0.3, alpha=0.8, vmin=22, vmax=200)
    
    format_map(ax, 'B3 \u00b7 Fishnet Grid Aggregation (VBD Frequency)\nDistribusi Kepadatan Hari Penangkapan Ikan (Ambang L2: >=22 hari)')
    
    cbar = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label('Total Hari Deteksi (2012-2025)', color='black')
    cbar.ax.yaxis.set_tick_params(color='black')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='black')

    out = os.path.join(F5_DIR, 'B3_fishnet_frequency.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# V1: KDE DENSITY MAP (Hotspots Nasional)
# ============================================================
def vis_V1():
    print("\n[2/5] V1 -- KDE Density Map (Nasional Hotspots)...")
    t = time.time()
    
    # Ambil grid yang masuk kategori L4 (High Activity, misal > 100 hari) untuk KDE
    # agar komputasi KDE tidak crash karena terlalu banyak titik
    df = pd.read_csv(GRID_FILE, usecols=['lat_grid', 'lon_grid', 'is_L4'])
    
    # Titik L2 sebagai background map (Ocean/EEZ mask)
    l2_df = df
    # Titik L4 (Hotspots) untuk KDE
    hotspots = df[df['is_L4'] == 1]
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # 1. Base Map (EEZ/WPP extent)
    ax.scatter(l2_df['lon_grid'], l2_df['lat_grid'], color='#173B57', s=0.2, alpha=0.3)
    
    # 2. KDE Hotspots
    # Menggunakan hexbin/hist2d karena lebih stabil dan cepat dibanding gaussian_kde
    hb = ax.hexbin(hotspots['lon_grid'], hotspots['lat_grid'], gridsize=150, 
                   cmap='inferno', bins='log', mincnt=1, alpha=0.9)
    
    format_map(ax, 'V1 \u00b7 Peta Densitas Hotspot Nasional (Kawasan Penangkapan Ikan Utama)\nBerdasarkan Area Kepadatan Tinggi (L4)')
    
    cbar = plt.colorbar(hb, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label('Intensitas Hotspot (Log-Scale Piksel L4)', color='black')

    out = os.path.join(F5_DIR, 'V1_kde_density_map.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# B8: RADIANCE DENSITY MAP
# ============================================================
def vis_B8():
    print("\n[3/5] B8 -- Radiance Density Map...")
    t = time.time()
    
    df = pd.read_csv(GRID_FILE, usecols=['lat_grid', 'lon_grid', 'log_rad_mean'])
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Gunakan colormap magma untuk Radiance (gelap ke terang)
    sc = ax.scatter(df['lon_grid'], df['lat_grid'], c=df['log_rad_mean'], 
                    cmap='magma', s=0.3, alpha=0.8)
    
    format_map(ax, 'B8 \u00b7 Radiance Density Map\nDistribusi Spasial Rata-rata Kecerahan Cahaya Kapal (Log-Transformed)')
    
    cbar = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label('log(1 + Rata-rata Radiance)', color='black')

    out = os.path.join(F5_DIR, 'B8_radiance_density.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# G6: GRID 700m RASTERIZED VBD (Tiers L4-L6)
# ============================================================
def vis_G6():
    print("\n[4/5] G6 -- Grid Rasterized VBD (L4-L6)...")
    t = time.time()
    
    # Fokus memetakan titik L4, L5, L6
    df = pd.read_csv(GRID_FILE, usecols=['lat_grid', 'lon_grid', 'is_L4', 'is_L5', 'is_L6'])
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plot background (L2 mask, dark blue)
    ax.scatter(df['lon_grid'], df['lat_grid'], color='#173B57', s=0.1, alpha=0.2, label='L2/L3 (Moderate)')
    
    # Plot L4 (High)
    l4 = df[(df['is_L4'] == 1) & (df['is_L5'] == 0)]
    ax.scatter(l4['lon_grid'], l4['lat_grid'], color='#F1C40F', s=0.5, alpha=0.8, label='L4 (High)')
    
    # Plot L5 (Very High)
    l5 = df[(df['is_L5'] == 1) & (df['is_L6'] == 0)]
    ax.scatter(l5['lon_grid'], l5['lat_grid'], color='#E67E22', s=1.0, alpha=0.9, label='L5 (Very High)')
    
    # Plot L6 (Extreme)
    l6 = df[df['is_L6'] == 1]
    ax.scatter(l6['lon_grid'], l6['lat_grid'], color='#E74C3C', s=2.0, alpha=1.0, label='L6 (Extreme)')
    
    format_map(ax, 'G6 \u00b7 Rasterized VBD Fishing Grounds (Kategorisasi L4-L6)\nPemetaan Spasial Daerah Penangkapan Ikan Berdasarkan Ambang Intensitas')
    
    # Legend
    leg = ax.legend(loc='lower left', markerscale=10, facecolor='#0B1D2A', edgecolor='white', labelcolor='white')
    for text in leg.get_texts():
        text.set_color("white")
        
    out = os.path.join(F5_DIR, 'G6_rasterized_vbd.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# B9: WPP PSEUDO-CHOROPLETH
# ============================================================
def vis_B9():
    print("\n[5/5] B9 -- WPP Pseudo-Choropleth...")
    t = time.time()
    
    df = pd.read_csv(GRID_FILE, usecols=['lat_grid', 'lon_grid', 'wpp_dominant'])
    # Hapus Unknown jika ada
    df = df[df['wpp_dominant'] != 'Unknown']
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Palette unik untuk WPP (11 WPP NRI utama)
    wpps = sorted(df['wpp_dominant'].unique())
    colors = sns.color_palette("tab20", len(wpps))
    
    for wpp, color in zip(wpps, colors):
        subset = df[df['wpp_dominant'] == wpp]
        # Jika nama WPP terlalu panjang, pendekkan
        label = wpp.replace('WPP-NRI', 'WPP').replace('WPP-RI', 'WPP').strip()
        ax.scatter(subset['lon_grid'], subset['lat_grid'], color=color, s=0.3, alpha=0.9, label=label)
    
    format_map(ax, 'B9 \u00b7 Peta Wilayah Pengelolaan Perikanan (WPP)\nBatas Administratif Diperkirakan dari Area Aktivitas Penangkapan')
    
    leg = ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', markerscale=15, 
                    title='Area WPP', facecolor='white', framealpha=0.9)
    plt.setp(leg.get_title(), fontweight='bold')
        
    out = os.path.join(F5_DIR, 'B9_wpp_choropleth.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    results = {}
    results['B3'] = vis_B3()
    results['V1'] = vis_V1()
    results['B8'] = vis_B8()
    results['G6'] = vis_G6()
    results['B9'] = vis_B9()

    elapsed = time.time() - t0
    print()
    print("=" * 68)
    print(f"FASE 5 SELESAI -- {elapsed:.0f} detik")
    print("=" * 68)
    for code, path in results.items():
        status = "OK" if path else "SKIP"
        print(f"  [{status}] {code}: {os.path.basename(path) if path else '-'}")
    print(f"\nSemua gambar di: {F5_DIR}")
    print("=" * 68)
