"""
FASE 2: STATISTIK DESKRIPTIF -- 5 Visualisasi
===============================================
  V2  -- Pareto Chart WPP (ranking aktivitas)
  D1  -- Radiance Class Histogram (profil armada)
  V7  -- Box/Violin Radiance per WPP
  D4  -- Violin + Strip Chart per WPP
  D6  -- Log-Transformed Distribution (Raw vs Log comparison)

Input (dari Fase 0 output/):
  yearly_aggregated.csv   -> V2
  radiance_sample_log.csv -> D1, V7, D4, D6
  pixel_grid_all.csv      -> V7 tambahan (freq_days per WPP)

Output: output/fase2/*.png
"""

import matplotlib
matplotlib.use('Agg')

import os, sys, time, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings('ignore')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ============================================================
# KONFIGURASI
# ============================================================
BASE      = r"e:\UNIVERSITAS PENDIDIKAN INDONESIA\PENELITIAN\FISHING GROUND PATTERN\riset_viirs"
OUT_DIR   = os.path.join(BASE, "output")
F2_DIR    = os.path.join(OUT_DIR, "fase2")
os.makedirs(F2_DIR, exist_ok=True)

YEARLY    = os.path.join(OUT_DIR, "yearly_aggregated.csv")
RAD_FILE  = os.path.join(OUT_DIR, "radiance_sample_log.csv")
PIXEL_ALL = os.path.join(OUT_DIR, "pixel_grid_all.csv")

# Threshold empiris
THR = {
    'L1':10, 'L2':22, 'L3':37, 'L4':68, 'L5':101, 'L6':146
}

# Kelas radiance empiris (ThresholdEmpiris.md)
RAD_CLASSES = {
    'tradisional': {'label': 'Tradisional (< 10)',   'color': '#27AE60', 'max': 10},
    'menengah':    {'label': 'Menengah (10-100)',     'color': '#F39C12', 'max': 100},
    'industri':    {'label': 'Industri (100-1000)',   'color': '#E74C3C', 'max': 1000},
    'anomali':     {'label': 'Anomali (> 1000)',      'color': '#8E44AD', 'max': 1e9},
}

plt.rcParams.update({
    'font.size': 10, 'font.family': 'DejaVu Sans',
    'axes.titlesize': 11, 'axes.labelsize': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 96, 'savefig.dpi': 120,
    'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
    'grid.alpha': 0.3,
})

def shorten_wpp(name, maxlen=30):
    """Potong nama WPP panjang untuk label axis."""
    return str(name)[:maxlen] + ('...' if len(str(name)) > maxlen else '')

def load_rad(usecols=None, nrows=300_000):
    """
    Baca radiance_sample_log.csv dengan dtype kompak (float32)
    untuk menghemat RAM. 300k baris cukup untuk semua visualisasi Fase 2.
    """
    dtype_map = {
        'year':           'int16',
        'month':          'int8',
        'radiance_raw':   'float32',
        'radiance_log1p': 'float32',
        'wpp':            'object',
        'rad_class':      'category',
    }
    cols = usecols if usecols else list(dtype_map.keys())
    use  = [c for c in cols if c in dtype_map]
    dt   = {c: dtype_map[c] for c in use}
    df   = pd.read_csv(RAD_FILE, usecols=use, nrows=nrows, dtype=dt,
                       low_memory=False)
    return df

t0 = time.time()
print("=" * 68)
print("FASE 2: STATISTIK DESKRIPTIF -- 5 Visualisasi")
print("=" * 68)


