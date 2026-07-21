# Fase 2 — Deskripsi Lengkap Visualisasi Statistik Deskriptif
## VBD Indonesia 2012–2026 · VIIRS Boat Detection

> Semua visualisasi menggunakan file output Fase 0 yang sudah difilter EEZ Indonesia.
> Input utama: `output/yearly_aggregated.csv` dan `output/radiance_sample_log.csv`

---

## V2 · Pareto Chart WPP — *Ranking Aktivitas Penangkapan Ikan*

### Mengapa Dibuat?
Sebelum membuat peta atau analisis temporal, kita perlu tahu **WPP mana yang paling dominan** dalam dataset. Jika distribusi sangat tidak merata (misalnya satu WPP mendominasi 40%+), maka:
- Threshold global akan bias ke WPP dominan
- Visualisasi nasional akan "didominasi" satu wilayah
- Perlu pertimbangan threshold adaptif per WPP

Chart ini mengaplikasikan **Prinsip Pareto (80/20)** — berapa banyak WPP yang menyumbang 80% total deteksi nasional?

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `wpp` | `yearly_aggregated.csv` | Nama Wilayah Pengelolaan Perikanan |
| `detection_count` | `yearly_aggregated.csv` | Jumlah baris deteksi kapal per tahun per WPP |
| `is_partial_year` | `yearly_aggregated.csv` | Filter: buang 2026 (parsial) |

### Proses yang Dilalui
1. Baca `yearly_aggregated.csv`, filter `is_partial_year == 0` (hanya 2012–2025)
2. **Sum** `detection_count` per WPP lintas semua tahun → total per WPP
3. **Sort descending** → WPP terbesar pertama
4. Hitung `pct` (%) dan `cum_pct` (kumulatif %) tiap WPP
5. Plot **bar chart** (sumbu kiri = volume juta deteksi) + **garis kumulatif** (sumbu kanan = %)
6. Gambar garis horizontal di 80% dan 95% sebagai referensi
7. Beri shading "vital few" untuk WPP yang membentuk 80% pertama

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Prinsip Pareto (80/20)** | Fenomena di mana ~20% entitas menyumbang ~80% dampak. Dalam konteks ini: berapa WPP (dari total ~15 WPP) yang menghasilkan 80% seluruh deteksi Indonesia? |
| **"Vital Few"** | Istilah Pareto — WPP-WPP paling dominan yang harus diprioritaskan dalam analisis |
| **Persentase Kumulatif** | Jumlah akumulatif persentase dari WPP pertama sampai ke-N; mencapai 100% saat semua WPP dihitung |
| **WPP (Wilayah Pengelolaan Perikanan)** | Pembagian administratif perairan Indonesia oleh KKP (Kementerian Kelautan dan Perikanan); ada 11 WPP-NRI (711–718 + Danau/Waduk) |

### Insight yang Diperoleh
- **WPP712 (Laut Jawa) = 41,8% deteksi nasional** — konfirmasi dari ThresholdEmpiris.md
- Dari prinsip Pareto, hanya **2–3 WPP** kemungkinan sudah menyumbang 80% deteksi
- Ini membuktikan perlunya **threshold adaptif per WPP** agar visualisasi tidak bias ke Laut Jawa

---

## D1 · Radiance Class Histogram — *Profil Komposisi Armada Kapal*

### Mengapa Dibuat?
Radiance (kecerahan cahaya) adalah **proxy ukuran armada kapal** — kapal besar dengan generator dan lampu industri menghasilkan radiance jauh lebih tinggi dari perahu nelayan dengan lampu kecil. Histogram ini menjawab: **"Seperti apa komposisi armada kapal yang beroperasi di perairan Indonesia?"**

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `radiance_raw` | `radiance_sample_log.csv` | Nilai radiance asli dalam nW/cm²/sr |
| `radiance_log1p` | `radiance_sample_log.csv` | Nilai log(1 + radiance) — untuk distribusi |
| `rad_class` | `radiance_sample_log.csv` | Kelas armada: tradisional/menengah/industri/anomali |
| `year` | `radiance_sample_log.csv` | Tahun — untuk analisis temporal kelas |

