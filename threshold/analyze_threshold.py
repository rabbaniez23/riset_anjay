"""
Analisis Distribusi Frekuensi Piksel VBD -- 2012 s/d 2026
Tujuan: Menentukan threshold empiris berbasis data riil untuk visualisasi
Metode: Agregasi koordinat (lat/lon) ke grid piksel VIIRS (~0.00630 deg)
        kemudian hitung distribusi frekuensi kunjungan per piksel.
"""

import os
import sys
import glob
import csv
import math
from collections import defaultdict
import time

# Fix encoding konsol Windows (CP1252 tidak support karakter Unicode khusus)
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ---- KONFIGURASI ------------------------------------------------------------
VIIRS_BASE = r"e:\UNIVERSITAS PENDIDIKAN INDONESIA\PENELITIAN\FISHING GROUND PATTERN\riset_viirs\viirs"
OUTPUT_DIR  = r"e:\UNIVERSITAS PENDIDIKAN INDONESIA\PENELITIAN\FISHING GROUND PATTERN\riset_viirs"

# Resolusi piksel VIIRS DNB ~ 742 m -> ~0.00630 deg pada ekuator
# Dibulatkan ke 0.01 deg (~1.1 km) untuk grid stabil
GRID_DEG = 0.01  # derajat per sel grid

# Kolom yang digunakan
LAT_COL = "Lat_DNB"
LON_COL = "Lon_DNB"
RAD_COL = "Rad_DNB"
QF_COL  = "QF_Detect"
WPP_COL = "FMZ"

YEARS = list(range(2012, 2027))

# ---- FUNGSI BANTU ----------------------------------------------------------

def to_grid_key(lat, lon, deg=GRID_DEG):
    """Snap koordinat ke pusat grid sel."""
    lat_snap = round(math.floor(lat / deg) * deg + deg / 2, 6)
    lon_snap = round(math.floor(lon / deg) * deg + deg / 2, 6)
    return (lat_snap, lon_snap)

def percentile(sorted_list, p):
    """Hitung persentil dari list yang sudah diurutkan."""
    if not sorted_list:
        return 0
    idx = (p / 100) * (len(sorted_list) - 1)
    lower = int(idx)
    upper = lower + 1
    if upper >= len(sorted_list):
        return sorted_list[-1]
    frac = idx - lower
    return sorted_list[lower] * (1 - frac) + sorted_list[upper] * frac

# ---- LANGKAH 1: Hitung frekuensi per piksel seluruh dataset ----------------

SEP1 = "=" * 72
SEP2 = "-" * 72

print(SEP1)
print("ANALISIS THRESHOLD VBD -- DATA EMPIRIS 2012-2026")
print(SEP1)
print(f"\nGrid resolusi: {GRID_DEG} deg (~{GRID_DEG * 111:.1f} km per sel)")
print("\n[1/4] Mulai scanning file CSV...")

pixel_count   = defaultdict(int)   # {(lat,lon): jumlah hari terdeteksi}
pixel_radmax  = defaultdict(float) # {(lat,lon): max radiance}
pixel_radsum  = defaultdict(float) # {(lat,lon): sum radiance}
wpp_counts    = defaultdict(int)   # {wpp: total baris}
year_counts   = defaultdict(int)   # {year: total baris}
radiance_vals = []                 # sample nilai radiance (max 500k)
total_rows    = 0
total_files   = 0
error_files   = 0

t0 = time.time()

for year in YEARS:
    year_dir = os.path.join(VIIRS_BASE, str(year))
    if not os.path.isdir(year_dir):
        print(f"  [SKIP] Direktori tidak ditemukan: {year_dir}")
        continue

    csv_files = sorted(glob.glob(os.path.join(year_dir, "*.csv")))
    year_rows = 0

    for fpath in csv_files:
        fsize = os.path.getsize(fpath)
        if fsize < 500:   # skip file kosong / sangat kecil
            continue

        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        lat = float(row[LAT_COL])
                        lon = float(row[LON_COL])
                        rad = float(row.get(RAD_COL, 0) or 0)
                        wpp = row.get(WPP_COL, "Unknown").strip()

                        # Hanya data di laut (bukan darat)
                        land = int(row.get("Land_Mask", 3) or 3)
                        if land == 1:   # 1 = darat, 3 = laut
                            continue

                        key = to_grid_key(lat, lon)
                        pixel_count[key]  += 1
                        pixel_radsum[key] += rad
                        if rad > pixel_radmax[key]:
                            pixel_radmax[key] = rad

                        if wpp:
                            wpp_counts[wpp] += 1
                        year_counts[year] += 1

                        if len(radiance_vals) < 500_000:
                            radiance_vals.append(rad)

                        total_rows += 1
                        year_rows  += 1

                    except (ValueError, KeyError):
                        continue

            total_files += 1

        except Exception as e:
            error_files += 1

    elapsed = time.time() - t0
    print(f"  {year}: {len(csv_files):4d} files | {year_rows:>9,} baris | elapsed {elapsed:.0f}s")

