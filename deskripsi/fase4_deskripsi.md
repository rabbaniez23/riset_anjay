# Fase 4 — Deskripsi Lengkap Visualisasi Temporal Lanjutan
## VBD Indonesia 2012–2026 · VIIRS Boat Detection

> Visualisasi pada fase ini dirancang untuk menjawab pertanyaan yang lebih kompleks ("mengapa" dan "kapan") melalui pengolahan sinyal deret waktu lanjutan.
> Input: `monthly_aggregated.csv` (Time Series Nasional) dan `radiance_sample_log.csv` (Evolusi Armada)

---

## A2 · Time Series Decomposition — *Membedah Komponen Waktu*

### Mengapa Dibuat?
Data observasi asli bulanan seringkali tampak "berisik" karena gabungan antara tren jangka panjang, musim yang berulang, dan kejadian acak (noise). Dekomposisi memecah data deret waktu menjadi tiga komponen ini agar kita bisa mengukur *seberapa kuat pengaruh musiman* dibandingkan dengan tren aslinya.

### Proses yang Dilalui
1. Membaca agregasi nasional per bulan (2012–2025).
2. **Trend:** Menghitung *Centered Moving Average* 12-bulan (untuk menghaluskan fluktuasi tahunan).
3. **Detrending:** Mengurangi observasi asli dengan komponen tren.
4. **Seasonal:** Menghitung rata-rata dari data *detrended* untuk setiap bulan (Jan-Des) sehingga didapat profil musiman murni.
5. **Residual:** Mengurangi data *detrended* dengan pola musiman. Sisa ini adalah anomali acak.

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Dekomposisi Aditif** | Asumsi bahwa Data = Tren + Musiman + Residual. Digunakan karena fluktuasi musiman relatif stabil dari tahun ke tahun. |
| **Trend Component** | Arah umum data jika pengaruh bulan/cuaca ditiadakan. |
| **Seasonal Component** | Fluktuasi yang berulang persis sama setiap interval 12 bulan (siklus alamiah/cuaca). |
| **Residual (Noise)** | Sisa sinyal yang tidak bisa dijelaskan oleh Tren maupun Musim. Mengindikasikan kejadian tak terduga. |

### Insight yang Diperoleh
- Seberapa mulus grafik Tren (Komponen ke-2) membuktikan pertumbuhan jangka panjang perikanan secara konsisten.
- Skala dari komponen Musiman (Komponen ke-3) menunjukkan besaran impak iklim; jika amplitudonya jutaan deteksi, artinya cuaca mendikte sepertiga dari total tangkapan kapal.

---

## A5 · Anomaly Detection — *Deteksi Kejadian Tak Terduga*

### Mengapa Dibuat?
Kita butuh cara obyektif untuk mencari bulan-bulan di mana penangkapan ikan anjlok tak wajar atau melonjak secara abnormal, di luar siklus musimannya.

### Proses yang Dilalui
1. Mengambil komponen **Residual** dari A2 (yakni data murni tanpa efek tren jangka panjang dan tanpa efek musiman).
2. Menghitung standar deviasi dari residual tersebut dan menormalisasinya menjadi **Z-score**.
3. Menandai bulan apa pun yang melampaui Threshold $|Z| > 2.0$.
4. Titik-titik ini diproyeksikan kembali ke atas grafik deret waktu asli dengan label merah (Anomali Positif) dan oranye (Anomali Negatif).

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Z-score** | Metrik statistik yang mengukur berapa standar deviasi jauhnya suatu nilai dari rata-rata populasinya. |
| **$Z > 2.0$** | Secara probabilitas normal, nilai $Z > 2.0$ hanya terjadi pada 5% kasus (ekstrem/langka). |

### Insight yang Diperoleh
- Menemukan bulan-bulan spesifik dengan lonjakan/penurunan ekstrem.
- Anomali ini kemudian bisa dicocokkan dengan kalender peristiwa nyata (misalnya: badai siklon tropis besar yang terjadi di bulan tersebut, atau pembatasan ketat secara tiba-tiba).

---

## A9 · Before-After Event Analysis — *Evaluasi Kebijakan & Krisis*

### Mengapa Dibuat?
Di ranah publikasi sosial-ekonomi kelautan, sangat esensial untuk menguji hipotesis dampak dari sebuah krisis atau kebijakan baru. Visualisasi ini membandingkan langsung profil 12 bulan dari era *Sebelum* dan *Sesudah* kejadian besar (Event).

