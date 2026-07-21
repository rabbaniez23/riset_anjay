"""
FASE 3: TEMPORAL DASAR -- 5 Visualisasi
===============================================
  V3  -- Annual Trend Line (nasional)
  A3  -- Yearly Multi-Line per WPP
  A1  -- Calendar Heatmap
  V4  -- Monthly Ridge Plot (KDE / Violin)
  A7  -- YoY Growth Rate

Input (dari Fase 0 output/):
  yearly_aggregated.csv   -> V3, A3, A7
  monthly_aggregated.csv  -> A1, V4

Output: output/fase3/*.png
"""

import matplotlib
matplotlib.use('Agg')

import os, sys, time, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats

warnings.filterwarnings('ignore')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ============================================================
# KONFIGURASI
# ============================================================
BASE      = r"e:\UNIVERSITAS PENDIDIKAN INDONESIA\PENELITIAN\FISHING GROUND PATTERN\riset_viirs"
OUT_DIR   = os.path.join(BASE, "output")
F3_DIR    = os.path.join(OUT_DIR, "fase3")
os.makedirs(F3_DIR, exist_ok=True)

YEARLY    = os.path.join(OUT_DIR, "yearly_aggregated.csv")
MONTHLY   = os.path.join(OUT_DIR, "monthly_aggregated.csv")

plt.rcParams.update({
    'font.size': 10, 'font.family': 'DejaVu Sans',
    'axes.titlesize': 11, 'axes.labelsize': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 96, 'savefig.dpi': 120,
    'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
    'grid.alpha': 0.3, 'grid.linestyle': '--'
})

def shorten_wpp(name, maxlen=30):
    return str(name)[:maxlen] + ('...' if len(str(name)) > maxlen else '')

t0 = time.time()
print("=" * 68)
print("FASE 3: TEMPORAL DASAR -- 5 Visualisasi")
print("=" * 68)