print(f"\n  Total baris valid : {total_rows:,}")
print(f"  Total files proses: {total_files:,}")
print(f"  File error        : {error_files}")
print(f"  Jumlah piksel unik: {len(pixel_count):,}")

# ---- LANGKAH 2: Distribusi frekuensi piksel --------------------------------

print("\n[2/4] Menghitung distribusi frekuensi piksel...")

freq_list = sorted(pixel_count.values())
total_pixels = len(freq_list)

freq_min   = freq_list[0]
freq_max   = freq_list[-1]
freq_mean  = sum(freq_list) / total_pixels
freq_med   = percentile(freq_list, 50)

pct_targets = [50, 60, 70, 75, 80, 85, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 99.5, 99.9]
pct_vals = {p: percentile(freq_list, p) for p in pct_targets}

brackets = [
    (1,    4,    "Sangat Jarang (1-4 hari)"),
    (5,    9,    "Jarang (5-9 hari)"),
    (10,   19,   "Kadang (10-19 hari)"),
    (20,   49,   "Aktif Rendah (20-49 hari)"),
    (50,   99,   "Aktif Sedang (50-99 hari)"),
    (100,  199,  "Aktif Tinggi (100-199 hari)"),
    (200,  499,  "Hotspot (200-499 hari)"),
    (500,  999,  "Core Hotspot (500-999 hari)"),
    (1000, 9999, "Inti Permanen (>=1000 hari)"),
]

bracket_stats = []
for lo, hi, label in brackets:
    count = sum(1 for v in freq_list if lo <= v <= hi)
    pct   = 100 * count / total_pixels if total_pixels > 0 else 0
    bracket_stats.append((lo, hi, label, count, pct))

# ---- LANGKAH 3: Distribusi radiance ----------------------------------------

print("[3/4] Menghitung distribusi radiance...")

rad_sorted = sorted(radiance_vals)
rad_n      = len(rad_sorted)
rad_mean   = sum(rad_sorted) / rad_n if rad_n else 0
rad_med    = percentile(rad_sorted, 50)

rad_pct_targets = [25, 50, 75, 90, 95, 99, 99.5]
rad_pct = {p: percentile(rad_sorted, p) for p in rad_pct_targets}

rad_brackets = [
    (0,      0.5,   "Ultra-low (<0.5)"),
    (0.5,    2,     "Very low  (0.5-2)"),
    (2,      10,    "Low       (2-10)"),
    (10,     50,    "Med-low   (10-50)"),
    (50,     200,   "Medium    (50-200)"),
    (200,    1000,  "High      (200-1000)"),
    (1000,   1e9,   "Very High (>1000)"),
]

rad_stats = []
for lo, hi, label in rad_brackets:
    count = sum(1 for v in rad_sorted if lo <= v < hi)
    pct   = 100 * count / rad_n if rad_n else 0
    rad_stats.append((lo, hi, label, count, pct))

# ---- LANGKAH 4: WPP Summary ------------------------------------------------

print("[4/4] Menyusun laporan...")

wpp_sorted = sorted(wpp_counts.items(), key=lambda x: -x[1])
total_wpp_rows = sum(wpp_counts.values())

# ---- OUTPUT LAPORAN --------------------------------------------------------

report_path = os.path.join(OUTPUT_DIR, "threshold_analysis_report.txt")