### Proses yang Dilalui
1. Baca 300.000 sampel dari `radiance_sample_log.csv` dengan dtype float32 (hemat RAM)
2. Filter: buang nilai ≤ 0 (tidak valid secara fisika)
3. **Panel (a)**: Histogram dengan bins logaritmik (0.1–100.000 nW/cm²/sr), tiap kelas warna berbeda
4. **Panel (b)**: Donut chart proporsi volume deteksi per kelas
5. **Panel (c)**: Bar chart median vs mean per kelas (log-scale Y) — menunjukkan skewness dalam kelas

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Radiance (nW/cm²/sr)** | Kecerahan cahaya per unit area per unit sudut solid. Satuan: nano-watt per sentimeter-persegi per steradian. Semakin besar = semakin terang |
| **Kelas Tradisional (<10 nW)** | Perahu/kapal kecil dengan lampu 12V/LED sederhana; ~60% deteksi; mayoritas nelayan lokal |
| **Kelas Menengah (10–100 nW)** | Kapal kayu menengah, kapal ikan komersial kecil; ~38% deteksi |
| **Kelas Industri (100–1000 nW)** | Kapal ikan komersial besar, kapal survey, kapal pengolah; ~2% deteksi |
| **Kelas Anomali (>1000 nW)** | Platform minyak, kapal ultra-besar, atau noise sensor; <0.4% deteksi |
| **Logarithmic Bins** | Bin histogram yang lebarnya meningkat secara logaritmik — diperlukan saat data mencakup beberapa order of magnitude (dari 0.1 hingga 100.000) |
| **Median vs Mean** | Untuk distribusi skewed: median lebih representatif dari "tipikal" kapal; mean ditarik ke atas oleh outlier (kapal sangat terang) |

### Insight yang Diperoleh
- **~60% armada adalah kapal tradisional kecil** → mayoritas nelayan Indonesia masih skala kecil
- Mean jauh lebih besar dari median dalam setiap kelas → distribusi power-law bahkan di dalam kelas
- Armada industri hanya 2% deteksi tapi mungkin menyumbang porsi besar biomass yang ditangkap → penting untuk kebijakan perikanan

---

## V7 · Box/Violin Radiance per WPP — *Perbedaan Profil Armada Antar Wilayah*

### Mengapa Dibuat?
Profil armada nasional (D1) tidak cukup — kita perlu tahu **apakah setiap WPP memiliki karakteristik armada yang berbeda**. Apakah Laut Arafura (WPP718) didominasi kapal asing besar? Apakah Laut Jawa (WPP712) memang didominasi nelayan kecil? Violin + box plot per WPP menjawab ini secara visual.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `wpp` | `radiance_sample_log.csv` | WPP asal deteksi |
| `radiance_log1p` | `radiance_sample_log.csv` | Radiance log-transformed untuk visualisasi |
| `rad_class` | `radiance_sample_log.csv` | Kelas armada |

### Proses yang Dilalui
1. Identifikasi **top 12 WPP** berdasarkan volume deteksi
2. Subsample maksimum **8.000 baris per WPP** (untuk efisiensi memori)
3. Hitung median per WPP → urutkan WPP dari median terendah ke tertinggi
4. **Panel (a)**: `seaborn.violinplot` horizontal + overlay `seaborn.boxplot` (median = garis merah)
5. **Panel (b)**: Boxplot biasa dengan anotasi nilai median asli (setelah di-invers dari log1p)
6. Garis referensi vertikal: log(1+6.38) = median nasional

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Violin Plot** | Gabungan KDE (distribusi) dan box plot. Lebar violin = densitas probabilitas pada nilai tersebut; semakin lebar = semakin banyak data di sana |
| **Box Plot** | Menampilkan Q25, median, Q75 (kotak) + whisker (1.5×IQR) + outlier (titik) |
| **IQR (Interquartile Range)** | Q75 – Q25; representasi "rentang tengah" 50% data |
| **log1p(Radiance)** | log(1 + radiance) — digunakan karena radiance mendekati 0 hingga 100.000+ (perlu transformasi agar skala visual wajar) |
| **Median Nasional** | Garis vertikal abu-abu = log(1+6.38) = nilai tengah seluruh dataset Indonesia |
| **Nadir** | Titik tepat di bawah satelit — satelit di nadir (SATZ≈0°) menghasilkan resolusi spasial terbaik |

