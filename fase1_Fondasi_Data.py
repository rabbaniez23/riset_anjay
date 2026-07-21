"""
FASE 1: FONDASI DATA -- 5 Visualisasi Statistik Diagnostik
===========================================================
  D2  -- ECDF Frekuensi Piksel + anotasi threshold L1-L6
  I1  -- Data Coverage Temporal Heatmap (Tahun x Bulan)
  I2  -- Cloud Cover Bias Analysis (Pola Bulanan + Musim Muson)
  H5  -- Quality Flag Analysis (Distribusi + Tren Temporal)
  H1  -- Correlation Matrix (Atribut Numerik VBD)

Input (dari Fase 0 output/):
  pixel_grid_all.csv, monthly_aggregated.csv
  + sampling raw CSVs untuk H5 dan H1

Output: output/fase1/*.png
"""

import matplotlib
matplotlib.use('Agg')

import os, sys, csv, glob, time, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings('ignore')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ============================================================
# KONFIGURASI PATH
# ============================================================
BASE       = r"e:\UNIVERSITAS PENDIDIKAN INDONESIA\PENELITIAN\FISHING GROUND PATTERN\riset_viirs"
VIIRS_DIR  = os.path.join(BASE, "viirs")
OUT_DIR    = os.path.join(BASE, "output")
F1_DIR     = os.path.join(OUT_DIR, "fase1")
os.makedirs(F1_DIR, exist_ok=True)

PIXEL_ALL  = os.path.join(OUT_DIR, "pixel_grid_all.csv")
MONTHLY    = os.path.join(OUT_DIR, "monthly_aggregated.csv")
YEARLY     = os.path.join(OUT_DIR, "yearly_aggregated.csv")
RAD_FILE   = os.path.join(OUT_DIR, "radiance_sample_log.csv")

EEZ_VALID  = "Indonesian Exclusive Economic Zone"
YEARS_FULL = list(range(2012, 2026))
ALL_YEARS  = list(range(2012, 2027))

# ============================================================
# THRESHOLD EMPIRIS (ThresholdEmpiris.md)
# ============================================================
THR = {
    'L1': {'val': 10,  'pct': 'P80',   'label': 'L1 Eksplorasi',   'color': '#5DADE2'},
    'L2': {'val': 22,  'pct': 'P90',   'label': 'L2 Aktif (DEF)',  'color': '#27AE60'},
    'L3': {'val': 37,  'pct': 'P95',   'label': 'L3 Significant',  'color': '#F39C12'},
    'L4': {'val': 68,  'pct': 'P98',   'label': 'L4 Hotspot',      'color': '#E74C3C'},
    'L5': {'val': 101, 'pct': 'P99',   'label': 'L5 Core/Paper',   'color': '#8E44AD'},
    'L6': {'val': 146, 'pct': 'P99.5', 'label': 'L6 Apex',         'color': '#1A252F'},
}

MONTH_ID = ['Jan','Feb','Mar','Apr','Mei','Jun',
            'Jul','Ags','Sep','Okt','Nov','Des']

# Musim muson Indonesia
MONSOON_COLORS = {
    'Muson Barat (Des-Feb)': ('#AED6F1', [12,1,2]),
    'Peralihan I (Mar-Mei)': ('#A9DFBF', [3,4,5]),
    'Muson Timur (Jun-Ags)': ('#FAD7A0', [6,7,8]),
    'Peralihan II (Sep-Nov)': ('#D7BDE2', [9,10,11]),
}

plt.rcParams.update({
    'font.size': 10, 'font.family': 'DejaVu Sans',
    'axes.titlesize': 11, 'axes.labelsize': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 96, 'savefig.dpi': 120,
    'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
    'grid.alpha': 0.35, 'grid.linestyle': '--',
})

t0 = time.time()
print("=" * 68)
print("FASE 1: FONDASI DATA -- 5 Visualisasi Statistik")
print("=" * 68)

