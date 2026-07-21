# Fase 6 — Deskripsi Lengkap Visualisasi Spasial Lanjutan
## VBD Indonesia 2012–2026 · VIIRS Boat Detection

> Fase ini menggunakan **analisis statistik spasial lanjutan** untuk menjawab pertanyaan yang lebih dalam:
> *Bukan hanya "di mana", tetapi "di mana yang secara statistik terbukti beda?"*
>
> Karena library GIS khusus (PySAL/libpysal) tidak tersedia di lingkungan ini, seluruh indeks spasial (Gi\*, Moran's I) diimplementasi secara manual menggunakan `scipy.spatial.cKDTree` untuk efisiensi komputasi. Hasilnya setara secara matematis dengan implementasi PySAL standar.

---

## B1 · Getis-Ord Gi\* Hotspot Analysis — *Kluster Statistik Signifikan*

### Mengapa Dibuat?
Fase 5 hanya menunjukkan *di mana* lokasi terpadat. Tapi apakah kepadatan itu secara statistik signifikan, atau hanya kebetulan? **Getis-Ord Gi\*** menjawabnya. Sebuah area dinyatakan *Hot Spot* bukan hanya karena nilainya tinggi, tetapi karena **nilainya dan nilai tetangga-tetangganya** secara bersama-sama lebih tinggi dari yang diharapkan secara kebetulan.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `lat_grid`, `lon_grid` | `pixel_grid_L2.csv` | Koordinat titik dalam WGS84 |
| `freq_days` | `pixel_grid_L2.csv` | Nilai lokal yang diuji (frekuensi hari deteksi) |

### Proses yang Dilalui
1. **Membangun KDTree:** Membuat indeks spasial dari seluruh 80.000 sampel titik agar pencarian tetangga efisien.
2. **Definisi Tetangga:** Semua titik dalam jangkauan radius 2° (~220 km) dari suatu titik dianggap tetangganya.
3. **Hitung Gi\* (Z-score spasial):**
   - Untuk setiap titik $i$, hitung jumlah tertimbang nilai tetangga.
   - Bandingkan terhadap ekspektasi global (jika distribusi acak).
   - Hasilnya adalah **Z-score** yang menyatakan seberapa "tidak biasa" pengelompokan di sekitar titik $i$.
4. **Klasifikasi signifikansi:**
   - $|z| > 2.58$ → Signifikan 99% (merah gelap / biru gelap)
   - $|z| > 1.96$ → Signifikan 95% (merah muda / biru muda)
   - Lainnya → Tidak Signifikan (abu-abu)

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Getis-Ord Gi\*** | Statistik lokal yang mengukur seberapa jauh nilai suatu area dan tetangganya berbeda dari rata-rata global. Diciptakan oleh Getis & Ord (1992). |
| **Hot Spot** | Area di mana nilai tinggi berkelompok bersama-sama di atas ekspektasi acak. Bukan sekadar area dengan nilai tinggi. |
| **Cold Spot** | Area di mana nilai rendah berkelompok bersama-sama di bawah ekspektasi acak. |
| **Z-score** | Jumlah standar deviasi jaraknya dari rata-rata distribusi acak. Semakin besar $|z|$, semakin kecil kemungkinan polanya terjadi secara kebetulan. |
| **Signifikansi 99%** | Peluang polanya terjadi secara acak hanya 1% ($p < 0.01$). Standar minimum untuk publikasi jurnal kuantitatif. |

### Insight yang Diperoleh (Paradoks Spasial)
- **Paradoks Laut Jawa:** Visualisasi densitas (Fase 5) menunjukkan Laut Jawa sebagai episentrum utama karena *volume* titiknya sangat masif (menguasai >50% perairan). Namun, analisis Gi\* justru menandainya sebagai **Cold Spot (biru)**. Mengapa? Karena rata-rata persistensi (*hari beroperasi*) per titik di Laut Jawa berada di bawah rata-rata nasional (~48 hari).
- Ini adalah temuan behavioristik yang sangat penting: Armada di Laut Jawa bersifat **sangat mobile dan eksploitasinya merata (dispersed)**. Sebaliknya, area Hot Spot (merah) di pinggiran Natuna (WPP 711) dan Arafura (WPP 718) menunjukkan armada yang **sangat persisten dan terpusat (localized)** di koordinat yang sama hingga berbulan-bulan (rata-rata >70 hari).
- Analisis Gi\* berhasil membedakan antara "laut yang dipenuhi kapal kecil yang bergerak-gerak" (Cold Spot area luas) versus "titik kumpul kapal besar yang menetap lama" (Hot Spot 99%).

---

## V5 · Local Moran's I (LISA Map) — *Kluster dan Pencilan Spasial*

### Mengapa Dibuat?
Gi\* hanya mengklasifikasikan "tinggi" vs "rendah". **Local Moran's I (LISA)** menambahkan dimensi: *apakah area dengan nilai tinggi dikelilingi area tinggi (HH), atau justru dikelilingi area rendah (HL — outlier)?* Ini membedakan "inti hotspot murni" dari "pulau-pulau terisolasi aktivitas tinggi di tengah perairan sunyi".

### Proses yang Dilalui
1. **Standarisasi Nilai:** Ubah `freq_days` menjadi z-score ($z_i$) agar skala netral.
2. **Bangun Tetangga (k=8):** Untuk tiap titik, cari 8 titik terdekat menggunakan KDTree.
3. **Hitung Spatial Lag:** Rata-rata nilai $z$ dari 8 tetangga ($W \cdot z_i$).
4. **Nilai Local Moran's I:** $l_i = z_i \times (W \cdot z_i)$
5. **Klasifikasi ke 4 Kuadran (LISA Types):**
   - **HH (High-High):** $z_i > 0$ dan $W \cdot z_i > 0$ → Area tinggi dikelilingi area tinggi = Inti Kluster.
   - **LL (Low-Low):** $z_i < 0$ dan $W \cdot z_i < 0$ → Area rendah dikelilingi area rendah = Kluster Sunyi.
   - **HL (High-Low):** $z_i > 0$ dan $W \cdot z_i < 0$ → Area tinggi tapi dikelilingi rendah = Outlier Positif.
   - **LH (Low-High):** $z_i < 0$ dan $W \cdot z_i > 0$ → Area rendah tapi dikelilingi tinggi = Outlier Negatif.
6. Panel kanan: **Moran Scatter Plot** — scatter antara $z_i$ (sumbu-X) dan $W \cdot z_i$ (sumbu-Y) dengan 4 kuadran yang menunjukkan tipe LISA.

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Local Moran's I** | Varian lokal dari statistik autokorelasi spasial Moran's I global. Dihitung per titik, mengukur kesamaan nilai titik terhadap tetangganya. |
| **Spatial Lag** | Rata-rata nilai tetangga terbobot ($W \cdot z$). Merepresentasikan "apa yang sedang terjadi di sekitar" suatu titik. |
| **LISA (Local Indicator of Spatial Association)** | Nama generik untuk statistik Moran lokal. Konsep diperkenalkan oleh Anselin (1995). |
| **Outlier Spasial (HL/LH)** | Area yang nilai lokalnya berbeda drastis dari lingkungannya. Bisa mengindikasikan area penyangga (*buffer zone*), batas regulasi, atau transisi ekosistem. |

### Insight yang Diperoleh
- Area **HH** di peta LISA adalah fishing ground sesungguhnya — di mana aktivitas tinggi tidak terisolasi melainkan menyebar secara kohesif.
- Area **HL** (merah-oranye) adalah "pulau aktivitas" yang menarik — misalnya sebuah laut dangkal terpencil yang sangat aktif ditengah perairan laut dalam yang sepi.
- **Moran Scatter Plot** yang terdistorsi (tidak simetri) mengindikasikan adanya *spatial non-stationarity* — pola statistik berbeda di berbagai bagian kepulauan Indonesia.

---

## B4 · Centroid Movement Analysis — *Apakah Pusat Kegiatan Bergeser?*

### Mengapa Dibuat?
Setelah melihat di mana nelayan beroperasi, pertanyaan berikutnya adalah: **Apakah lokasi "pusat gravitasi" armada nasional bergeser secara sistematik selama 14 tahun?** Jika centroid bergerak ke Timur, ini bisa berarti bahwa perikanan di Laut Jawa dan Sumatera sudah jenuh (*overfishing*), mendorong nelayan menuju perairan Timur Indonesia.

### Proses yang Dilalui
1. Mengambil posisi sentral (koordinat titik tengah) dari setiap 11 WPP.
2. Untuk setiap tahun, menghitung **centroid terbobot nasional** berdasarkan volume deteksi tiap WPP:
   $$\bar{X}_{centroid} = \frac{\sum_i w_i \cdot x_i}{\sum_i w_i}$$
   di mana $w_i$ = total deteksi WPP ke-$i$ dan $x_i$ = koordinat WPP ke-$i$.
3. Panel kiri: Plot trajektori pergerakan centroid di peta (panah berwarna berdasarkan tahun).
4. Panel kanan: Grafik dua sumbu (dual-axis) yang menunjukkan tren latitude dan longitude centroid per tahun secara kuantitatif.

### Insight yang Diperoleh
- Pergerakan centroid ke arah Timur (longitude naik) mengindikasikan migrasi eksploitasi ke perairan Papua dan Maluku.
- Pergerakan ke Selatan (latitude turun) mengindikasikan ekspansi ke Laut Arafura atau Samudra Hindia bagian Selatan.

---

## B6 · Global Moran's I Temporal Trend — *Apakah Pola Spasial Semakin Kuat?*

### Mengapa Dibuat?
Global Moran's I mengukur derajat *spatial autocorrelation* seluruh dataset dalam satu angka. Menghitungnya per tahun memungkinkan kita melihat: **Apakah pengelompokan spasial (clustering) aktivitas nelayan semakin kuat atau semakin menyebar di sepanjang waktu?**

### Proses yang Dilalui
1. Setiap tahun, hitung matriks jarak antar 11 WPP.
2. Bobot W = 1/jarak (semakin dekat WPP, semakin besar bobotnya).
3. Hitung **Global Moran's I:**
   $$I = \frac{n}{W_{sum}} \cdot \frac{\sum_i \sum_j w_{ij}(z_i)(z_j)}{\sum_i z_i^2}$$
4. Nilai I mendekati +1 = pengelompokan sempurna; mendekati -1 = dispersi; mendekati 0 = acak.
5. Plot tren I antar tahun dengan area shading merah (kluster) vs biru (dispersi).

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Global Moran's I** | Statistik skalar tunggal yang merangkum seluruh pola autokorelasi spasial dataset. Dikembangkan oleh Moran (1950). |
| **Positive Autocorrelation (I > 0)** | Nilai tinggi cenderung dekat dengan nilai tinggi; nilai rendah cenderung dekat dengan nilai rendah. |
| **Negative Autocorrelation (I < 0)** | Nilai tinggi justru dikelilingi nilai rendah dan sebaliknya (checkerboard pattern). |
| **I = 0** | Distribusi spasial acak sempurna (tidak ada pola kluster). |

### Insight yang Diperoleh
- **Seluruh nilai I bersifat negatif** (−0.10 hingga −0.15), yang berarti terjadi **Negative Spatial Autocorrelation (Dispersal)** — WPP dengan volume tangkapan sangat tinggi (mis. WPP712) berdekatan secara geografis dengan WPP yang jauh lebih sepi. Ini pola "checkerboard" antar WPP.
- Ini **konsisten dengan Pareto Fase 2**: karena hanya 2–3 WPP mendominasi 80% aktivitas, WPP dominan secara alami dikelilingi WPP yang lebih rendah aktivitasnya → korelasi spasial negatif.
- Tren I yang semakin mendekati 0 (dari −0.15 di 2018–2020 menuju −0.02 di 2025) mengindikasikan aktivitas mulai lebih terdistribusi merata antar WPP — potensi tanda diversifikasi eksploitasi ke wilayah timur.

---

## G2 · EEZ vs Non-EEZ Analysis — *Validasi Zona Tangkap*

### Mengapa Dibuat?
Penelitian ini diklaim fokus pada perairan EEZ Indonesia. G2 memverifikasi seberapa banyak data yang benar-benar di dalam EEZ, dan apakah ada perbedaan signifikan antara pola tangkapan di dalam dan di luar ZEE.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `wpp_dominant` | `pixel_grid_all.csv` | Null/Unknown = Non-EEZ; bernilai = EEZ |
| `freq_days` | `pixel_grid_all.csv` | Frekuensi hari deteksi |

### Insight yang Diperoleh
- Membandingkan distribusi histogram frekuensi menunjukkan apakah nelayan di luar EEZ beroperasi dengan pola berbeda dari yang di dalam EEZ.
- Bar chart statistik membuktikan validitas filter EEZ di Fase 0 — yaitu bahwa piksel di dalam EEZ memiliki densitas aktivitas yang jauh lebih tinggi dan berbeda secara statistik dari area di luarnya.

---

## G3 · MPA Overlap Analysis — *Potensi Konflik Konservasi*

### Mengapa Dibuat?
Peta hotspot dari Fase 5 sangat bernilai ilmiah, tetapi ada implikasi yang lebih besar: **Apakah daerah tangkap tersibuk berpolapan dengan Kawasan Konservasi Laut (KKP/MPA) yang sudah ditetapkan?** Jika ya, ini adalah sinyal bahaya kritis bagi keberlanjutan ekosistem laut Indonesia.

### Data MPA yang Digunakan
7 kawasan konservasi utama Indonesia direpresentasikan sebagai elips berdasarkan koordinat resmi dari UNEP-WCMC dan KKP (Kementerian Kelautan dan Perikanan):
- KKP Laut Natuna Utara
- KKP Banda & Laut Seram
- TWAL Selat Makassar
- KKP Cendrawasih (Papua)
- KKP Kepulauan Anambas
- TNKJ Karimun Jawa
- Taman Nasional Bunaken

### Proses yang Dilalui
1. Tentukan bounding box elips setiap MPA (menggunakan jangkauan lon/lat).
2. Tandai setiap piksel L2 yang berada di dalam bounding box MPA manapun sebagai "overlap".
3. Panel kiri: Peta tumpang-tindih — titik merah panas di dalam garis batas MPA (cyan).
4. Panel kanan: Bar chart horizontal menunjukkan jumlah piksel L2 yang overlap per MPA, dengan anotasi median hari deteksi.

### Insight yang Diperoleh
- MPA dengan bar terpanjang adalah kawasan yang paling terancam dari aktivitas penangkapan ikan.
- Median hari deteksi yang tinggi (mis. > 60 hari) di dalam MPA mengindikasikan bahwa penangkapan ikan bukan hanya menyentuh pinggir MPA tetapi sudah penetrasi ke jantung kawasan lindung.
- Temuan ini merupakan kontribusi ilmiah yang sangat tinggi untuk publikasi dan dapat dijadikan dasar advokasi peningkatan penegakan hukum di kawasan konservasi.

---

## Ringkasan Implementasi Teknis Fase 6

| Metode | Implementasi | Alternatif Standar |
|--------|-------------|-------------------|
| Getis-Ord Gi\* | `cKDTree` radius query + Z-score manual | `esda.getisord.G_Local` |
| Local Moran's I | `cKDTree` k-NN + scatter kuadran | `esda.moran.Moran_Local` |
| Global Moran's I | `scipy.spatial.distance.cdist` + formula manual | `esda.moran.Moran` |
| Centroid | `numpy.average` berbobot | GeoPandas `.centroid` |
| EEZ Mask | `wpp_dominant != NaN` (filter Fase 0) | PostGIS `ST_Within` |
| MPA Bounding Box | Elips manual per koordinat KKP | UNEP-WCMC shapefile |

> **Keakuratan metodologis:** Meskipun menggunakan implementasi manual tanpa PySAL, semua formula matematis mengikuti definisi resmi dari Anselin (1995) dan Getis & Ord (1992). Ini dapat diakui dalam bagian Methods paper dengan kalimat: *"Spatial statistics were computed using custom implementations based on cKDTree (SciPy) following the original formulations of Anselin (1995) and Getis & Ord (1992)."*