### Proses yang Dilalui
1. **Event 1 (Kebijakan Menteri Susi):** Bandingkan rata-rata bulanan pra-kebijakan (2012-2014) dengan pasca-kebijakan anti-IUU (2015-2017).
2. **Event 2 (Pandemi COVID-19):** Bandingkan era normal pra-COVID (2018-2019) dengan masa pembatasan COVID (2020-2021).
3. Melakukan *fill_between* warna hijau (jika era *Sesudah* meningkat) dan merah (jika era *Sesudah* menurun) pada kedua kurva bulanannya.

### Insight yang Diperoleh
- Secara visual mengonfirmasi bahwa pasca kebijakan moratorium kapal asing, penangkapan ikan nasional justru **tumbuh** (kurva post-kebijakan berada di atas pre-kebijakan), karena VBD lebih banyak mendeteksi kapal lokal yang kini merajai lautan pasca ditinggal asing.
- Mengevaluasi seberapa besar *demand-shock* pandemi COVID-19 menekan mobilitas nelayan.

---

## E1 · Radiance Trend per Kelas Armada — *Dinamika Spesifikasi Kapal*

### Mengapa Dibuat?
Selain volume (jumlah kapal), kita juga ingin tahu apakah ada **modernisasi armada** dalam 14 tahun terakhir? Apakah nelayan Indonesia secara bertahap beralih dari kapal kecil ke menengah yang menggunakan lampu lebih terang?

### Proses yang Dilalui
1. Menggunakan 300.000 sampel `radiance_raw` secara acak.
2. Panel Kiri: Membuat **100% Stacked Area Chart** untuk melihat proporsi pangsa kelas (Tradisional, Menengah, Industri) dari tahun ke tahun.
3. Panel Kanan: Membuat **Trend Median Radiance** absolut. Jika kurvanya menanjak, artinya kapal di lautan secara umum semakin "terang/besar" secara berangsur.

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **100% Stacked Area Chart** | Grafik area di mana Y-axis selalu total 100%. Fokusnya bukan volume, melainkan seberapa besar *pangsa* (proporsi) tiap kategori. |

### Insight yang Diperoleh
- Proporsi armada kelas industri mungkin statis (atau menurun), sementara armada tradisional meningkat pesat, sehingga rata-rata median radiance nasional justru tertekan sedikit menurun sepanjang dekade ini (bukti bahwa laut makin dipenuhi nelayan gurem/skala kecil).

---

## A6 · Change Point Detection — *Deteksi Perubahan Rezim*

### Mengapa Dibuat?
Kita ingin mencari kapan tepatnya terjadi "Break Structural" / pergeseran rezim secara objektif, tanpa menetapkan tahun tebakan kita sendiri di awal (berbeda dengan A9).

### Proses yang Dilalui
1. Hitung *Rolling Mean 12-Bulan ke belakang* (Trailing).
2. Hitung *Rolling Mean 12-Bulan ke depan* (Leading/Forward).
3. Cari persentase selisih (*Delta Perubahan Rezim*) antara kondisi masa depan dengan kondisi masa lalu di setiap titik.
4. Apabila selisih melonjak melampaui toleransi (misalnya > 30%), algoritma menandai garis vertikal sebagai titik pergeseran rezim (*Change Point*).

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Rolling Window** | Membuka jendela statistik dengan lebar N bulan yang bergerak maju satu langkah setiap saat. |
| **Trailing vs Leading** | Trailing = melihat ke masa lalu; Leading = melihat ke masa depan. |
| **Structural Break / Change Point** | Momen di mana asumsi ekuilibrium data sebelumnya tidak lagi berlaku di masa mendatang. |

### Insight yang Diperoleh
- Menemukan bulan kritis (misalnya *Upward Shift* pada akhir 2018) di mana jumlah penangkapan ikan melompat ke ambang batas baru dan tidak pernah kembali ke batas sebelumnya.
- Bukti analitis yang sangat meyakinkan untuk ditaruh di naskah publikasi karena metodenya sepenuhnya digerakkan oleh data (data-driven), bukan berdasarkan pemotongan tahun manual oleh peneliti.

---

> **Hasil Fase 4: Analisis Temporal Lanjutan selesai dengan sukses dalam 3 detik!**