# ============================================================
# V2: PARETO CHART WPP
# ============================================================
def vis_V2():
    print("\n[1/5] V2 -- Pareto Chart WPP...")
    t = time.time()

    df = pd.read_csv(YEARLY)
    # Gunakan hanya tahun penuh (bukan 2026 parsial)
    df = df[df['is_partial_year'] == 0]
    df['detection_count'] = pd.to_numeric(df['detection_count'], errors='coerce')

    # Agregasi per WPP (sum semua tahun)
    wpp_total = (df.groupby('wpp')['detection_count']
                 .sum().sort_values(ascending=False).reset_index())
    wpp_total.columns = ['wpp', 'total']
    total_all = wpp_total['total'].sum()
    wpp_total['pct']    = wpp_total['total'] / total_all * 100
    wpp_total['cum_pct'] = wpp_total['pct'].cumsum()
    wpp_total['wpp_short'] = wpp_total['wpp'].apply(lambda x: shorten_wpp(x, 28))

    n = len(wpp_total)
    # Cari berapa WPP mencapai 80%
    n80 = int((wpp_total['cum_pct'] <= 80).sum()) + 1

    # --- Warna gradasi dari biru tua ke biru muda ---
    blues = plt.cm.Blues(np.linspace(0.85, 0.3, n))

    fig, ax1 = plt.subplots(figsize=(14, 7))
    fig.suptitle(
        'V2 \u00b7 Pareto Chart: Ranking Aktivitas Penangkapan Ikan per WPP\n'
        'VBD Indonesia 2012\u20132025 (tahun penuh) \u2014 Total: '
        f'{total_all:,.0f} deteksi kapal',
        fontsize=12, fontweight='bold', y=1.01
    )

    x = np.arange(n)
    bars = ax1.bar(x, wpp_total['total'] / 1e6, color=blues,
                   edgecolor='white', linewidth=0.4, zorder=2)

    # Highlight WPP dalam 80% kumulatif
    for i in range(min(n80, n)):
        bars[i].set_edgecolor('#1A252F')
        bars[i].set_linewidth(1.5)

    ax1.set_xticks(x)
    ax1.set_xticklabels(wpp_total['wpp_short'], rotation=45, ha='right', fontsize=8.5)
    ax1.set_ylabel('Total Deteksi (juta baris)', fontsize=10)
    ax1.set_xlabel('WPP (Wilayah Pengelolaan Perikanan)', fontsize=10)
    ax1.grid(True, axis='y', alpha=0.3, zorder=0)
    ax1.set_ylim(0, wpp_total['total'].max() / 1e6 * 1.18)

    # Anotasi persentase di atas bar teratas
    for i, (_, row) in enumerate(wpp_total.head(6).iterrows()):
        ax1.text(i, row['total'] / 1e6 + wpp_total['total'].max() / 1e6 * 0.01,
                f"{row['pct']:.1f}%", ha='center', va='bottom',
                fontsize=8, fontweight='bold', color='#1A252F')

    # Sumbu kanan: kumulatif %
    ax2 = ax1.twinx()
    ax2.plot(x, wpp_total['cum_pct'], 'o-',
             color='#E74C3C', linewidth=2.5, markersize=6, zorder=5,
             label='Kumulatif %')
    ax2.axhline(y=80, color='#E74C3C', linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.axhline(y=95, color='#F39C12', linestyle=':', linewidth=1.2, alpha=0.7)
    ax2.set_ylim(0, 110)
    ax2.set_ylabel('Persentase Kumulatif (%)', fontsize=10, color='#E74C3C')
    ax2.tick_params(axis='y', labelcolor='#E74C3C')
    ax2.spines['right'].set_visible(True)

    # Anotasi garis 80%
    ax2.text(n - 0.5, 81.5, f'80% (dari {n80} WPP teratas)', fontsize=8.5,
            color='#E74C3C', ha='right', fontweight='bold')
    ax2.text(n - 0.5, 96.5, '95%', fontsize=8, color='#F39C12', ha='right')

    # Shading "vital few" (<= 80%)
    ax1.axvspan(-0.5, n80 - 0.5, alpha=0.06, color='#3498DB', zorder=0)
    ax1.text(n80/2 - 0.5, wpp_total['total'].max() / 1e6 * 1.12,
            f'"Vital Few"\n{n80} WPP = 80% deteksi',
            ha='center', fontsize=8.5, color='#2980B9',
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#EBF5FB', alpha=0.8))

    plt.tight_layout()
    out = os.path.join(F2_DIR, 'V2_pareto_wpp.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# D1: RADIANCE CLASS HISTOGRAM
# ============================================================
def vis_D1():
    print("\n[2/5] D1 -- Radiance Class Histogram...")
    t = time.time()

    df = load_rad(usecols=['year','radiance_raw','radiance_log1p','rad_class'])
    df['radiance_raw'] = pd.to_numeric(df['radiance_raw'], errors='coerce')
    df = df.dropna(subset=['radiance_raw'])
    df = df[df['radiance_raw'] > 0]

    class_order  = ['tradisional', 'menengah', 'industri', 'anomali']
    class_colors = [RAD_CLASSES[c]['color'] for c in class_order]
    class_labels = [RAD_CLASSES[c]['label'] for c in class_order]

    # Statistik per kelas
    class_stats = df.groupby('rad_class').agg(
        n=('radiance_raw', 'count'),
        median=('radiance_raw', 'median'),
        mean=('radiance_raw', 'mean'),
    ).reindex(class_order)
    total_n = len(df)

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle(
        'D1 \u00b7 Profil Armada: Distribusi Radiance per Kelas Kapal\n'
        'Kelas empiris: <10 / 10\u2013100 / 100\u20131000 / >1000 nW/cm\u00b2/sr \u2014 '
        f'Sample: {total_n:,} deteksi Indonesia EEZ-filtered',
        fontsize=11, fontweight='bold', y=1.02
    )

    # Panel (a): Histogram log-scale X (tampilkan distribusi penuh)
    ax = axes[0]
    # Bins logaritmik (0.1 hingga 100.000)
    log_bins = np.logspace(-1, 5, 80)

    for cls, color in zip(class_order, class_colors):
        subset = df[df['rad_class'] == cls]['radiance_raw']
        ax.hist(subset, bins=log_bins, color=color, alpha=0.75,
                label=RAD_CLASSES[cls]['label'], edgecolor='none')

    ax.set_xscale('log')
    ax.set_xlabel('Radiance (nW/cm\u00b2/sr) \u2014 Skala Log', fontsize=10)
    ax.set_ylabel('Jumlah Deteksi', fontsize=10)
    ax.set_title('(a) Distribusi Radiance\nSkala Log (semua kelas)', fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, which='both')

    # Garis vertikal pembatas kelas
    for val, lbl in [(10,''), (100,''), (1000,'')]:
        ax.axvline(x=val, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    # Annotasi median empiris P50
    ax.axvline(x=6.38, color='#8E44AD', linestyle='-', linewidth=1.5)
    ax.text(6.38 * 1.4, ax.get_ylim()[1] * 0.85,
            'Median\n= 6.38', fontsize=7.5, color='#8E44AD', fontweight='bold')

    # Panel (b): Donut chart proporsi kelas
    ax2 = axes[1]
    class_counts = [class_stats.loc[c, 'n'] if c in class_stats.index else 0
                    for c in class_order]
    class_pcts   = [100 * c / total_n for c in class_counts]

    wedges, texts, autotexts = ax2.pie(
        class_counts, labels=None,
        colors=class_colors, autopct='%1.1f%%',
        pctdistance=0.7, startangle=140,
        wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'}
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight('bold')
        at.set_color('white')

    # Lubang donut
    circle = plt.Circle((0, 0), 0.42, color='white')
    ax2.add_patch(circle)
    ax2.text(0, 0, f'{total_n//1000}k\ndeteksi', ha='center', va='center',
            fontsize=9, fontweight='bold', color='#2C3E50')
    ax2.set_title('(b) Proporsi Kelas\nberdasarkan Volume Deteksi', fontsize=10)
    ax2.legend(wedges, class_labels, loc='lower center', fontsize=8,
              bbox_to_anchor=(0.5, -0.12), ncol=2)

    # Panel (c): Bar statistik per kelas (median & mean)
    ax3 = axes[2]
    x_pos   = np.arange(len(class_order))
    medians = [class_stats.loc[c, 'median'] if c in class_stats.index else 0
               for c in class_order]
    means   = [class_stats.loc[c, 'mean'] if c in class_stats.index else 0
               for c in class_order]

    bars_med  = ax3.bar(x_pos - 0.2, medians, width=0.35,
                       color=class_colors, alpha=0.9, label='Median', edgecolor='white')
    bars_mean = ax3.bar(x_pos + 0.2, means, width=0.35,
                       color=class_colors, alpha=0.45, label='Mean', edgecolor='white',
                       hatch='//')
    ax3.set_yscale('log')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(['Tradit.', 'Menen.', 'Indust.', 'Anomali'], fontsize=9)
    ax3.set_ylabel('Radiance (nW/cm\u00b2/sr) \u2014 Log Scale', fontsize=9)
    ax3.set_title('(c) Median vs Mean Radiance\nper Kelas (Log Scale)', fontsize=10)
    ax3.legend(fontsize=9)
    ax3.grid(True, axis='y', alpha=0.3)

    for bar in bars_med:
        h = bar.get_height()
        if h > 0:
            ax3.text(bar.get_x() + bar.get_width()/2, h * 1.3,
                    f'{h:.1f}', ha='center', va='bottom', fontsize=7.5, fontweight='bold')

    plt.tight_layout()
    out = os.path.join(F2_DIR, 'D1_radiance_histogram.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# V7: BOX + VIOLIN RADIANCE per WPP
# ============================================================
def vis_V7():
    print("\n[3/5] V7 -- Box/Violin Radiance per WPP...")
    t = time.time()

    df = pd.read_csv(RAD_FILE, usecols=['wpp','radiance_log1p','rad_class'])
    df['radiance_log1p'] = pd.to_numeric(df['radiance_log1p'], errors='coerce')
    df = df.dropna(subset=['radiance_log1p'])

    # WPP dengan deteksi terbanyak (top 12)
    top_wpp = df['wpp'].value_counts().nlargest(12).index.tolist()
    df_plot = df[df['wpp'].isin(top_wpp)].copy()
    df_plot['wpp_short'] = df_plot['wpp'].apply(lambda x: shorten_wpp(x, 25))

    # Hitung median per WPP untuk sorting
    wpp_median = df_plot.groupby('wpp_short')['radiance_log1p'].median().sort_values()
    wpp_order  = wpp_median.index.tolist()

    # Subsample agar violin tidak OOM
    df_sub = df_plot.groupby('wpp', group_keys=False).apply(
        lambda x: x.sample(min(len(x), 8000), random_state=42)
    )
    df_sub['wpp_short'] = df_sub['wpp'].apply(lambda x: shorten_wpp(x, 25))

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(
        'V7 \u00b7 Distribusi Radiance per WPP: Profil Intensitas Cahaya Kapal\n'
        'Top 12 WPP berdasarkan volume deteksi | Radiance dalam skala log1p(nW/cm\u00b2/sr)',
        fontsize=11, fontweight='bold', y=1.01
    )

    # Panel (a): Violin plot horizontal
    ax = axes[0]
    palette = sns.color_palette('tab10', len(wpp_order))
    sns.violinplot(
        data=df_sub, y='wpp_short', x='radiance_log1p',
        order=wpp_order,
        palette=palette, orient='h', inner=None,
        cut=0, ax=ax, linewidth=0.8
    )
    # Overlay boxplot
    sns.boxplot(
        data=df_sub, y='wpp_short', x='radiance_log1p',
        order=wpp_order,
        color='white', width=0.18,
        linewidth=1, fliersize=2, orient='h', ax=ax,
        boxprops={'zorder': 2}, whiskerprops={'zorder': 2},
        medianprops={'color': '#E74C3C', 'linewidth': 2, 'zorder': 3}
    )
    ax.set_xlabel('log(1 + Radiance) [nW/cm\u00b2/sr]', fontsize=10)
    ax.set_ylabel('')
    ax.set_title('(a) Violin + Box Plot\nDistribusi Radiance per WPP', fontsize=10)
    ax.grid(True, axis='x', alpha=0.3)
    # Garis vertikal: log(1+6.38) = median nasional
    ax.axvline(x=np.log1p(6.38), color='gray', linestyle='--',
               linewidth=1, alpha=0.6)
    ax.text(np.log1p(6.38) + 0.02, len(wpp_order) - 0.5,
            'Median\nnasional', fontsize=7, color='gray')

    # Panel (b): Box plot dengan outlier visible
    ax2 = axes[1]
    sns.boxplot(
        data=df_sub, y='wpp_short', x='radiance_log1p',
        order=wpp_order,
        palette=palette, orient='h', ax=ax2,
        width=0.5, flierprops={'marker': '.', 'markersize': 2, 'alpha': 0.3},
        medianprops={'color': 'white', 'linewidth': 2}
    )
    # Overlay median ticks
    for i, wpp in enumerate(wpp_order):
        med = wpp_median[wpp]
        ax2.plot(med, i, 'D', color='white', markersize=5, zorder=5)
        ax2.text(med + 0.05, i, f'{np.expm1(med):.1f}', va='center',
                fontsize=7, color='#2C3E50')

    ax2.set_xlabel('log(1 + Radiance) [nW/cm\u00b2/sr]', fontsize=10)
    ax2.set_ylabel('')
    ax2.set_title('(b) Box Plot + Median Value\n(Nilai asli dalam nW/cm\u00b2/sr)', fontsize=10)
    ax2.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    out = os.path.join(F2_DIR, 'V7_violin_box_wpp.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# D4: VIOLIN + STRIP CHART per WPP (KELAS ARMADA)
# ============================================================
def vis_D4():
    print("\n[4/5] D4 -- Violin + Strip Chart per WPP...")
    t = time.time()

    df = pd.read_csv(RAD_FILE, usecols=['wpp','radiance_log1p','rad_class'])
    df['radiance_log1p'] = pd.to_numeric(df['radiance_log1p'], errors='coerce')
    df = df.dropna(subset=['radiance_log1p'])

    # Top 8 WPP, subsample kecil agar strip tidak terlalu padat
    top_wpp = df['wpp'].value_counts().nlargest(8).index.tolist()
    df_top  = df[df['wpp'].isin(top_wpp)].copy()
    df_top['wpp_short'] = df_top['wpp'].apply(lambda x: shorten_wpp(x, 22))

    # Subsample: max 3000 per WPP untuk strip, max 10000 untuk violin
    df_strip  = df_top.groupby('wpp', group_keys=False).apply(
        lambda x: x.sample(min(len(x), 2000), random_state=1))
    df_violin = df_top.groupby('wpp', group_keys=False).apply(
        lambda x: x.sample(min(len(x), 8000), random_state=1))
    df_strip['wpp_short']  = df_strip['wpp'].apply(lambda x: shorten_wpp(x, 22))
    df_violin['wpp_short'] = df_violin['wpp'].apply(lambda x: shorten_wpp(x, 22))

    # Urutan WPP berdasarkan total deteksi
    wpp_order = [shorten_wpp(w, 22) for w in top_wpp]
    class_pal = {
        'tradisional': '#27AE60', 'menengah': '#F39C12',
        'industri': '#E74C3C',    'anomali': '#8E44AD'
    }

    fig, axes = plt.subplots(2, 1, figsize=(15, 11))
    fig.suptitle(
        'D4 \u00b7 Distribusi Radiance per WPP + Sebaran Kelas Armada (Violin + Strip)\n'
        'Setiap titik = 1 deteksi | Warna = Kelas Armada | Top 8 WPP',
        fontsize=11, fontweight='bold', y=1.01
    )

    # Panel (a): Violin (no split) + strip warna kelas
    ax = axes[0]
    sns.violinplot(
        data=df_violin, x='wpp_short', y='radiance_log1p',
        order=wpp_order, inner=None, cut=0,
        color='#D6EAF8', linewidth=0.8, ax=ax
    )
    sns.stripplot(
        data=df_strip, x='wpp_short', y='radiance_log1p',
        order=wpp_order,
        hue='rad_class', palette=class_pal,
        size=2.0, alpha=0.45, jitter=True, ax=ax, zorder=3,
        hue_order=['tradisional', 'menengah', 'industri', 'anomali']
    )
    ax.set_xlabel('')
    ax.set_ylabel('log(1 + Radiance)', fontsize=10)
    ax.set_title('(a) Violin (distribusi) + Strip (titik individual berwarna kelas armada)', fontsize=10)
    ax.set_xticklabels(wpp_order, rotation=30, ha='right', fontsize=8.5)
    ax.grid(True, axis='y', alpha=0.3)
    ax.axhline(y=np.log1p(6.38), color='gray', linestyle='--', linewidth=0.9, alpha=0.7)
    ax.text(len(wpp_order) - 0.5, np.log1p(6.38) + 0.05,
            'Median nasional\n(6.38 nW)', fontsize=7, color='gray', ha='right')

    handles = [mpatches.Patch(color=c, label=RAD_CLASSES[k]['label'])
               for k, c in class_pal.items()]
    ax.legend(handles=handles, fontsize=8, title='Kelas Armada', ncol=2, loc='upper right')

    # Panel (b): Stacked bar proporsi kelas per WPP
    ax2 = axes[1]
    class_order_list = ['tradisional', 'menengah', 'industri', 'anomali']

    # Hitung proporsi
    prop_data = {}
    for cls in class_order_list:
        prop_data[cls] = []
        for wpp in top_wpp:
            sub = df_top[df_top['wpp'] == wpp]
            pct = 100 * (sub['rad_class'] == cls).sum() / len(sub) if len(sub) > 0 else 0
            prop_data[cls].append(pct)

    bottom = np.zeros(len(top_wpp))
    for cls in class_order_list:
        vals = np.array(prop_data[cls])
        ax2.bar(wpp_order, vals, bottom=bottom,
               color=class_pal[cls], label=RAD_CLASSES[cls]['label'],
               edgecolor='white', linewidth=0.5)
        # Anotasi jika > 5%
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 8:
                ax2.text(i, b + v/2, f'{v:.0f}%',
                        ha='center', va='center', fontsize=7.5,
                        color='white', fontweight='bold')
        bottom += vals

    ax2.set_ylabel('Proporsi Kelas Armada (%)', fontsize=10)
    ax2.set_xlabel('WPP', fontsize=10)
    ax2.set_title('(b) Komposisi Kelas Armada per WPP (%)', fontsize=10)
    ax2.set_xticklabels(wpp_order, rotation=30, ha='right', fontsize=8.5)
    ax2.legend(fontsize=8, loc='lower right', ncol=2)
    ax2.set_ylim(0, 105)
    ax2.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    out = os.path.join(F2_DIR, 'D4_violin_strip_wpp.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# D6: LOG-TRANSFORMED DISTRIBUTION COMPARISON
# ============================================================
def vis_D6():
    print("\n[5/5] D6 -- Log-Transformed Distribution Comparison...")
    t = time.time()

    df = load_rad(usecols=['year','radiance_raw','radiance_log1p','rad_class'])
    df['radiance_raw']   = pd.to_numeric(df['radiance_raw'],   errors='coerce')
    df['radiance_log1p'] = pd.to_numeric(df['radiance_log1p'], errors='coerce')
    df = df.dropna()
    df = df[df['radiance_raw'] > 0]

    df_sub = df.sample(n=min(len(df), 100_000), random_state=42)

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle(
        'D6 \u00b7 Analisis Transformasi Log: Perbandingan Distribusi Raw vs Log-Transformed\n'
        'Mengapa log-transform wajib untuk data radiance VBD (mean=377 vs median=6.38 nW/cm\u00b2/sr)',
        fontsize=11, fontweight='bold', y=1.01
    )

    # ---- Baris 1: Distribusi Raw ----
    # (1a) Histogram raw (linear scale)
    ax = axes[0, 0]
    ax.hist(df_sub['radiance_raw'].clip(upper=200), bins=100,
            color='#E74C3C', alpha=0.75, edgecolor='none')
    ax.set_xlabel('Radiance Raw (nW/cm\u00b2/sr)', fontsize=9)
    ax.set_ylabel('Frekuensi', fontsize=9)
    ax.set_title('(a) Distribusi RAW \u2014 Linear Scale\n(Terpotong di 200 untuk visibilitas)', fontsize=9.5)
    ax.axvline(x=6.38, color='#2C3E50', linestyle='--', lw=1.5,
               label=f'Median = 6.38')
    ax.axvline(x=df_sub['radiance_raw'].mean(), color='#F39C12', linestyle='-', lw=1.5,
               label=f"Mean = {df_sub['radiance_raw'].mean():.0f}")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.text(0.65, 0.85, 'Skewness\nextrem!',
            transform=ax.transAxes, fontsize=9, color='#E74C3C', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#FADBD8', alpha=0.8))

    # (1b) Histogram raw (log X scale)
    ax = axes[0, 1]
    log_bins = np.logspace(-1, 5, 70)
    ax.hist(df_sub['radiance_raw'], bins=log_bins,
            color='#E74C3C', alpha=0.75, edgecolor='none')
    ax.set_xscale('log')
    ax.set_xlabel('Radiance Raw (nW/cm\u00b2/sr) \u2014 Log X', fontsize=9)
    ax.set_ylabel('Frekuensi', fontsize=9)
    ax.set_title('(b) Distribusi RAW \u2014 Log-X Scale\n(Lebih terlihat tapi masih right-skewed)', fontsize=9.5)
    ax.axvline(x=6.38, color='#2C3E50', linestyle='--', lw=1.5, label='Median')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, which='both')

    # (1c) QQ plot raw vs normal
    ax = axes[0, 2]
    from scipy import stats as scipy_stats
    sample_raw = df_sub['radiance_raw'].clip(upper=500).sample(5000, random_state=1)
    (osm, osr), (slope, intercept, r) = scipy_stats.probplot(
        sample_raw, dist='norm', fit=True)
    ax.plot(osm, osr, '.', color='#E74C3C', markersize=2, alpha=0.5, label='Data')
    x_line = np.linspace(min(osm), max(osm), 100)
    ax.plot(x_line, slope * x_line + intercept, 'k-', linewidth=1.5, label=f'Normal (r={r:.3f})')
    ax.set_xlabel('Kuantil Teoritis (Normal)', fontsize=9)
    ax.set_ylabel('Kuantil Sampel', fontsize=9)
    ax.set_title(f'(c) QQ Plot: Raw vs Normal\nr = {r:.3f} \u2192 TIDAK Normal', fontsize=9.5)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.text(0.05, 0.9, 'Menyimpang\nextrem dari normal',
            transform=ax.transAxes, fontsize=8.5, color='#E74C3C', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#FADBD8', alpha=0.8))

    # ---- Baris 2: Distribusi Log-Transformed ----
    # (2a) Histogram log1p
    ax = axes[1, 0]
    ax.hist(df_sub['radiance_log1p'], bins=80,
            color='#27AE60', alpha=0.75, edgecolor='none')
    ax.set_xlabel('log(1 + Radiance)', fontsize=9)
    ax.set_ylabel('Frekuensi', fontsize=9)
    ax.set_title('(d) Distribusi LOG(1+Radiance)\nJauh lebih simetris \u2714', fontsize=9.5)
    ax.axvline(x=np.log1p(6.38), color='#2C3E50', linestyle='--', lw=1.5,
               label=f'Median log = {np.log1p(6.38):.2f}')
    ax.axvline(x=df_sub['radiance_log1p'].mean(), color='#F39C12', linestyle='-', lw=1.5,
               label=f"Mean log = {df_sub['radiance_log1p'].mean():.2f}")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.text(0.55, 0.85, 'Distribusi lebih\nbisa dianalisis!',
            transform=ax.transAxes, fontsize=9, color='#27AE60', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#D5F5E3', alpha=0.8))

    # (2b) KDE per kelas armada (log transformed)
    ax = axes[1, 1]
    for cls in ['tradisional', 'menengah', 'industri']:
        subset = df_sub[df_sub['rad_class'] == cls]['radiance_log1p']
        if len(subset) < 100:
            continue
        subset.plot.kde(ax=ax, label=RAD_CLASSES[cls]['label'],
                       color=RAD_CLASSES[cls]['color'], linewidth=2)
    ax.set_xlabel('log(1 + Radiance)', fontsize=9)
    ax.set_ylabel('Densitas', fontsize=9)
    ax.set_title('(e) KDE per Kelas Armada\n(Log-transformed)', fontsize=9.5)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)

    # (2c) QQ plot log1p vs normal
    ax = axes[1, 2]
    sample_log = df_sub['radiance_log1p'].sample(5000, random_state=1)
    (osm2, osr2), (slope2, intercept2, r2) = scipy_stats.probplot(
        sample_log, dist='norm', fit=True)
    ax.plot(osm2, osr2, '.', color='#27AE60', markersize=2, alpha=0.5, label='Data')
    x_line2 = np.linspace(min(osm2), max(osm2), 100)
    ax.plot(x_line2, slope2 * x_line2 + intercept2, 'k-', linewidth=1.5,
           label=f'Normal (r={r2:.3f})')
    ax.set_xlabel('Kuantil Teoritis (Normal)', fontsize=9)
    ax.set_ylabel('Kuantil Sampel', fontsize=9)
    ax.set_title(f'(f) QQ Plot: Log1p vs Normal\nr = {r2:.3f} \u2192 Mendekati Normal \u2714', fontsize=9.5)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.text(0.05, 0.85, 'Jauh lebih\nnormal',
            transform=ax.transAxes, fontsize=8.5, color='#27AE60', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#D5F5E3', alpha=0.8))

    plt.tight_layout()
    out = os.path.join(F2_DIR, 'D6_log_transform_comparison.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    results = {}
    results['V2'] = vis_V2()
    results['D1'] = vis_D1()
    results['V7'] = vis_V7()
    results['D4'] = vis_D4()
    results['D6'] = vis_D6()

    elapsed = time.time() - t0
    print()
    print("=" * 68)
    print(f"FASE 2 SELESAI -- {elapsed:.0f} detik")
    print("=" * 68)
    for code, path in results.items():
        status = "OK" if path else "SKIP"
        print(f"  [{status}] {code}: {os.path.basename(path) if path else '-'}")
    print(f"\nSemua gambar di: {F2_DIR}")
    print("=" * 68)
