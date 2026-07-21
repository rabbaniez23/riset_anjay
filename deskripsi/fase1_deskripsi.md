# Fase 1 — Deskripsi Lengkap Visualisasi Fondasi Data
## VBD Indonesia 2012–2026 · VIIRS Boat Detection

> Semua visualisasi menggunakan data yang sudah difilter EEZ Indonesia dan diproses Fase 0.
> Threshold mengacu pada **ThresholdEmpiris.md** (komputasi 17,8 juta baris VBD nyata).

---

## D2 · ECDF Frekuensi Kunjungan Kapal per Piksel

### Apa yang Ditampilkan
Kurva ECDF (*Empirical Cumulative Distribution Function*) menunjukkan distribusi kumulatif frekuensi kunjungan kapal per sel piksel. Sumbu-X = jumlah hari suatu piksel terdeteksi kapal; sumbu-Y = probabilitas kumulatif (0–1).

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `freq_days` | `output/pixel_grid_all.csv` | Jumlah total hari berbeda di mana sebuah piksel (0.01°×0.01°) memiliki ≥1 deteksi kapal selama 2012–2026 |
| `wpp_dominant` | `output/pixel_grid_all.csv` | WPP yang paling sering muncul di piksel tersebut |

### Proses yang Dilalui
1. Baca `pixel_grid_all.csv` (1.270.431 baris, hasil Fase 0)
2. Sort ascending nilai `freq_days` → membentuk distribusi empiris
3. **Subsample 50.000 titik** terdistribusi merata (efisiensi memori; akurasi statistik terjaga)
4. Hitung probabilitas kumulatif: `posisi_rank / total_piksel`
5. Plot dua panel: (a) skala linear 0–250 hari, (b) skala log penuh 1–13.279 hari
6. Tambahkan garis vertikal di tiap threshold L1–L6 dengan anotasi persentase piksel lolos

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **ECDF** | *Empirical Cumulative Distribution Function* — kurva yang menunjukkan proporsi data ≤ X. Tidak perlu binning, representasi distribusi yang paling akurat. |
| **Piksel (grid 0.01°)** | Sel grid ~1.1 km × 1.1 km. `freq_days` = berapa hari berbeda ada kapal di dalamnya selama 14 tahun. |
| **Subsample ECDF** | Mengambil N titik merata dari distribusi yang diurutkan; ECDF tetap akurat karena titik dipilih proporsional. |
| **P80, P90, dst.** | Persentil: P90 = 22 hari → 90% piksel dikunjungi ≤22 hari, 10% dikunjungi >22 hari. |
| **Power-law/Pareto** | Distribusi ekor panjang — sebagian kecil piksel mendapat kunjungan sangat sering. Terlihat sebagai garis lurus di plot log-log. |

### Nilai Ilmiah
Grafik ini adalah **bukti empiris justifikasi threshold** di bagian *Methods* paper. Membuktikan bahwa 66,7% piksel hanya 1–4 hari (noise), dan threshold 22 hari = P90 secara terukur.

---

## I1 · Data Coverage Temporal Heatmap

### Apa yang Ditampilkan
Heatmap dua panel: (a) intensitas deteksi per bulan×tahun (log-scale), (b) coverage biner ada/tidak ada data. Sel kosong dapat berarti tidak ada kapal ATAU tidak ada data satelit (awan, orbit gap).

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `year` | `output/monthly_aggregated.csv` | Tahun 2012–2026 |
| `month` | `output/monthly_aggregated.csv` | Bulan 1–12 |
| `detection_count` | `output/monthly_aggregated.csv` | Jumlah baris deteksi kapal semua WPP pada bulan dan tahun tersebut |
| `is_partial_year` | `output/monthly_aggregated.csv` | Flag: 1 = tahun 2026 (parsial, s/d Juli) |

### Proses yang Dilalui
1. Baca `monthly_aggregated.csv`, filter bulan 1–12
2. Group by (year, month), sum `detection_count` dari semua WPP
3. Pivot table: year=baris, month=kolom
4. Log-transform (`log1p`) untuk panel intensitas
5. Binarisasi (>0 → 1) untuk panel coverage
6. Tandai 2026 dengan kotak border biru (parsial)

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Temporal Coverage** | Kelengkapan rekaman data sepanjang waktu — apakah tiap bulan×tahun punya deteksi |
| **log1p transform** | log(1+x) — aman untuk x=0 (tidak menghasilkan -∞ seperti log biasa); berguna saat range data sangat besar |
| **Coverage Biner** | Hanya nilai ADA/TIDAK ADA — mengidentifikasi gap temporal yang mempengaruhi analisis tren |
| **Data Parsial (2026)** | Data 2026 hanya sampai Juli 2026; dikecualikan dari analisis tren tahunan penuh |