# ============================================================
# V3: ANNUAL TREND LINE (NASIONAL)
# ============================================================
def vis_V3():
    print("\n[1/5] V3 -- Annual Trend Line (Nasional)...")
    t = time.time()

    df = pd.read_csv(YEARLY)
    # Filter hanya tahun penuh
    df = df[df['is_partial_year'] == 0]
    
    # Agregasi nasional
    df_nat = df.groupby('year')['detection_count'].sum().reset_index()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle('V3 \u00b7 Tren Aktivitas Penangkapan Ikan Tahunan (Nasional)\n2012\u20132025 (WPP Indonesia)', fontsize=12, fontweight='bold', y=0.98)
    
    years = df_nat['year'].values
    counts = df_nat['detection_count'].values / 1e6  # Juta deteksi
    
    ax.plot(years, counts, marker='o', linestyle='-', linewidth=2.5, markersize=8, color='#2C3E50', label='Total Deteksi')
    
    # Regresi linear trendline
    slope, intercept, r_value, p_value, std_err = stats.linregress(years, counts)
    trend = slope * years + intercept
    ax.plot(years, trend, linestyle='--', color='#E74C3C', linewidth=2, label=f'Trendline (R\u00b2={r_value**2:.2f})')
    
    ax.set_xticks(years)
    ax.set_xlabel('Tahun', fontsize=10)
    ax.set_ylabel('Total Deteksi (Juta Baris)', fontsize=10)
    ax.grid(True, alpha=0.4)
    ax.set_ylim(0, max(counts) * 1.15)
    
    # Anotasi angka pada titik
    for x, y in zip(years, counts):
        ax.text(x, y + (max(counts)*0.03), f'{y:.1f}', ha='center', va='bottom', fontsize=9)
        
    # Anotasi arah tren
    trend_dir = "Meningkat" if slope > 0 else "Menurun"
    ax.text(0.02, 0.95, f'Tren Keseluruhan: {trend_dir}\nLaju: {slope:.2f} juta/tahun\np-value: {p_value:.3f}', 
            transform=ax.transAxes, va='top', fontsize=10, 
            bbox=dict(boxstyle='round', facecolor='#F8F9F9', edgecolor='#BDC3C7', alpha=0.8))

    ax.legend(loc='lower right')
    
    plt.tight_layout()
    out = os.path.join(F3_DIR, 'V3_annual_trend_national.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# A3: YEARLY MULTI-LINE PER WPP
# ============================================================
def vis_A3():
    print("\n[2/5] A3 -- Yearly Multi-Line per WPP...")
    t = time.time()

    df = pd.read_csv(YEARLY)
    df = df[df['is_partial_year'] == 0]
    
    # Ambil Top 6 WPP
    top_wpp = df.groupby('wpp')['detection_count'].sum().nlargest(6).index.tolist()
    
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle('A3 \u00b7 Tren Aktivitas Tahunan per WPP (Top 6)\n2012\u20132025', fontsize=12, fontweight='bold', y=0.98)
    
    colors = sns.color_palette("husl", 6)
    
    for i, wpp in enumerate(top_wpp):
        df_wpp = df[df['wpp'] == wpp].sort_values('year')
        y_vals = df_wpp['detection_count'].values / 1e6
        x_vals = df_wpp['year'].values
        ax.plot(x_vals, y_vals, marker='o', linewidth=2, color=colors[i], label=shorten_wpp(wpp, 25))
        
        # Anotasi di titik terakhir
        if len(x_vals) > 0:
            ax.text(x_vals[-1] + 0.1, y_vals[-1], shorten_wpp(wpp, 10), va='center', fontsize=8, color=colors[i], fontweight='bold')
            
    ax.set_xticks(np.arange(2012, 2026))
    ax.set_xlabel('Tahun', fontsize=10)
    ax.set_ylabel('Total Deteksi (Juta Baris)', fontsize=10)
    ax.grid(True, alpha=0.4)
    ax.legend(title='WPP Dominan', fontsize=9, bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Limit X axis agar label terakhir tidak kepotong
    ax.set_xlim(2011.5, 2026.5)
    
    plt.tight_layout()
    out = os.path.join(F3_DIR, 'A3_yearly_multiline_wpp.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# A1: CALENDAR HEATMAP (Year vs Month)
# ============================================================
def vis_A1():
    print("\n[3/5] A1 -- Calendar Heatmap (Year x Month)...")
    t = time.time()

    df = pd.read_csv(MONTHLY)
    # Buang bulan di luar 1-12 jika ada anomali
    df = df[df['month'].between(1, 12)]
    
    # Agregasi nasional
    df_nat = df.groupby(['year', 'month'])['detection_count'].sum().reset_index()
    
    # Pivot
    pivot = df_nat.pivot(index='year', columns='month', values='detection_count')
    # Normalisasi ke Juta untuk display text
    pivot_m = pivot / 1e6
    
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle('A1 \u00b7 Calendar Heatmap Intensitas Deteksi (Juta Baris)\nNasional: Tahun vs Bulan (2012-2026)', fontsize=12, fontweight='bold', y=1.02)
    
    # Heatmap
    sns.heatmap(pivot_m, cmap='YlOrRd', annot=True, fmt=".2f", linewidths=.5, ax=ax, cbar_kws={'label': 'Juta Deteksi'})
    
    ax.set_xlabel('Bulan', fontsize=10)
    ax.set_ylabel('Tahun', fontsize=10)
    
    months_labels = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Ags','Sep','Okt','Nov','Des']
    ax.set_xticklabels(months_labels, rotation=0)
    
    # Tandai 2026 sebagai parsial
    if 2026 in pivot.index:
        y_idx = pivot.index.get_loc(2026)
        ax.add_patch(mpatches.Rectangle((0, y_idx), 7, 1, fill=False, edgecolor='blue', lw=3, clip_on=False))
        ax.text(7.1, y_idx + 0.5, '2026 Parsial', va='center', color='blue', fontweight='bold', fontsize=9)
        
    plt.tight_layout()
    out = os.path.join(F3_DIR, 'A1_calendar_heatmap.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# V4: MONTHLY RIDGE PLOT (Violin)
# ============================================================
def vis_V4():
    print("\n[4/5] V4 -- Monthly Distribution (Violin/Ridge)...")
    t = time.time()

    df = pd.read_csv(MONTHLY)
    df = df[df['is_partial_year'] == 0]
    df = df[df['month'].between(1, 12)]
    
    # Log transform detection count for better distribution view
    df['log_det'] = np.log1p(df['detection_count'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle('V4 \u00b7 Distribusi Aktivitas Bulanan (Violin Plot)\nSemua WPP (2012\u20132025) \u2014 Memperlihatkan Variasi Musiman', fontsize=12, fontweight='bold', y=0.98)
    
    sns.violinplot(data=df, x='month', y='log_det', ax=ax, color='#3498DB', inner='quartile', linewidth=1.2)
    
    # Overlay swarmplot for actual points (11 WPPs x 14 years = 154 points per month)
    sns.stripplot(data=df, x='month', y='log_det', color='black', alpha=0.3, size=3, ax=ax, jitter=True)
    
    months_labels = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Ags','Sep','Okt','Nov','Des']
    ax.set_xticks(range(12))
    ax.set_xticklabels(months_labels)
    ax.set_xlabel('Bulan', fontsize=10)
    ax.set_ylabel('log(1 + Deteksi per WPP)', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Highlight Muson Barat (Des-Feb) dan Timur (Jun-Ags)
    ax.axvspan(10.5, 11.5, color='gray', alpha=0.1, zorder=0) # Des
    ax.axvspan(-0.5, 1.5, color='gray', alpha=0.1, zorder=0)  # Jan-Feb
    ax.text(0.5, ax.get_ylim()[1]*0.95, 'Muson\nBarat', ha='center', color='#7F8C8D', fontweight='bold', fontsize=9)
    
    ax.axvspan(4.5, 7.5, color='#F39C12', alpha=0.1, zorder=0) # Jun-Ags
    ax.text(6, ax.get_ylim()[1]*0.95, 'Muson\nTimur', ha='center', color='#D68910', fontweight='bold', fontsize=9)

    plt.tight_layout()
    out = os.path.join(F3_DIR, 'V4_monthly_ridge.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# A7: YOY GROWTH RATE
# ============================================================
def vis_A7():
    print("\n[5/5] A7 -- YoY Growth Rate...")
    t = time.time()

    df = pd.read_csv(YEARLY)
    df = df[df['is_partial_year'] == 0]
    
    df_nat = df.groupby('year')['detection_count'].sum().reset_index()
    df_nat = df_nat.sort_values('year')
    
    # Hitung Year-over-Year % change
    df_nat['yoy_pct'] = df_nat['detection_count'].pct_change() * 100
    
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle('A7 \u00b7 Year-over-Year (YoY) Growth Rate Nasional\nPersentase Perubahan Total Deteksi Kapal per Tahun', fontsize=12, fontweight='bold', y=0.98)
    
    # Filter nan (tahun pertama tidak ada YoY)
    plot_df = df_nat.dropna()
    years = plot_df['year'].values
    yoy = plot_df['yoy_pct'].values
    
    colors = ['#27AE60' if val >= 0 else '#E74C3C' for val in yoy]
    bars = ax.bar(years, yoy, color=colors, edgecolor='black', linewidth=0.5)
    
    ax.axhline(0, color='black', linewidth=1)
    ax.set_xticks(years)
    ax.set_xlabel('Tahun', fontsize=10)
    ax.set_ylabel('YoY Growth (%)', fontsize=10)
    ax.grid(True, axis='y', alpha=0.3)
    
    # Anotasi nilai pada bar
    for bar, val in zip(bars, yoy):
        y_pos = bar.get_height() + (1 if val >= 0 else -3)
        va = 'bottom' if val >= 0 else 'top'
        ax.text(bar.get_x() + bar.get_width()/2, y_pos, f'{val:+.1f}%', ha='center', va=va, fontsize=9, fontweight='bold', color=bar.get_facecolor())

    # Rata-rata growth
    avg_growth = np.mean(yoy)
    ax.axhline(avg_growth, color='blue', linestyle='--', linewidth=1.5, alpha=0.6)
    ax.text(years[-1], avg_growth + 1, f'Rata-rata YoY: {avg_growth:+.1f}%', color='blue', ha='right', fontsize=9, fontweight='bold')

    plt.tight_layout()
    out = os.path.join(F3_DIR, 'A7_yoy_growth.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    results = {}
    results['V3'] = vis_V3()
    results['A3'] = vis_A3()
    results['A1'] = vis_A1()
    results['V4'] = vis_V4()
    results['A7'] = vis_A7()

    elapsed = time.time() - t0
    print()
    print("=" * 68)
    print(f"FASE 3 SELESAI -- {elapsed:.0f} detik")
    print("=" * 68)
    for code, path in results.items():
        status = "OK" if path else "SKIP"
        print(f"  [{status}] {code}: {os.path.basename(path) if path else '-'}")
    print(f"\nSemua gambar di: {F3_DIR}")
    print("=" * 68)