with open(report_path, "w", encoding="utf-8") as out:

    def w(line=""):
        print(line)
        out.write(line + "\n")

    w(SEP1)
    w("LAPORAN ANALISIS THRESHOLD EMPIRIS -- VBD INDONESIA 2012-2026")
    w(SEP1)
    w(f"Grid resolusi    : {GRID_DEG} deg (~{GRID_DEG * 111:.1f} km per sel)")
    w(f"Total baris VBD  : {total_rows:,}")
    w(f"Total piksel unik: {total_pixels:,}")
    w()

    w(SEP2)
    w("STATISTIK DISTRIBUSI FREKUENSI KUNJUNGAN PER PIKSEL (hari)")
    w(SEP2)
    w(f"  Minimum       : {freq_min:,.0f} hari")
    w(f"  Maximum       : {freq_max:,.0f} hari")
    w(f"  Mean          : {freq_mean:,.1f} hari")
    w(f"  Median (P50)  : {freq_med:,.1f} hari")
    w()
    w("  PERSENTIL DISTRIBUSI FREKUENSI:")
    for p, v in pct_vals.items():
        w(f"    P{str(p).ljust(5)} = {v:>8.1f} hari")
    w()

    w(SEP2)
    w("DISTRIBUSI PIKSEL PER BRACKET FREKUENSI")
    w(SEP2)
    w(f"  {'Bracket':<35} {'Jumlah Piksel':>15} {'% Piksel':>10}  {'Cum %':>8}")
    w("  " + "-" * 70)
    cum = 0
    for lo, hi, label, count, pct in bracket_stats:
        cum += pct
        w(f"  {label:<35} {count:>15,} {pct:>9.2f}%  {cum:>7.2f}%")
    w()

    w(SEP2)
    w("REKOMENDASI THRESHOLD BERDASARKAN DATA EMPIRIS")
    w(SEP2)
    p75_v  = pct_vals.get(75, 0)
    p80_v  = pct_vals.get(80, 0)
    p90_v  = pct_vals.get(90, 0)
    p95_v  = pct_vals.get(95, 0)
    p99_v  = pct_vals.get(99, 0)
    p995_v = pct_vals.get(99.5, 0)

    w(f"  DISPLAY  (P75 -- tampilkan 25% piksel teratas) : >= {p75_v:.0f} hari")
    w(f"  STANDARD (P80 -- tampilkan 20% piksel teratas) : >= {p80_v:.0f} hari")
    w(f"  HOTSPOT  (P90 -- tampilkan 10% piksel teratas) : >= {p90_v:.0f} hari")
    w(f"  CORE     (P95 -- tampilkan  5% piksel teratas) : >= {p95_v:.0f} hari")
    w(f"  INTI     (P99 -- tampilkan  1% piksel teratas) : >= {p99_v:.0f} hari")
    w(f"  APEX    (P99.5 -- tampilkan 0.5% teratas)      : >= {p995_v:.0f} hari")
    w()
    w("  INTERPRETASI:")
    w(f"    - Threshold 'Instruksi1.md' (100 hari) setara Persentil: "
      f"P{sum(1 for v in freq_list if v < 100) / total_pixels * 100:.1f}")
    w(f"    - Jumlah piksel yg lolos threshold 100 hari : "
      f"{sum(1 for v in freq_list if v >= 100):,} piksel "
      f"({sum(1 for v in freq_list if v >= 100)/total_pixels*100:.2f}%)")
    w(f"    - Jumlah piksel yg lolos threshold 50 hari  : "
      f"{sum(1 for v in freq_list if v >= 50):,} piksel "
      f"({sum(1 for v in freq_list if v >= 50)/total_pixels*100:.2f}%)")
    w(f"    - Jumlah piksel yg lolos threshold 200 hari : "
      f"{sum(1 for v in freq_list if v >= 200):,} piksel "
      f"({sum(1 for v in freq_list if v >= 200)/total_pixels*100:.2f}%)")
    w()

    w(SEP2)
    w("DISTRIBUSI RADIANCE (nW/cm2/sr) -- SAMPEL")
    w(SEP2)
    w(f"  Sampel n      : {rad_n:,}")
    w(f"  Mean          : {rad_mean:,.3f}")
    w(f"  Median (P50)  : {rad_med:,.3f}")
    w()
    w("  PERSENTIL RADIANCE:")
    for p, v in rad_pct.items():
        w(f"    P{str(p).ljust(5)} = {v:>12.3f} nW/cm2/sr")
    w()
    w(f"  {'Bracket':<30} {'Jumlah':>12} {'%':>8}")
    w("  " + "-" * 52)
    for lo, hi, label, count, pct in rad_stats:
        w(f"  {label:<30} {count:>12,} {pct:>7.2f}%")
    w()

    w(SEP2)
    w("DISTRIBUSI DETEKSI PER WPP (Top 20)")
    w(SEP2)
    w(f"  {'WPP':<40} {'Deteksi':>12} {'%':>8}")
    w("  " + "-" * 62)
    for wpp_name, cnt in wpp_sorted[:20]:
        pct = 100 * cnt / total_wpp_rows if total_wpp_rows else 0
        w(f"  {wpp_name:<40} {cnt:>12,} {pct:>7.2f}%")
    w()

    w(SEP2)
    w("DISTRIBUSI DETEKSI PER TAHUN")
    w(SEP2)
    w(f"  {'Tahun':>6} {'Deteksi':>12} {'%':>8}")
    w("  " + "-" * 30)
    for yr in sorted(year_counts.keys()):
        cnt = year_counts[yr]
        pct = 100 * cnt / total_rows if total_rows else 0
        w(f"  {yr:>6} {cnt:>12,} {pct:>7.2f}%")
    w()

    w(SEP1)
    w(f"Laporan dihasilkan dalam {time.time() - t0:.0f} detik")
    w(SEP1)

print(f"\nLaporan tersimpan di: {report_path}")