### Insight yang Diperoleh
- Variasi distribusi radiance antar WPP mengungkap **karakteristik armada regional yang berbeda**
- WPP dengan distribusi bimodal mungkin memiliki dua populasi armada (nelayan lokal + kapal komersial)
- WPP dengan median radiance jauh di atas rata-rata nasional = area aktivitas kapal lebih besar/lebih terang

---

## D4 · Violin + Strip Chart per WPP — *Komposisi Kelas Armada per Wilayah*

### Mengapa Dibuat?
V7 menampilkan distribusi radiance sebagai statistik ringkas. D4 menambahkan **dua lapisan informasi**:
1. **Strip chart**: titik-titik individual berwarna kelas armada — terlihat di mana persis kapal "industri" (merah) berada dalam distribusi WPP tersebut
2. **Stacked bar**: proporsi eksplisit (%) tiap kelas armada per WPP — memudahkan perbandingan komposisi

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `wpp` | `radiance_sample_log.csv` | WPP asal deteksi |
| `radiance_log1p` | `radiance_sample_log.csv` | Radiance log-transformed |
| `rad_class` | `radiance_sample_log.csv` | Kelas armada (tradisional/menengah/industri/anomali) |

### Proses yang Dilalui
1. Pilih **top 8 WPP** (lebih sedikit dari V7 agar strip tidak terlalu padat)
2. Subsample violin: **8.000 baris per WPP**, strip: **2.000 baris per WPP**
3. **Panel atas**: Violin biru transparan + `seaborn.stripplot` dengan warna kelas armada + jitter
4. **Panel bawah**: Hitung proporsi kelas per WPP → stacked bar chart dengan anotasi %
5. Tambah garis horizontal: median nasional sebagai referensi

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Strip Plot** | Scatter plot di mana X = nilai data, Y = kategori; jitter ditambahkan agar titik tidak tumpang tindih |
| **Jitter** | Gangguan acak kecil pada posisi titik agar terlihat saat banyak titik memiliki nilai serupa |
| **Stacked Bar Chart** | Bar yang tersusun bertumpuk — tinggi total = 100%, tiap segmen = proporsi satu kategori |
| **Subsampling** | Mengambil N baris secara acak dari populasi lebih besar; diperlukan agar strip plot tidak overplotted (jutaan titik di satu lokasi) |

### Insight yang Diperoleh
- Visualisasi paling informatif untuk kebijakan: **"WPP mana yang perlu perhatian khusus terkait kapal industri?"**
- WPP dengan proporsi "industri" (merah) tinggi = area yang perlu pengawasan lebih ketat
- Distribusi strip menunjukkan apakah kelas industri tersebar merata atau terkonsentrasi di nilai radiance tertentu

---

## D6 · Log-Transformed Distribution — *Mengapa Log-Transform Wajib*

### Mengapa Dibuat?
Ini adalah **visualisasi metodologis paling penting di Fase 2**. Setiap kali menggunakan log-transform dalam penelitian, reviewer jurnal Q1/Q2 akan bertanya: *"Mengapa Anda menggunakan log-transform? Apakah memang diperlukan?"*

D6 menjawab pertanyaan itu secara kuantitatif — membandingkan distribusi raw vs log-transformed dengan QQ plot dan nilai korelasi Pearson (r) terhadap distribusi normal.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `radiance_raw` | `radiance_sample_log.csv` | Nilai radiance asli (nW/cm²/sr) |
| `radiance_log1p` | `radiance_sample_log.csv` | log(1 + radiance) — sudah dihitung di Fase 0 |
| `rad_class` | `radiance_sample_log.csv` | Kelas armada — untuk KDE per kelas |