### Nilai Ilmiah
Mengidentifikasi gap temporal sebelum analisis dimulai. Mendukung klaim validitas "dataset 14 tahun penuh" di bagian *Data Description* paper.

---

## I2 · Cloud Cover Bias Analysis

### Apa yang Ditampilkan
Analisis apakah pola deteksi bulanan dipengaruhi cloud cover musiman. Sensor VIIRS DNB tidak menembus awan tebal → bulan musim hujan (Muson Barat) menghasilkan lebih sedikit deteksi bukan karena lebih sedikit kapal, tapi karena sensor terblok.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `year`, `month` | `output/monthly_aggregated.csv` | Dimensi temporal |
| `detection_count` | `output/monthly_aggregated.csv` | Jumlah deteksi per WPP per bulan per tahun |
| `wpp` | `output/monthly_aggregated.csv` | Identitas Wilayah Pengelolaan Perikanan |
| `is_partial_year` | `output/monthly_aggregated.csv` | Filter kecualikan 2026 |

### Proses yang Dilalui
1. Filter hanya tahun penuh 2012–2025
2. Sum `detection_count` per (year, month) lintas semua WPP
3. Statistik bulanan: mean, std, median, Q25, Q75 per bulan 1–12 lintas 14 tahun
4. Panel (a): Plot mean ± std + IQR + shading musim muson
5. Panel (b): Per WPP top-6 pola bulanan masing-masing
6. Anotasi bulan tertinggi dan terendah

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Cloud Cover Bias** | Bias pengamatan akibat awan — deteksi lebih sedikit bukan karena kapal berkurang |
| **Muson Barat (Des–Feb)** | Angin dari Samudra Hindia → hujan deras di Jawa/Sumatera → cloud cover tinggi |
| **Muson Timur (Jun–Ags)** | Relatif kering di selatan Indonesia → lebih cerah → deteksi lebih banyak |
| **Peralihan I & II** | Transisi antar musim (Mar–Mei & Sep–Nov) — cuaca bervariasi |
| **IQR** | *Interquartile Range* = Q75 – Q25; representasi variabilitas antar-tahun pada bulan yang sama |

### Nilai Ilmiah
Mengidentifikasi bulan dengan deteksi rendah akibat cloud bias (bukan tidak ada kapal). Penting untuk bagian *Limitations* paper: "detections may be underestimated during wet monsoon season."

---

## H5 · Quality Flag (QF_Detect) Analysis

### Apa yang Ditampilkan
Distribusi dan tren temporal kualitas deteksi berdasarkan `QF_Detect` — flag yang menilai kepercayaan bahwa suatu deteksi adalah kapal nyata, bukan noise/interferensi.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `QF_Detect` | Raw CSV (sampling ~135k baris) | Quality Flag: 1=tinggi, 2=sedang, 3=rendah, 255=tidak valid |
| `FMZ` | Raw CSV | WPP (*Fishing Management Zone*) |
| `EEZ` | Raw CSV | Filter EEZ Indonesia |
| `year` | Dari direktori file | Tahun sumber |

### Proses yang Dilalui
1. **Sampling stratifikasi**: ~9.000 baris per tahun, ~15 file merata per tahun → total ~135.000 baris
2. Filter EEZ Indonesia + non-daratan saat baca
3. Konversi numerik `QF_Detect`, buang NaN
4. Panel (a): Bar chart distribusi proporsi QF (%)
5. Panel (b): Tren % QF=1 dan QF=2 per tahun (2012–2026)
6. Panel (c): Proporsi QF=1 per WPP top-8

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **QF_Detect** | *Quality Flag Detection* — penilaian kepercayaan algoritma VBD bahwa deteksi adalah kapal nyata |
| **QF=1** | Memenuhi semua kriteria: radiance spike signifikan, SMI/SI/SHI di atas threshold, tidak ada interferensi bulan/matahari |
| **QF=2** | Memenuhi sebagian besar kriteria — mungkin kapal kecil atau kondisi atmosfer tidak ideal |
| **QF=3** | Deteksi lemah — eksplorasi saja, tidak untuk analisis utama |
| **QF=255** | Gagal semua kriteria — invalid, tidak digunakan |
| **VIIRS VBD v23** | Versi 2.3 algoritma VIIRS Boat Detection dari NOAA/JPSS — standar saat ini |
| **Sampling Stratifikasi** | N baris per tahun dari file dipilih merata → semua periode musim terwakili |

### Nilai Ilmiah
Memvalidasi bahwa dominasi QF=1 membuktikan dataset berkualitas tinggi. Tren QF per tahun mengkonfirmasi konsistensi data 14 tahun. Variasi per WPP bisa mengindikasikan interferensi lokal (cahaya kota).

---

## H1 · Correlation Matrix Atribut Numerik VBD

