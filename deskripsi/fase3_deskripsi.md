# Fase 3 — Deskripsi Lengkap Visualisasi Temporal Dasar
## VBD Indonesia 2012–2026 · VIIRS Boat Detection

> Semua visualisasi menggunakan file output agregasi temporal dari Fase 0.
> Input utama: `output/yearly_aggregated.csv` dan `output/monthly_aggregated.csv`
> Tahun 2026 dikecualikan dari analisis tren karena datanya parsial (hanya sampai Juli).

---

## V3 · Annual Trend Line (Nasional) — *Tren Aktivitas Keseluruhan*

### Mengapa Dibuat?
Visualisasi dasar pertama untuk setiap analisis time-series adalah melihat arah secara keseluruhan. Apakah penangkapan ikan di perairan Indonesia secara umum meningkat, menurun, atau stagnan dalam 14 tahun terakhir? V3 memberikan gambaran "big picture" secara makro.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `year` | `yearly_aggregated.csv` | Tahun observasi (2012–2025) |
| `detection_count` | `yearly_aggregated.csv` | Total baris deteksi kapal |
| `is_partial_year` | `yearly_aggregated.csv` | Filter untuk mengecualikan 2026 |

### Proses yang Dilalui
1. Baca `yearly_aggregated.csv`, filter `is_partial_year == 0`.
2. Group by `year`, jumlahkan (sum) total deteksi lintas semua WPP untuk mendapat agregat nasional.
3. Plot titik deteksi dan tarik garis regresi linier sederhana.
4. Hitung *slope* (laju pertumbuhan per tahun), p-value, dan $R^2$ sebagai indikator tren regresi.

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Trendline** | Garis lurus yang meminimalkan jarak ke semua titik data (Regresi Linier) untuk menunjukkan arah tren jangka panjang. |
| **Slope / Laju** | Angka yang menunjukkan rata-rata penambahan (atau pengurangan) jumlah deteksi per tahun secara linear. |
| **$R^2$ (R-squared)** | Koefisien determinasi. Menggambarkan seberapa baik varians data dijelaskan oleh garis tren (0 berarti acak/tidak cocok, 1 berarti cocok sempurna). |

### Insight yang Diperoleh
- Arah tren utama industri/aktivitas penangkapan ikan di Indonesia secara makro (meningkat/menurun).
- Memverifikasi apakah tren tahunan stabil atau terdapat fluktuasi besar (volatilitas) yang memicu anomali.

---

## A3 · Yearly Multi-Line per WPP — *Tren Temporal Spasial (Top WPP)*

### Mengapa Dibuat?
Tren nasional mungkin menyembunyikan dinamika lokal yang sangat berbeda. Apakah Laut Jawa terus bertumbuh sedangkan perairan Samudra Hindia stagnan? Visualisasi multi-garis ini memecah tren nasional menjadi tren komponen per WPP utama.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `year` | `yearly_aggregated.csv` | Tahun (2012–2025) |
| `wpp` | `yearly_aggregated.csv` | Nama Wilayah Pengelolaan Perikanan |
| `detection_count` | `yearly_aggregated.csv` | Total baris deteksi |

### Proses yang Dilalui
1. Identifikasi *Top 6 WPP* dengan jumlah deteksi tertinggi (meminjam insight Pareto V2).
2. Plot masing-masing WPP sebagai garis tersendiri pada satu grafik dari 2012 hingga 2025.
3. Beri warna berbeda (kategorikal) dan anotasi untuk membedakan.

### Insight yang Diperoleh
- WPP mana yang berkontribusi paling besar terhadap pertumbuhan nasional.
- Menemukan jika ada WPP yang tren aktivitasnya *berkebalikan* dengan tren WPP dominan lainnya.
- Membantu untuk menargetkan WPP yang memiliki anomali atau pertumbuhan ekstrem di bab studi kasus paper.

---

## A1 · Calendar Heatmap — *Intensitas Pola Waktu*

### Mengapa Dibuat?
Banyak fenomena alam (dan kebiasaan nelayan) memiliki siklus bulanan (musiman) yang berulang setiap tahun. Heatmap ini memadukan dimensi tahun vs bulan dalam matriks grid sederhana untuk mempermudah mata menangkap pola musiman atau bulan-bulan anomali.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `year` | `monthly_aggregated.csv` | Tahun |
| `month` | `monthly_aggregated.csv` | Bulan (1-12) |
| `detection_count` | `monthly_aggregated.csv` | Total baris deteksi dalam juta |

### Proses yang Dilalui
1. Pivot data menjadi format matriks: Baris = Tahun, Kolom = Bulan.
2. Render Heatmap menggunakan colormap *YlOrRd* (Kuning-Oranye-Merah) di mana warna merah melambangkan intensitas jumlah deteksi tertinggi.
3. Tahun 2026 yang hanya sampai Juli ditandai batas biru agar terlihat jelas.