### Proses yang Dilalui
1. Baca 300.000 sampel, subsample 100.000 untuk plotting
2. **Baris 1 — Distribusi RAW:**
   - Panel (a): Histogram linear (dipotong di 200 agar terlihat)
   - Panel (b): Histogram log-X scale (lebih terlihat tapi masih skewed)
   - Panel (c): QQ plot vs distribusi normal → hitung Pearson r
3. **Baris 2 — Distribusi LOG-TRANSFORMED:**
   - Panel (d): Histogram log1p (jauh lebih simetris)
   - Panel (e): KDE overlay per kelas armada (3 kelas berbeda)
   - Panel (f): QQ plot log1p vs normal → hitung Pearson r
4. **Bandingkan r** dari panel (c) dan (f) → perbedaan dramatis membuktikan perlunya log-transform

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **log1p(x) = log(1+x)** | Transformasi logaritmik yang aman untuk x=0 (log(0) = -∞, tapi log(1+0)=0). Mempertahankan urutan relatif data sambil "meratakan" distribusi yang sangat miring |
| **Right-skewed (positively skewed)** | Distribusi dengan ekor panjang ke kanan — kebanyakan nilai kecil, tapi ada nilai ekstrem sangat besar (mean > median) |
| **QQ Plot (Quantile-Quantile Plot)** | Scatter plot kuantil data vs kuantil teoritis distribusi normal. Jika data normal → titik membentuk garis lurus. Semakin menyimpang dari garis = semakin tidak normal |
| **Pearson r (dalam QQ Plot)** | Korelasi antara kuantil sampel dan kuantil teoritis normal. r ≈ 1.0 = sangat mendekati normal; r < 0.7 = menyimpang signifikan |
| **Log-Normal Distribution** | Distribusi di mana log(x) berdistribusi normal. Sangat umum untuk data yang selalu positif dan sangat skewed (harga, pendapatan, radiance kapal) |
| **KDE (Kernel Density Estimate)** | Estimasi non-parametrik dari distribusi probabilitas — versi "halus" dari histogram |

### Insight yang Diperoleh
- **Raw radiance**: QQ plot sangat menyimpang → r ≈ 0.3–0.5 → **TIDAK normal**
- **Log-transformed**: QQ plot hampir lurus → r ≈ 0.95–0.99 → **Mendekati log-normal**
- Perbedaan r ini adalah **bukti kuantitatif** untuk menulis di Methods paper: *"Radiance values were log-transformed (log(1+x)) prior to analysis, as raw values exhibited extreme right-skewness (Pearson r = X.XX vs normal) while transformed values approached log-normality (r = X.XX)"*
- KDE per kelas menunjukkan bahwa **setiap kelas armada memiliki distribusi log-normal sendiri** — mendukung segmentasi kelas yang kita gunakan

---

## Ringkasan File Output Fase 2

| Kode | File PNG | Dibuat Dari | Durasi |
|------|----------|-------------|--------|
| V2 | `V2_pareto_wpp.png` | `yearly_aggregated.csv` | ~0s |
| D1 | `D1_radiance_histogram.png` | `radiance_sample_log.csv` | ~2s |
| V7 | `V7_violin_box_wpp.png` | `radiance_sample_log.csv` | ~3s |
| D4 | `D4_violin_strip_wpp.png` | `radiance_sample_log.csv` | ~5s |
| D6 | `D6_log_transform_comparison.png` | `radiance_sample_log.csv` | ~7s |

> **Total Fase 2: 17 detik** · 300.000 sampel radiance · Top 12 WPP · 5 output PNG
>
> Filter universal: EEZ = "Indonesian Exclusive Economic Zone" · Land_Mask ≠ 1 · 2026 = parsial (dikecualikan dari V2)
>
> *Threshold radiance empiris: tradisional <10 / menengah 10–100 / industri 100–1000 / anomali >1000 nW/cm²/sr*