### Apa yang Ditampilkan
Matriks korelasi Pearson antar semua atribut numerik dataset VBD. Menunjukkan kekuatan dan arah hubungan antar variabel, terutama dengan `Rad_DNB` (cahaya kapal yang diamati).

### Kolom yang Digunakan
| Kolom | Deskripsi Lengkap | Unit |
|-------|-------------------|------|
| `Rad_DNB` | Radiance pita tampak (Day/Night Band) — sinyal utama cahaya kapal | nW/cm²/sr |
| `Rad_I04` | Radiance inframerah 3.7 µm — panas yang dipancarkan kapal | nW/cm²/sr |
| `SMI` | *Spike Maximum Intensity* — rasio radiance puncak vs rata-rata piksel sekitar | dimensionless |
| `SI` | *Spike Index* — ketajaman "lonjakan" sinyal di atas latar belakang | dimensionless |
| `SHI` | *Spike Height Index* — tinggi puncak sinyal dibandingkan noise floor | dimensionless |
| `LI` | *Lamp Index* — estimasi daya lampu kapal dari geometri + radiance | dimensionless |
| `QF_Detect` | Quality Flag (1, 2, 3, 255) | - |
| `SOLZ_GDNBO` | *Solar Zenith Angle* — sudut matahari dari zenith saat akuisisi | derajat (harus >90° karena malam) |
| `SATZ_GDNBO` | *Satellite Zenith Angle* — sudut pandang satelit (0°=nadir) | derajat |
| `LUNZ_GDNBO` | *Lunar Zenith Angle* — posisi bulan; >90° = bulan di bawah horizon | derajat |
| `LUNA_GDNBO` | *Lunar Azimuth Angle* — arah bulan terhadap utara | derajat |

### Proses yang Dilalui
1. Sampling ~5.000 baris per tahun dari raw CSV (~75.000 total)
2. Filter EEZ Indonesia + non-daratan
3. Konversi numerik semua kolom, buang baris dengan banyak NaN
4. Hitung **matriks korelasi Pearson** semua pasangan kolom
5. Panel (a): Heatmap korelasi segitiga bawah (diagonal=1, atas=mirror → tidak ditampilkan)
6. Panel (b): Bar chart korelasi tiap variabel terhadap `Rad_DNB`

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Pearson r** | Koefisien korelasi linear (-1 s/d +1). r=+1 = positif sempurna, r=0 = tidak ada korelasi linear, r=-1 = negatif sempurna |
| **Rad_DNB** | Sinyal utama — cahaya kapal yang ditangkap sensor DNB VIIRS. Variabel dependen utama |
| **SMI/SI/SHI** | Tiga indeks yang memastikan "spike" adalah kapal, bukan noise. Tinggi untuk kapal bercahaya terang |
| **LI (Lamp Index)** | Estimasi total daya lampu kapal — sangat berkorelasi dengan Rad_DNB (keduanya derived dari sinyal yang sama) |
| **SOLZ > 90°** | Matahari di bawah horizon → malam hari (syarat mutlak data VBD) |
| **SATZ rendah (0°–30°)** | Satelit hampir tepat di bawah (nadir) → kualitas geometri terbaik, distorsi minimal |
| **LUNZ > 90°** | Bulan di bawah horizon → tidak ada interferensi cahaya bulan → deteksi lebih bersih |
| **Segitiga Bawah** | Matriks korelasi simetrik (r_AB = r_BA), cukup satu sisi untuk menghindari redundansi |
| **Multikolinearitas** | Korelasi tinggi antar prediktor → SMI, SI, SHI sangat berkorelasi satu sama lain → gunakan satu saja dalam model |

### Nilai Ilmiah
- Mengidentifikasi **multikolinearitas** → basis untuk *feature selection* jika dibuat model prediktif
- Membuktikan **LI ≈ fungsi dari Rad_DNB** (redundant dalam analisis)
- Hubungan LUNZ dengan Rad_DNB mengkonfirmasi *lunar interference effect* — penting dikontrol dalam analisis

---

## Ringkasan File Output

| Kode | File PNG | Dibuat Dari |
|------|----------|-------------|
| D2 | `D2_ecdf_threshold.png` | `pixel_grid_all.csv` |
| I1 | `I1_data_coverage.png` | `monthly_aggregated.csv` |
| I2 | `I2_cloud_cover_bias.png` | `monthly_aggregated.csv` |
| H5 | `H5_quality_flag.png` | Raw CSV (sampling) |
| H1 | `H1_correlation_matrix.png` | Raw CSV (sampling) |

> Filter universal: EEZ = "Indonesian Exclusive Economic Zone" · Land_Mask ≠ 1 · 2026 = parsial
>
> *Threshold empiris dari komputasi 17.833.394 baris VBD · Grid 0.01° · 504 detik*