### Insight yang Diperoleh
- Blok warna gelap vertikal membuktikan musim memancing tinggi/puncak di bulan yang sama tiap tahun.
- Blok warna pucat vertikal yang membentang tiap tahun menegaskan bahwa bias cuaca (cloud bias) atau off-season sangat konsisten dari 2012–2025.
- Adanya "hotspot" (satu sel paling merah) mengindikasikan bulan anomali di tahun tertentu.

---

## V4 · Monthly Ridge Plot (Violin) — *Distribusi Musiman Antar WPP*

### Mengapa Dibuat?
Heatmap nasional (A1) tidak menunjukkan bagaimana variasi per WPP dalam setiap bulan. V4 menggunakan *Violin Plot* (gabungan dari ridge/KDE) per bulan untuk menunjukkan bagaimana distribusi volume penangkapan antar 11 WPP bervariasi pada setiap bulan. 

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `month` | `monthly_aggregated.csv` | Sumbu-X |
| `detection_count` | `monthly_aggregated.csv` | Sumbu-Y (kemudian di log-transform) |

### Proses yang Dilalui
1. Filter bulan (1–12) dan keluarkan tahun 2026.
2. Terapkan `log1p(detection_count)` agar distribusi variasi WPP dapat divisualisasikan dengan baik dalam rentang yang logis.
3. Buat Violin Plot per bulan, menempatkan overlay titik *swarm* di atasnya (tiap titik mewakili 1 WPP pada tahun tersebut di bulan tersebut).
4. Tambahkan *shading* bayangan musim (Muson Barat dan Timur).

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Muson Barat** | Desember – Februari. Biasa ditandai curah hujan tinggi dan ombak besar di banyak lokasi Indonesia, membuat intensitas terdeteksi sering kali tertekan. |
| **Muson Timur** | Juni – Agustus. Musim kemarau, cuaca cerah di mayoritas laut selatan, sering dikaitkan dengan puncak tangkapan di perairan selatan. |

### Insight yang Diperoleh
- Sebaran violin yang "lebar" pada satu bulan menunjukkan varians/perbedaan aktivitas antar WPP yang tinggi.
- Mengkonfirmasi bahwa musim Muson Barat (Des-Feb) memiliki distribusi yang paling tertekan, sedangkan Muson Timur (Jun-Ags) memuncak, baik secara nilai tengah (median) maupun sebaran atas (maksimum).

---

## A7 · YoY Growth Rate — *Percepatan dan Kontraksi Nasional*

### Mengapa Dibuat?
V3 hanya menunjukkan jumlah absolut (volume). Tetapi *Year-over-Year (YoY) Growth* menghitung **kecepatan pertumbuhan/penurunan**. Hal ini sangat krusial di ranah kebijakan ekonomi perikanan: apakah aktivitas nelayan menurun tajam di tahun tertentu? Apakah pertumbuhan sudah melandai?

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `year` | `yearly_aggregated.csv` | Tahun berturut-turut |
| `detection_count` | `yearly_aggregated.csv` | Total nasional |

### Proses yang Dilalui
1. Sum volume deteksi tahunan nasional.
2. Hitung delta proporsi persentase: $ \frac{\text{Tahun Ini} - \text{Tahun Sebelumnya}}{\text{Tahun Sebelumnya}} \times 100\% $
3. Render ke *Bar Chart* dengan divergensi warna: Hijau untuk YoY positif, Merah untuk YoY negatif (penurunan).

### Insight yang Diperoleh
- Mengidentifikasi tahun-tahun "kejutan" (*shocks*), seperti saat COVID-19 (2020/2021) atau saat ada pemberlakuan regulasi moratorium kapal (2014-2015).
- Garis rata-rata (Average YoY) membantu menyimpulkan "normal baru" dari tingkat ekspansi penangkapan ikan nasional dalam periode tersebut.

---

## Ringkasan File Output Fase 3

| Kode | File PNG | Dibuat Dari | 
|------|----------|-------------|
| V3 | `V3_annual_trend_national.png` | `yearly_aggregated.csv` | 
| A3 | `A3_yearly_multiline_wpp.png` | `yearly_aggregated.csv` | 
| A1 | `A1_calendar_heatmap.png` | `monthly_aggregated.csv` | 
| V4 | `V4_monthly_ridge.png` | `monthly_aggregated.csv` | 
| A7 | `A7_yoy_growth.png` | `yearly_aggregated.csv` | 

> **Semua hasil Fase 3 dapat digabungkan dengan Fase 2 untuk bab Analisis Time-Series dan Karakteristik Sektoral pada publikasi ilmiah.**
