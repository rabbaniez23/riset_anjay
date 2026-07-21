"""
FASE 4: TEMPORAL LANJUTAN -- 5 Visualisasi
===============================================
  A2  -- Time Series Decomposition (Trend, Seasonal, Residual)
  A5  -- Anomaly Detection
  A9  -- Before-After Event Analysis (COVID & Moratorium)
  E1  -- Radiance Trend per Kelas (Armada Temporal)
  A6  -- Change Point Detection

Input (dari Fase 0 output/):
  monthly_aggregated.csv   -> A2, A5, A9, A6
  radiance_sample_log.csv  -> E1

Output: output/fase4/*.png
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
F4_DIR    = os.path.join(OUT_DIR, "fase4")
os.makedirs(F4_DIR, exist_ok=True)

MONTHLY   = os.path.join(OUT_DIR, "monthly_aggregated.csv")
RAD_FILE  = os.path.join(OUT_DIR, "radiance_sample_log.csv")

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

def get_national_monthly():
    """Mengambil time series nasional (bulanan) 2012-2025."""
    df = pd.read_csv(MONTHLY)
    df = df[df['is_partial_year'] == 0]
    df = df[df['month'].between(1, 12)]
    
    # Agregasi nasional
    nat = df.groupby(['year', 'month'])['detection_count'].sum().reset_index()
    
    # Buat dummy date (tanggal 1) untuk indexing
    nat['date'] = pd.to_datetime(nat['year'].astype(str) + '-' + nat['month'].astype(str).str.zfill(2) + '-01')
    nat = nat.sort_values('date').set_index('date')
    return nat

t0 = time.time()
print("=" * 68)
print("FASE 4: TEMPORAL LANJUTAN -- 5 Visualisasi")
print("=" * 68)

# ============================================================
# HELPER: CLASSICAL DECOMPOSITION
# ============================================================
def classical_decompose(series, period=12):
    """Fungsi manual untuk dekomposisi time series (pengganti statsmodels.STL)"""
    # 1. Trend: Rolling mean terpusat
    trend = series.rolling(window=period, center=True).mean()
    
    # 2. Detrended
    detrended = series - trend
    
    # 3. Seasonal: Rata-rata dari detrended untuk setiap bulan
    df_temp = pd.DataFrame({'val': detrended, 'month': detrended.index.month})
    seasonal_pattern = df_temp.groupby('month')['val'].mean()
    seasonal = df_temp['month'].map(seasonal_pattern)
    
    # Rata-ratakan (center) musiman agar mean = 0
    seasonal = seasonal - seasonal.mean()
    
    # 4. Residual
    residual = series - trend - seasonal
    
    return trend, seasonal, residual


# ============================================================
# A2: TIME SERIES DECOMPOSITION
# ============================================================
def vis_A2():
    print("\n[1/5] A2 -- Time Series Decomposition...")
    t = time.time()
    
    nat = get_national_monthly()
    y = nat['detection_count'] / 1e6  # dalam juta
    
    trend, seasonal, resid = classical_decompose(y, period=12)
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    fig.suptitle('A2 \u00b7 Dekomposisi Time Series Bulanan Nasional (2012\u20132025)\nMemisahkan Tren Jangka Panjang, Pola Musiman, dan Noise', 
                 fontsize=12, fontweight='bold', y=0.98)
    
    x = y.index
    
    # 1. Observed
    axes[0].plot(x, y, color='#2C3E50', linewidth=1.5)
    axes[0].set_ylabel('Observasi Asli\n(Juta Deteksi)', fontsize=9)
    axes[0].set_title('1. Observed Data (Total Deteksi Bulanan)', fontsize=10)
    
    # 2. Trend
    axes[1].plot(x, trend, color='#E74C3C', linewidth=2)
    axes[1].set_ylabel('Tren\n(Juta)', fontsize=9)
    axes[1].set_title('2. Komponen Tren (12-month centered moving average)', fontsize=10)
    
    # 3. Seasonal
    axes[2].plot(x, seasonal, color='#27AE60', linewidth=1.5)
    axes[2].set_ylabel('Musiman\n(Juta)', fontsize=9)
    axes[2].set_title('3. Komponen Musiman (Pola berulang tahunan)', fontsize=10)
    axes[2].axhline(0, color='black', linewidth=0.8, alpha=0.5)
    
    # 4. Residual
    axes[3].scatter(x, resid, color='#7F8C8D', alpha=0.7, s=15)
    axes[3].axhline(0, color='black', linewidth=0.8, alpha=0.5)
    axes[3].set_ylabel('Residual\n(Juta)', fontsize=9)
    axes[3].set_title('4. Komponen Residual (Noise / Anomali acak)', fontsize=10)
    axes[3].set_xlabel('Tahun', fontsize=10)
    
    for ax in axes:
        ax.grid(True, alpha=0.3)
        
    plt.tight_layout()
    out = os.path.join(F4_DIR, 'A2_decomposition.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# A5: ANOMALY DETECTION
# ============================================================
def vis_A5():
    print("\n[2/5] A5 -- Anomaly Detection...")
    t = time.time()
    
    nat = get_national_monthly()
    y = nat['detection_count'] / 1e6
    
    # Ambil residual dari dekomposisi
    trend, seasonal, resid = classical_decompose(y, period=12)
    
    # Hitung Z-score pada residual untuk menemukan anomali
    z_scores = (resid - resid.mean()) / resid.std()
    
    # Threshold anomali: Z > 2.0 atau Z < -2.0
    threshold = 2.0
    anomalies = z_scores[abs(z_scores) > threshold]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle(f'A5 \u00b7 Deteksi Anomali pada Residual Bulanan (Threshold |Z| > {threshold})\n'
                 'Mengidentifikasi lonjakan atau penurunan drastis di luar tren dan musiman normal', 
                 fontsize=12, fontweight='bold', y=0.98)
    
    # Plot data asli
    ax.plot(y.index, y, color='#34495E', linewidth=1.5, label='Deteksi Bulanan (Juta)', zorder=1)
    
    # Tandai anomali di kurva asli
    anomaly_dates = anomalies.index
    anomaly_vals = y[anomaly_dates]
    
    # Bedakan warna positif (hijau) dan negatif (merah)
    pos_anom = anomaly_dates[z_scores[anomaly_dates] > 0]
    neg_anom = anomaly_dates[z_scores[anomaly_dates] < 0]
    
    ax.scatter(pos_anom, y[pos_anom], color='#E74C3C', s=80, label=f'Anomali Positif (Z > {threshold})', zorder=2)
    ax.scatter(neg_anom, y[neg_anom], color='#F39C12', s=80, label=f'Anomali Negatif (Z < -{threshold})', zorder=2)
    
    # Tambahkan trendline sbg referensi
    ax.plot(trend.index, trend, color='#95A5A6', linestyle='--', linewidth=1.5, label='Tren Baseline', zorder=0)
    
    # Anotasi teks pada anomali
    for date in anomaly_dates:
        ax.annotate(date.strftime('%b %Y'), (date, y[date]), 
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7, ec="none"))

    ax.set_ylabel('Total Deteksi (Juta Baris)', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=9)
    
    plt.tight_layout()
    out = os.path.join(F4_DIR, 'A5_anomaly_detection.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# A9: BEFORE-AFTER EVENT ANALYSIS
# ============================================================
def vis_A9():
    print("\n[3/5] A9 -- Before-After Event Analysis...")
    t = time.time()
    
    # Kita bandingkan dua event besar:
    # 1. Moratorium / Kebijakan Susi (2014 akhir) -> Bandingkan 2012-2014 vs 2015-2017
    # 2. COVID-19 (Mulai 2020) -> Bandingkan 2018-2019 vs 2020-2021
    
    df = pd.read_csv(MONTHLY)
    df = df[df['is_partial_year'] == 0]
    df = df[df['month'].between(1, 12)]
    
    # Agregasi nasional bulanan
    nat = df.groupby(['year', 'month'])['detection_count'].sum().reset_index()
    nat['det_juta'] = nat['detection_count'] / 1e6
    
    def get_period_avg(y_start, y_end):
        subset = nat[(nat['year'] >= y_start) & (nat['year'] <= y_end)]
        return subset.groupby('month')['det_juta'].mean()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('A9 \u00b7 Analisis Dampak Peristiwa Besar: Rata-Rata Pola Bulanan Sebelum vs Sesudah', 
                 fontsize=12, fontweight='bold', y=1.02)
    
    months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Ags','Sep','Okt','Nov','Des']
    
    # Event 1: Era Menteri Susi (Illegal Fishing Crackdown ~2015)
    pre_susi = get_period_avg(2012, 2014)
    post_susi = get_period_avg(2015, 2017)
    
    axes[0].plot(months, pre_susi, marker='o', color='#3498DB', linewidth=2, label='Pre-Kebijakan (2012-2014)')
    axes[0].plot(months, post_susi, marker='s', color='#E74C3C', linewidth=2, label='Post-Kebijakan (2015-2017)')
    axes[0].fill_between(months, pre_susi, post_susi, where=(pre_susi >= post_susi), interpolate=True, color='red', alpha=0.1)
    axes[0].fill_between(months, pre_susi, post_susi, where=(pre_susi < post_susi), interpolate=True, color='green', alpha=0.1)
    axes[0].set_title('(a) Dampak Kebijakan Anti-IUU Fishing\n(Meskipun kapal ilegal hilang, deteksi lokal justru tumbuh)', fontsize=10)
    axes[0].set_ylabel('Rata-rata Deteksi per Bulan (Juta)', fontsize=10)
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3)
    
    # Event 2: COVID-19 Pandemi
    pre_covid = get_period_avg(2018, 2019)
    covid = get_period_avg(2020, 2021)
    
    axes[1].plot(months, pre_covid, marker='o', color='#3498DB', linewidth=2, label='Pre-COVID (2018-2019)')
    axes[1].plot(months, covid, marker='s', color='#E74C3C', linewidth=2, label='COVID Era (2020-2021)')
    axes[1].fill_between(months, pre_covid, covid, where=(pre_covid >= covid), interpolate=True, color='red', alpha=0.1)
    axes[1].fill_between(months, pre_covid, covid, where=(pre_covid < covid), interpolate=True, color='green', alpha=0.1)
    axes[1].set_title('(b) Dampak Pandemi COVID-19\n(Perubahan aktivitas penangkapan selama pembatasan)', fontsize=10)
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    out = os.path.join(F4_DIR, 'A9_event_analysis.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# E1: RADIANCE TREND PER KELAS
# ============================================================
def vis_E1():
    print("\n[4/5] E1 -- Radiance Trend per Kelas Armada...")
    t = time.time()
    
    # Load 300k sampel dari radiance (Fase 2 logic)
    dtype_map = {'year': 'int16', 'rad_class': 'category', 'radiance_raw': 'float32'}
    df = pd.read_csv(RAD_FILE, usecols=['year', 'rad_class', 'radiance_raw'], 
                     dtype=dtype_map, nrows=300_000, low_memory=False)
    
    df = df[df['year'] < 2026]
    
    # Hitung proporsi kelas per tahun
    yearly_counts = df.groupby(['year', 'rad_class']).size().unstack(fill_value=0)
    yearly_pct = yearly_counts.div(yearly_counts.sum(axis=1), axis=0) * 100
    
    # Warna empiris Fase 2
    colors = {'tradisional': '#27AE60', 'menengah': '#F39C12', 'industri': '#E74C3C', 'anomali': '#8E44AD'}
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('E1 \u00b7 Dinamika Temporal Kelas Armada (2012\u20132025)\nApakah armada penangkapan ikan Indonesia menjadi lebih besar/terang seiring waktu?', 
                 fontsize=12, fontweight='bold', y=1.02)
    
    years = yearly_pct.index
    
    # Panel a: 100% Stacked Area Chart (Komposisi relatif)
    axes[0].stackplot(years, 
                      yearly_pct['tradisional'], yearly_pct['menengah'], 
                      yearly_pct['industri'], yearly_pct['anomali'],
                      labels=['Tradisional (<10)', 'Menengah (10-100)', 'Industri (100-1000)', 'Anomali (>1000)'],
                      colors=[colors['tradisional'], colors['menengah'], colors['industri'], colors['anomali']],
                      alpha=0.85)
    
    axes[0].set_title('(a) Evolusi Komposisi Kelas Armada (%)', fontsize=10)
    axes[0].set_ylabel('Proporsi (%)', fontsize=10)
    axes[0].set_xlim(years.min(), years.max())
    axes[0].set_ylim(0, 100)
    axes[0].legend(loc='lower left', fontsize=8)
    
    # Panel b: Median Radiance per Tahun (Apakah lampu makin terang?)
    median_rad = df.groupby('year')['radiance_raw'].median()
    mean_rad = df.groupby('year')['radiance_raw'].mean()
    
    axes[1].plot(years, median_rad, marker='o', color='#2980B9', linewidth=2.5, label='Median Radiance (Tipikal Kapal)')
    axes[1].set_title('(b) Tren Intensitas Cahaya (Median Radiance Nasional)', fontsize=10)
    axes[1].set_ylabel('Radiance (nW/cm\u00b2/sr)', fontsize=10)
    axes[1].set_xticks(years)
    axes[1].grid(True, alpha=0.3)
    
    # Regresi trendline
    slope, intercept, _, _, _ = stats.linregress(years, median_rad)
    axes[1].plot(years, slope * years + intercept, linestyle='--', color='red', alpha=0.7, 
                 label=f'Tren: {slope:+.2f} nW/tahun')
    axes[1].legend(fontsize=9)
    
    plt.tight_layout()
    out = os.path.join(F4_DIR, 'E1_radiance_class_trend.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# A6: CHANGE POINT DETECTION (Rolling Diff)
# ============================================================
def vis_A6():
    print("\n[5/5] A6 -- Change Point Detection...")
    t = time.time()
    
    nat = get_national_monthly()
    y = nat['detection_count'] / 1e6
    
    # Kita gunakan pendekatan deteksi Breakpoint sederhana:
    # Membandingkan rolling mean (12 bulan ke belakang) vs (12 bulan ke depan)
    # Titik di mana selisih keduanya paling besar adalah potensi "Structural Break" / Change Point
    
    window = 12
    roll_backward = y.rolling(window=window).mean()
    # Menggeser rolling backward ke belakang untuk mensimulasikan rolling forward
    roll_forward = y.iloc[::-1].rolling(window=window).mean().iloc[::-1]
    
    # Selisih persentase antara "kondisi ke depan" vs "kondisi ke belakang"
    diff = (roll_forward - roll_backward) / roll_backward * 100
    
    # Cari puncak-puncak (perubahan paling drastis)
    # Exclude pinggiran NaN
    valid_diff = diff.dropna()
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle('A6 \u00b7 Change Point Detection: Deteksi Perubahan Struktural dalam Time Series\nMencari titik waktu di mana aktivitas berubah rezim (meningkat drastis / anjlok)', 
                 fontsize=12, fontweight='bold', y=0.98)
    
    x = y.index
    
    # Plot atas: Data asli + rolling window
    axes[0].plot(x, y, color='#BDC3C7', linewidth=1, label='Deteksi Bulanan', alpha=0.8)
    axes[0].plot(x, roll_backward, color='#2980B9', linewidth=2, label=f'{window}-Mo Trailing Mean (Belakang)')
    axes[0].plot(x, roll_forward, color='#E67E22', linewidth=2, label=f'{window}-Mo Leading Mean (Depan)')
    axes[0].set_ylabel('Total Deteksi (Juta)', fontsize=10)
    axes[0].set_title('(a) Perbandingan Rata-rata 1 Tahun ke Belakang vs 1 Tahun ke Depan', fontsize=10)
    axes[0].legend(fontsize=9, loc='upper left')
    axes[0].grid(True, alpha=0.3)
    
    # Plot bawah: Delta persentase (Change indicator)
    axes[1].plot(valid_diff.index, valid_diff, color='#8E44AD', linewidth=2, label='Delta Perubahan Rezim (%)')
    axes[1].axhline(0, color='black', linewidth=1)
    
    # Beri area shading untuk fluktuasi normal (misal +-20%)
    axes[1].fill_between(valid_diff.index, -20, 20, color='gray', alpha=0.15, label='Batas Toleransi (±20%)')
    
    # Temukan titik-titik perubahan ekstrem (>30% atau <-30%)
    ext_pos = valid_diff[valid_diff > 35]
    ext_neg = valid_diff[valid_diff < -25]
    
    if not ext_pos.empty:
        # Ambil titik lokal maksimum
        cp_pos = ext_pos.idxmax()
        axes[1].axvline(cp_pos, color='green', linestyle='--', linewidth=1.5)
        axes[1].annotate(f'Upward Shift\n{cp_pos.strftime("%b %Y")}', 
                         (cp_pos, valid_diff[cp_pos]), xytext=(0, 15), textcoords='offset points', 
                         ha='center', color='green', fontweight='bold', fontsize=8)
                         
    if not ext_neg.empty:
        # Ambil titik lokal minimum
        cp_neg = ext_neg.idxmin()
        axes[1].axvline(cp_neg, color='red', linestyle='--', linewidth=1.5)
        axes[1].annotate(f'Downward Shift\n{cp_neg.strftime("%b %Y")}', 
                         (cp_neg, valid_diff[cp_neg]), xytext=(0, -25), textcoords='offset points', 
                         ha='center', color='red', fontweight='bold', fontsize=8)

    axes[1].set_ylabel('Perbedaan (%) Depan vs Belakang', fontsize=10)
    axes[1].set_title('(b) Change Point Indicator (Titik di mana garis ungu menjauhi nol secara drastis)', fontsize=10)
    axes[1].set_xlabel('Tahun', fontsize=10)
    axes[1].legend(fontsize=9, loc='upper right')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    out = os.path.join(F4_DIR, 'A6_change_point_detection.png')
    plt.savefig(out)
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    results = {}
    results['A2'] = vis_A2()
    results['A5'] = vis_A5()
    results['A9'] = vis_A9()
    results['E1'] = vis_E1()
    results['A6'] = vis_A6()

    elapsed = time.time() - t0
    print()
    print("=" * 68)
    print(f"FASE 4 SELESAI -- {elapsed:.0f} detik")
    print("=" * 68)
    for code, path in results.items():
        status = "OK" if path else "SKIP"
        print(f"  [{status}] {code}: {os.path.basename(path) if path else '-'}")
    print(f"\nSemua gambar di: {F4_DIR}")
    print("=" * 68)