# ============================================================
# HELPER: Sampling raw CSV untuk H5 & H1
# ============================================================
def sample_raw(needed_cols, rows_per_year=8000, files_per_year=15):
    """
    Sampling stratifikasi dari raw CSV: ambil rows_per_year baris per tahun
    dari files_per_year file (setiap tahun diambil file terdistribusi merata).
    Filter: EEZ Indonesia + bukan daratan.
    """
    all_cols = needed_cols + ['EEZ', 'Land_Mask']
    frames = []
    print(f"    Sampling raw CSV ({rows_per_year} baris/tahun)...")

    for year in ALL_YEARS:
        ydir = os.path.join(VIIRS_DIR, str(year))
        if not os.path.isdir(ydir):
            continue
        files = sorted(glob.glob(os.path.join(ydir, "*.csv")))
        # Ambil file terdistribusi merata sepanjang tahun
        step = max(1, len(files) // files_per_year)
        sel_files = files[::step][:files_per_year]

        year_frames = []
        for fp in sel_files:
            try:
                df = pd.read_csv(fp, usecols=lambda c: c in all_cols,
                                 nrows=1200, low_memory=False, on_bad_lines='skip')
                # Filter EEZ + daratan
                if 'EEZ' in df.columns:
                    df = df[df['EEZ'] == EEZ_VALID]
                if 'Land_Mask' in df.columns:
                    df = df[df['Land_Mask'] != 1]
                df = df.drop(columns=[c for c in ['EEZ','Land_Mask'] if c in df.columns])
                df['year'] = year
                year_frames.append(df)
            except Exception:
                continue

        if year_frames:
            yr_df = pd.concat(year_frames, ignore_index=True)
            frames.append(yr_df.head(rows_per_year))

    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    print(f"    Total sampel: {len(result):,} baris")
    return result


# ============================================================
# VIS D2: ECDF Frekuensi Piksel
# ============================================================
def vis_D2():
    print("\n[1/5] D2 -- ECDF Frekuensi Piksel...")
    t = time.time()

    df = pd.read_csv(PIXEL_ALL, usecols=['freq_days', 'wpp_dominant'])
    freq_all = np.sort(df['freq_days'].values)
    n_all    = len(freq_all)

    # Subsample untuk plotting (ECDF shape tetap akurat)
    # Ambil 50k titik terdistribusi merata
    PLOT_N = 50_000
    idx    = np.linspace(0, n_all - 1, PLOT_N, dtype=int)
    freq   = freq_all[idx]
    prob   = idx / (n_all - 1)   # posisi probabilitas asli

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        'D2 \u00b7 ECDF: Distribusi Kumulatif Frekuensi Kunjungan Kapal per Piksel\n'
        'VBD Indonesia 2012\u20132026 \u2014 EEZ-filtered \u2014 Grid 0.01\u00b0 (~1.1 km) \u2014 n = 1.270.431 piksel',
        fontsize=12, fontweight='bold', y=1.01
    )

    for ax_idx, (ax, log_x, xlim, title) in enumerate(zip(
        axes,
        [False, True],
        [(0, 250), (0.8, 20000)],
        ['(a) Skala Linear \u2014 Detail distribusi ekor kiri (0\u2013250 hari)',
         '(b) Skala Log \u2014 Tampilan penuh (1 s/d 13.279 hari)']
    )):
        if log_x:
            ax.semilogx(freq, prob, color='#2C3E50', linewidth=1.8, zorder=3)
        else:
            ax.plot(freq, prob, color='#2C3E50', linewidth=1.8, zorder=3)
        # Horizontal garis P50, P90
        for py, lbl in [(0.5, 'P50 (Median=2 hr)'), (0.9, 'P90')]:
            ax.axhline(y=py, color='gray', linestyle=':', linewidth=0.9)

        # Garis threshold vertikal
        for name, info in THR.items():
            v = info['val']
            pct_above = 100 * np.mean(freq_all >= v)
            px = np.searchsorted(freq_all, v) / n_all   # posisi y asli

            ax.axvline(x=v, color=info['color'], linestyle='--',
                       linewidth=1.6, alpha=0.9, zorder=4)

            # Annotasi di panel (a) saja agar tidak crowded
            if not log_x:
                if v <= 150:
                    ax.annotate(
                        f"{name}\n\u2265{v}hr\n{pct_above:.1f}%\u2b06",
                        xy=(v, px), xytext=(v + 8, px - 0.10),
                        fontsize=7.5, color=info['color'], fontweight='bold',
                        arrowprops=dict(arrowstyle='->', color=info['color'], lw=0.8)
                    )
            else:
                # Log panel: legend box saja
                pass

        ax.set_title(title, fontsize=10.5)
        ax.set_ylabel('Probabilitas Kumulatif', fontsize=10)
        ax.set_xlabel('Frekuensi Kunjungan Kapal (hari)', fontsize=10)
        ax.set_ylim(0, 1.05)
        if not log_x:
            ax.set_xlim(xlim)
        ax.grid(True)

    # Legend panel (b)
    patches = [mpatches.Patch(color=v['color'],
               label=f"{k} \u2265{v['val']}hr ({v['pct']}): {100*np.mean(freq_all>=v['val']):.1f}% piksel")
               for k, v in THR.items()]
    axes[1].legend(handles=patches, fontsize=8, loc='upper left',
                   title='Threshold Level (% piksel yang lolos)', title_fontsize=8)

    # Tabel bracket di bawah plot kiri
    brackets = [
        ('1\u20134 hr (noise)',     np.sum((freq_all>=1)  & (freq_all<=4))),
        ('5\u20139 hr',             np.sum((freq_all>=5)  & (freq_all<=9))),
        ('10\u201319 hr (L1+)',     np.sum((freq_all>=10) & (freq_all<=19))),
        ('20\u201349 hr (L2+)',     np.sum((freq_all>=20) & (freq_all<=49))),
        ('50\u201399 hr',           np.sum((freq_all>=50) & (freq_all<=99))),
        ('100\u2013199 hr (L5+)',   np.sum((freq_all>=100)& (freq_all<=199))),
        ('\u2265200 hr',            np.sum(freq_all>=200)),
    ]
    tbl_y = 0.0
    for lbl, cnt in brackets:
        axes[0].text(252, tbl_y, f'{lbl}: {cnt:,} ({100*cnt/n_all:.1f}%)',
                    fontsize=7, va='bottom', ha='left', transform=axes[0].transData,
                    clip_on=False)
        tbl_y += 0.13

    plt.tight_layout()
    out = os.path.join(F1_DIR, 'D2_ecdf_threshold.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# VIS I1: Data Coverage Temporal Heatmap
# ============================================================
def vis_I1():
    print("\n[2/5] I1 -- Data Coverage Heatmap...")
    t = time.time()

    df = pd.read_csv(MONTHLY)
    df['year']  = df['year'].astype(int)
    df['month'] = df['month'].astype(int)
    df = df[df['month'].between(1, 12)]

    # Pivot: year x month, jumlah deteksi (sum semua WPP)
    pivot_count = (df.groupby(['year','month'])['detection_count']
                   .sum().unstack(fill_value=0))
    # Pastikan semua bulan ada
    for m in range(1, 13):
        if m not in pivot_count.columns:
            pivot_count[m] = 0
    pivot_count = pivot_count[list(range(1,13))].sort_index()

    # Log-transform untuk visual (count sangat beragam)
    pivot_log = np.log1p(pivot_count)

    # Hitung coverage (1 = ada data, 0 = tidak ada)
    pivot_cov  = (pivot_count > 0).astype(int)
    cov_pct    = pivot_cov.values.sum() / pivot_cov.size * 100

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(
        'I1 \u00b7 Data Coverage: Kelengkapan Temporal Dataset VBD Indonesia 2012\u20132026\n'
        f'Coverage keseluruhan: {cov_pct:.1f}% sel tahun\u00d7bulan memiliki data deteksi',
        fontsize=12, fontweight='bold', y=1.01
    )

    # Panel (a): Heatmap intensitas deteksi (log scale)
    ax1 = axes[0]
    hm1 = sns.heatmap(
        pivot_log,
        ax=ax1, cmap='YlOrRd',
        linewidths=0.4, linecolor='#EEEEEE',
        xticklabels=MONTH_ID,
        cbar_kws={'label': 'log(1 + Deteksi)', 'shrink': 0.8}
    )
    ax1.set_title('(a) Intensitas Deteksi per Bulan\u00d7Tahun (log-scale)', fontsize=11)
    ax1.set_xlabel('Bulan', fontsize=10)
    ax1.set_ylabel('Tahun', fontsize=10)
    # Tandai 2026 sebagai parsial
    if 2026 in pivot_log.index:
        row_idx = list(pivot_log.index).index(2026)
        ax1.add_patch(plt.Rectangle((0, row_idx), 12, 1,
                                    fill=False, edgecolor='blue',
                                    linewidth=2, clip_on=False))
        ax1.text(12.1, row_idx + 0.5, 'Parsial\n(Jan-Jul)', fontsize=8,
                color='blue', va='center')

    # Panel (b): Heatmap coverage biner (ada/tidak ada data)
    ax2 = axes[1]
    sns.heatmap(
        pivot_cov,
        ax=ax2, cmap=['#F0F0F0', '#2ECC71'],
        linewidths=0.4, linecolor='#EEEEEE',
        xticklabels=MONTH_ID,
        cbar_kws={'label': '0=Tidak Ada Data | 1=Ada Data', 'shrink': 0.8},
        vmin=0, vmax=1
    )
    ax2.set_title('(b) Coverage Biner \u2014 Sel Hijau = Ada Data Deteksi', fontsize=11)
    ax2.set_xlabel('Bulan', fontsize=10)
    ax2.set_ylabel('Tahun', fontsize=10)

    # Anotasi jumlah bulan lengkap per tahun
    months_per_year = pivot_cov.sum(axis=1)
    for yr_idx, yr in enumerate(pivot_cov.index):
        ax2.text(12.2, yr_idx + 0.5, f'{months_per_year[yr]}/12',
                fontsize=7.5, va='center', color='#2C3E50')

    plt.tight_layout()
    out = os.path.join(F1_DIR, 'I1_data_coverage.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# VIS I2: Cloud Cover Bias Analysis
# ============================================================
def vis_I2():
    print("\n[3/5] I2 -- Cloud Cover Bias Analysis...")
    t = time.time()

    df = pd.read_csv(MONTHLY)
    df['year']  = df['year'].astype(int)
    df['month'] = df['month'].astype(int)

    # Gunakan hanya tahun penuh (bukan 2026 parsial)
    df_full = df[(df['is_partial_year'] == 0) & df['month'].between(1, 12)]

    # Agregasi per bulan (sum semua WPP, rata-rata antar tahun)
    monthly_sum = df_full.groupby(['year','month'])['detection_count'].sum().reset_index()
    monthly_stat = monthly_sum.groupby('month')['detection_count'].agg(
        mean='mean', std='std', median='median',
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75)
    ).reset_index()

    # Per WPP per bulan (untuk panel bawah)
    wpp_monthly = df_full.groupby(['month','wpp'])['detection_count'].mean().reset_index()
    top_wpp = (df_full.groupby('wpp')['detection_count'].sum()
               .nlargest(6).index.tolist())

    fig, axes = plt.subplots(2, 1, figsize=(13, 10))
    fig.suptitle(
        'I2 \u00b7 Cloud Cover Bias Analysis: Pola Deteksi Bulanan vs Musim Muson\n'
        'Sumber: monthly_aggregated.csv | Tahun penuh 2012\u20132025 (n=14 tahun)',
        fontsize=12, fontweight='bold', y=1.01
    )

    # Panel (a): Pola bulanan nasional
    ax = axes[0]
    months = monthly_stat['month'].values
    mean_  = monthly_stat['mean'].values / 1000  # ribuan
    std_   = monthly_stat['std'].values / 1000
    q25_   = monthly_stat['q25'].values / 1000
    q75_   = monthly_stat['q75'].values / 1000
    med_   = monthly_stat['median'].values / 1000

    # Shading musim muson
    monsoon_patches = []
    for season, (col, mons) in MONSOON_COLORS.items():
        for m in mons:
            if 1 <= m <= 12:
                ax.axvspan(m-0.5, m+0.5, alpha=0.25, color=col, zorder=0)
        monsoon_patches.append(mpatches.Patch(color=col, alpha=0.5, label=season))

    # IQR band
    ax.fill_between(months, q25_, q75_, alpha=0.25, color='#3498DB', label='IQR (Q25\u2013Q75)')
    # Mean + 1std band
    ax.fill_between(months, mean_-std_, mean_+std_, alpha=0.12, color='#E74C3C')
    # Mean line
    ax.plot(months, mean_, 'o-', color='#2C3E50', linewidth=2.5,
            markersize=8, label='Rata-rata tahunan', zorder=5)
    # Median
    ax.plot(months, med_, 's--', color='#E74C3C', linewidth=1.5,
            markersize=6, label='Median tahunan', zorder=4)

    ax.set_xticks(range(1,13))
    ax.set_xticklabels(MONTH_ID, fontsize=10)
    ax.set_xlabel('')
    ax.set_ylabel('Total Deteksi (ribuan baris)', fontsize=10)
    ax.set_title('(a) Pola Deteksi Bulanan Nasional (2012\u20132025) + Musim Muson', fontsize=11)
    ax.grid(True, axis='y')
    ax.set_xlim(0.5, 12.5)

    # Annotasi bulan tertinggi/terendah
    hi_m = months[np.argmax(mean_)]
    lo_m = months[np.argmin(mean_)]
    ax.annotate(f'Puncak: {MONTH_ID[hi_m-1]}\n{mean_[np.argmax(mean_)]:.0f}k',
                xy=(hi_m, mean_[np.argmax(mean_)]),
                xytext=(hi_m+0.5, mean_[np.argmax(mean_)] + std_[np.argmax(mean_)]*0.3),
                fontsize=8.5, color='#27AE60', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#27AE60'))
    ax.annotate(f'Minimum: {MONTH_ID[lo_m-1]}\n{mean_[np.argmin(mean_)]:.0f}k',
                xy=(lo_m, mean_[np.argmin(mean_)]),
                xytext=(lo_m+0.5, mean_[np.argmin(mean_)] - std_[np.argmin(mean_)]*0.2),
                fontsize=8.5, color='#E74C3C', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#E74C3C'))

    legend1 = ax.legend(handles=[
        plt.Line2D([0],[0], color='#2C3E50', lw=2.5, marker='o', ms=8, label='Mean'),
        plt.Line2D([0],[0], color='#E74C3C', lw=1.5, ls='--', marker='s', ms=6, label='Median'),
        mpatches.Patch(color='#3498DB', alpha=0.4, label='IQR Q25-Q75'),
    ] + monsoon_patches, fontsize=8, ncol=2, loc='lower right')
    ax.add_artist(legend1)

    # Panel (b): Per WPP top-6 pola bulanan
    ax2 = axes[1]
    colors_wpp = ['#E74C3C','#3498DB','#27AE60','#F39C12','#8E44AD','#1ABC9C']
    for i, wpp in enumerate(top_wpp):
        wpp_data = wpp_monthly[wpp_monthly['wpp'] == wpp].sort_values('month')
        if wpp_data.empty:
            continue
        vals = wpp_data.set_index('month')['detection_count'].reindex(range(1,13), fill_value=0) / 1000
        ax2.plot(range(1,13), vals.values, 'o-',
                color=colors_wpp[i % len(colors_wpp)], linewidth=2,
                markersize=6, label=wpp)

    # Shading musim
    for season, (col, mons) in MONSOON_COLORS.items():
        for m in mons:
            if 1 <= m <= 12:
                ax2.axvspan(m-0.5, m+0.5, alpha=0.2, color=col, zorder=0)

    ax2.set_xticks(range(1,13))
    ax2.set_xticklabels(MONTH_ID, fontsize=10)
    ax2.set_xlabel('Bulan', fontsize=10)
    ax2.set_ylabel('Rata-rata Deteksi per Bulan (ribuan)', fontsize=10)
    ax2.set_title('(b) Pola Bulanan per WPP (Top 6 berdasarkan volume deteksi)', fontsize=11)
    ax2.legend(fontsize=9, loc='upper right', title='WPP')
    ax2.grid(True, axis='y')
    ax2.set_xlim(0.5, 12.5)

    plt.tight_layout()
    out = os.path.join(F1_DIR, 'I2_cloud_cover_bias.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# VIS H5: Quality Flag Analysis
# ============================================================
def vis_H5():
    print("\n[4/5] H5 -- Quality Flag Analysis...")
    t = time.time()

    df = sample_raw(
        needed_cols=['QF_Detect', 'FMZ'],
        rows_per_year=9000, files_per_year=15
    )
    if df.empty or 'QF_Detect' not in df.columns:
        print("  [SKIP] Kolom QF_Detect tidak ditemukan")
        return None

    df['QF_Detect'] = pd.to_numeric(df['QF_Detect'], errors='coerce')
    df = df.dropna(subset=['QF_Detect'])
    df['QF_Detect'] = df['QF_Detect'].astype(int)
    df['year'] = df['year'].astype(int)

    print(f"  Sampel bersih: {len(df):,} baris | QF unik: {sorted(df['QF_Detect'].unique())}")

    # QF Decode (NOAA VBD v23 documentation)
    qf_labels = {
        1: 'QF=1\nKonfirmasi\n(High)',
        2: 'QF=2\nMungkin\n(Medium)',
        3: 'QF=3\nRendah\n(Low)',
        255: 'QF=255\nTidak Valid',
    }
    qf_colors = {1: '#27AE60', 2: '#F39C12', 3: '#E74C3C', 255: '#95A5A6'}

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle(
        'H5 \u00b7 Quality Flag (QF_Detect) Analysis \u2014 Validasi Kualitas Data VBD\n'
        f'Sample: {len(df):,} deteksi | Indonesia 2012\u20132026 | EEZ-filtered',
        fontsize=12, fontweight='bold', y=1.01
    )

    # Panel (a): Distribusi QF overall
    ax = axes[0]
    qf_counts = df['QF_Detect'].value_counts().sort_index()
    bars = ax.bar(
        [qf_labels.get(k, f'QF={k}') for k in qf_counts.index],
        qf_counts.values / len(df) * 100,
        color=[qf_colors.get(k, '#BDC3C7') for k in qf_counts.index],
        edgecolor='white', linewidth=0.5
    )
    for bar, (qf, cnt) in zip(bars, qf_counts.items()):
        pct = cnt / len(df) * 100
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
               f'{pct:.1f}%\n({cnt:,})', ha='center', va='bottom', fontsize=8.5, fontweight='bold')
    ax.set_ylabel('Persentase Deteksi (%)', fontsize=10)
    ax.set_title('(a) Distribusi Quality Flag\nKeseluruhan Dataset', fontsize=11)
    ax.set_ylim(0, 105)
    ax.grid(True, axis='y')

    # Panel (b): Tren temporal QF=1 (%) per tahun
    ax2 = axes[1]
    yearly_qf = df.groupby('year').apply(
        lambda x: pd.Series({
            'pct_qf1':  100 * (x['QF_Detect'] == 1).sum() / len(x),
            'pct_qf2':  100 * (x['QF_Detect'] == 2).sum() / len(x),
            'n':        len(x)
        })
    ).reset_index()

    ax2.fill_between(yearly_qf['year'], yearly_qf['pct_qf1'],
                    alpha=0.25, color='#27AE60')
    ax2.plot(yearly_qf['year'], yearly_qf['pct_qf1'], 'o-',
            color='#27AE60', linewidth=2.5, markersize=8,
            label='QF=1 (Konfirmasi Tinggi)')
    ax2.fill_between(yearly_qf['year'], yearly_qf['pct_qf2'],
                    alpha=0.2, color='#F39C12')
    ax2.plot(yearly_qf['year'], yearly_qf['pct_qf2'], 's--',
            color='#F39C12', linewidth=1.8, markersize=7,
            label='QF=2 (Konfirmasi Sedang)')

    ax2.set_xlabel('Tahun', fontsize=10)
    ax2.set_ylabel('Persentase (%)', fontsize=10)
    ax2.set_title('(b) Tren Temporal Kualitas Deteksi\nper Tahun (2012\u20132026)', fontsize=11)
    ax2.set_xticks(ALL_YEARS)
    ax2.set_xticklabels([str(y)[2:] for y in ALL_YEARS], fontsize=8)
    ax2.legend(fontsize=9)
    ax2.grid(True)
    ax2.set_ylim(0, 110)

    # Annotasi tren
    p0 = yearly_qf[yearly_qf['year'] == yearly_qf['year'].min()]['pct_qf1'].values
    pN = yearly_qf[yearly_qf['year'] == yearly_qf['year'].max()]['pct_qf1'].values
    if len(p0) and len(pN):
        trend_dir = '\u2197 Meningkat' if pN[0] > p0[0] else '\u2198 Menurun'
        ax2.text(0.05, 0.95, f'Tren: {trend_dir}', transform=ax2.transAxes,
                fontsize=9, va='top', color='#2C3E50',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Panel (c): QF per WPP (top 8)
    ax3 = axes[2]
    if 'FMZ' in df.columns:
        top_wpp_qf = df.groupby('FMZ').size().nlargest(8).index.tolist()
        wpp_qf = df[df['FMZ'].isin(top_wpp_qf)].groupby('FMZ').apply(
            lambda x: 100 * (x['QF_Detect'] == 1).sum() / len(x)
        ).sort_values()

        bars2 = ax3.barh(wpp_qf.index, wpp_qf.values,
                        color=['#27AE60' if v >= 70 else '#F39C12' if v >= 50 else '#E74C3C'
                               for v in wpp_qf.values])
        for bar, val in zip(bars2, wpp_qf.values):
            ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}%', va='center', fontsize=8)
        ax3.set_xlabel('% Deteksi QF=1 (Kualitas Tinggi)', fontsize=10)
        ax3.set_title('(c) Proporsi QF=1 per WPP\n(Top 8 berdasarkan volume)', fontsize=11)
        ax3.set_xlim(0, 110)
        ax3.axvline(x=70, color='#E74C3C', linestyle='--', linewidth=1, alpha=0.7)
        ax3.text(71, -0.5, 'Batas 70%', fontsize=7, color='#E74C3C')
        ax3.grid(True, axis='x')

    plt.tight_layout()
    out = os.path.join(F1_DIR, 'H5_quality_flag.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# VIS H1: Correlation Matrix
# ============================================================
def vis_H1():
    print("\n[5/5] H1 -- Correlation Matrix...")
    t = time.time()

    num_cols = ['Rad_DNB','Rad_I04','SMI','SI','SHI','LI',
                'QF_Detect','SOLZ_GDNBO','SATZ_GDNBO','LUNZ_GDNBO','LUNA_GDNBO']

    df = sample_raw(
        needed_cols=num_cols,
        rows_per_year=5000, files_per_year=12
    )
    if df.empty:
        print("  [SKIP] Tidak ada data untuk H1")
        return None

    # Konversi ke numerik
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = np.nan

    # Hanya kolom yang memiliki data cukup (> 10% non-NaN)
    valid_cols = [c for c in num_cols if c in df.columns and
                  df[c].notna().mean() > 0.1]
    df_num = df[valid_cols].dropna()
    print(f"  Kolom valid: {valid_cols}")
    print(f"  Sampel bersih: {len(df_num):,}")

    if len(df_num) < 100:
        print("  [SKIP] Data terlalu sedikit untuk korelasi")
        return None

    # Correlation matrix
    corr = df_num.corr(method='pearson')

    # Label deskriptif
    col_labels = {
        'Rad_DNB':     'Rad\nDNB',
        'Rad_I04':     'Rad\nI04',
        'SMI':         'SMI',
        'SI':          'SI',
        'SHI':         'SHI',
        'LI':          'LI',
        'QF_Detect':   'QF\nDetect',
        'SOLZ_GDNBO':  'SOLZ\n(Sun\nZenith)',
        'SATZ_GDNBO':  'SATZ\n(Sat\nZenith)',
        'LUNZ_GDNBO':  'LUNZ\n(Moon\nZenith)',
        'LUNA_GDNBO':  'LUNA\n(Moon\nAzimuth)',
    }
    corr.columns = [col_labels.get(c, c) for c in corr.columns]
    corr.index   = [col_labels.get(c, c) for c in corr.index]

    fig, axes = plt.subplots(1, 2, figsize=(17, 7),
                             gridspec_kw={'width_ratios': [3, 1]})
    fig.suptitle(
        'H1 \u00b7 Correlation Matrix: Hubungan Antar Atribut Numerik VBD\n'
        f'Pearson r \u2014 Sample: {len(df_num):,} deteksi Indonesia EEZ-filtered',
        fontsize=12, fontweight='bold', y=1.01
    )

    # Panel (a): Heatmap korelasi
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)  # upper triangle
    sns.heatmap(
        corr, ax=axes[0],
        mask=mask,
        cmap='RdBu_r', center=0, vmin=-1, vmax=1,
        annot=True, fmt='.2f', annot_kws={'size': 8},
        linewidths=0.5, linecolor='#EEEEEE',
        cbar_kws={'label': 'Pearson r', 'shrink': 0.8}
    )
    axes[0].set_title('(a) Matriks Korelasi Pearson (Segitiga Bawah)', fontsize=11)
    axes[0].tick_params(axis='both', labelsize=8)

    # Panel (b): Bar chart korelasi tertinggi terhadap Rad_DNB
    ax2 = axes[1]
    if 'Rad\nDNB' in corr.columns:
        rad_corr = corr['Rad\nDNB'].drop('Rad\nDNB').sort_values()
        colors_bar = ['#E74C3C' if v < 0 else '#27AE60' for v in rad_corr.values]
        ax2.barh(rad_corr.index, rad_corr.values, color=colors_bar, edgecolor='white')
        ax2.axvline(x=0, color='black', linewidth=0.8)
        ax2.set_xlabel('Korelasi Pearson r', fontsize=10)
        ax2.set_title('(b) Korelasi terhadap\nRad_DNB (Cahaya Kapal)', fontsize=11)
        ax2.set_xlim(-1.1, 1.1)
        ax2.grid(True, axis='x')
        for i, (label, val) in enumerate(zip(rad_corr.index, rad_corr.values)):
            ax2.text(val + (0.02 if val >= 0 else -0.02), i,
                    f'{val:.2f}', va='center',
                    ha='left' if val >= 0 else 'right', fontsize=8)

    plt.tight_layout()
    out = os.path.join(F1_DIR, 'H1_correlation_matrix.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.0f}s)")
    return out


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    results = {}

    # D2, I1, I2 -- gunakan file Fase 0 (cepat)
    results['D2'] = vis_D2()
    results['I1'] = vis_I1()
    results['I2'] = vis_I2()

    # H5, H1 -- sampling raw CSV (lebih lambat)
    results['H5'] = vis_H5()
    results['H1'] = vis_H1()

    # Ringkasan
    elapsed = time.time() - t0
    print()
    print("=" * 68)
    print(f"FASE 1 SELESAI -- {elapsed:.0f} detik")
    print("=" * 68)
    for code, path in results.items():
        status = "OK" if path else "SKIP"
        print(f"  [{status}] {code}: {os.path.basename(path) if path else '-'}")
    print(f"\nSemua gambar di: {F1_DIR}")
    print("=" * 68)
