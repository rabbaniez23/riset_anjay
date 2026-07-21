# Fase 7 — Deskripsi Lengkap Visualisasi Spatio-Temporal
## VBD Indonesia 2012–2026 · VIIRS Boat Detection · Flagship Figures

> Fase 7 adalah puncak dari seluruh rangkaian analisis. Semua visualisasi pada fase ini dirancang sebagai **"Flagship Figures"** — yakni gambar-gambar yang paling siap untuk menjadi **Main Figure** dalam publikasi jurnal internasional.
>
> **Strategi teknis:** Data temporal (bulanan/tahunan per WPP) dari `monthly_aggregated.csv` dan `yearly_aggregated.csv` ditumpuk di atas *backdrop* peta titik dari `pixel_grid_L2.csv`. Hasilnya adalah peta spasial yang sepenuhnya data-driven tanpa bergantung pada shapefile eksternal.
>
> **Konvensi Musim Indonesia (BMKG):**
> | Kode | Musim | Bulan | Karakteristik |
> |------|-------|-------|---------------|
> | DJF | Musim Barat | Des–Feb | Angin Muson Barat, Curah hujan tinggi di barat |
> | MAM | Pancaroba I | Mar–Mei | Transisi, angin lemah |
> | JJA | Musim Timur | Jun–Agu | Angin Muson Timur, perairan timur lebih produktif |
> | SON | Pancaroba II | Sep–Nov | Transisi kedua, pra-musim barat |

---

## C2 · 4 Musim Panel Map — *Flagship: Peta Perbandingan Musiman*

### Mengapa Dibuat?
Ini adalah visualisasi yang **paling sering diminta oleh reviewer jurnal perikanan**. Menunjukkan bagaimana distribusi spasial armada tangkap berpindah mengikuti siklus musim merupakan bukti langsung bahwa kapal nelayan berperilaku responsif terhadap dinamika oseanografi (suhu muka laut, upwelling, migrasi ikan).

### Kolom yang Digunakan
| Kolom | File | Keterangan |
|-------|------|------------|
| `month` | `monthly_aggregated.csv` | Bulan (1–12), untuk grouping ke 4 musim |
| `detection_count` | `monthly_aggregated.csv` | Total deteksi kapal per WPP per bulan |
| `wpp` | `monthly_aggregated.csv` | Kode wilayah WPP (filter 11 WPP NRI) |
| `lat_grid`, `lon_grid` | `pixel_grid_L2.csv` | Backdrop peta laut |

### Proses yang Dilalui
1. Kelompokkan bulan menjadi 4 musim: DJF [12,1,2], MAM [3,4,5], JJA [6,7,8], SON [9,10,11].
2. Untuk setiap musim, jumlahkan total deteksi seluruh tahun per WPP.
3. Tampilkan sebagai 4 panel 2×2. Tiap panel = satu musim.
4. Setiap WPP direpresentasikan sebagai bubble pada koordinat sentral WPP: **ukuran bubble ∝ total deteksi**, **warna ∝ intensitas** (colormap YlOrRd).

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Bubble Map** | Peta di mana besarnya lingkaran merepresentasikan nilai numerik suatu area. Lebih informatif dari peta choropleth karena area WPP tidak sebanding ukurannya. |
| **Musim Barat (DJF)** | Periode di mana angin Barat mendominasi. Perairan Samudera Hindia (WPP 571) dan Laut Natuna (WPP 572/711) sering bergolak — nelayan cenderung ke perairan pedalaman yang lebih tenang seperti Laut Jawa. |
| **Musim Timur (JJA)** | Angin Timur mendominasi. Upwelling kuat di Laut Arafura dan Laut Banda → produktivitas ikan tinggi → aktivitas VBD melonjak di WPP 718, 713, dan 714. |

### Insight yang Diperoleh
- **Dominasi WPP 712 (Laut Jawa) berlangsung di semua 4 musim** — pola ini tidak bergeser secara absolut. Ini adalah fakta empiris yang penting: meski musim berganti, Laut Jawa tetap episentrum perikanan Indonesia karena jumlah armadanya jauh melebihi WPP manapun.
- Pergeseran musiman bersifat **relatif, bukan absolut**. Untuk melihatnya, diperlukan analisis normalisasi (mis. % kontribusi tiap WPP per musim) yang akan dilakukan di fase analisis lanjutan.
- Panel Pancaroba (MAM & SON) memperlihatkan distribusi yang paling merata secara visual — bubble WPP timur (713, 718) relatif lebih besar proporsinya dibandingkan di panel DJF.

---

## C1 · 12 Panel Monthly KDE — *Flagship: Atlas Kalender Bulanan*

### Mengapa Dibuat?
Panel 4 musim memperlihatkan gambaran besar, namun dinamika perikanan sering beroperasi pada resolusi **bulanan**. Bulan Juni berbeda dari Juli berbeda dari Agustus — meski ketiganya adalah "Musim Timur". C1 adalah **atlas kalender perikanan** pertama berbasis VIIRS untuk perairan Indonesia yang menunjukkan pola bulanan selama 14 tahun.

### Proses yang Dilalui
1. Hitung rata-rata `detection_count` per WPP untuk setiap bulan (rata-rata lintas 2012–2025).
2. Tampilkan 12 panel (3 baris × 4 kolom = Jan–Des).
3. Setiap panel menggunakan **colormap "plasma"** yang sama (skala warna disamakan) sehingga pembaca dapat membandingkan intensitas antar bulan secara langsung.
4. Satu colorbar bersama di kanan gambar menghilangkan redundansi skala.

### Insight yang Diperoleh
- Puncak aktivitas nasional biasanya terkonsentrasi di **bulan-bulan tertentu** (bukan tersebar merata) — konfirmasi kuantitatif bahwa perikanan Indonesia bersifat musiman.
- Bulan-bulan dengan bubble sangat terang di WPP 712 (Laut Jawa) konsisten terjadi selama musim kemarau, sedangkan aktivitas di WPP 718 (Arafura) melonjak di pertengahan tahun.

---

## C3 · Yearly Evolution Panel — *Flagship: 14 Tahun Perubahan*

### Mengapa Dibuat?
Ini adalah **time-lapse** distribusi perikanan Indonesia dari 2012 hingga 2025. Dengan membandingkan 14 panel secara visual, pembaca bisa segera melihat apakah ada WPP yang mengalami pertumbuhan, stagnasi, atau penurunan — tanpa perlu membaca tabel angka.

### Proses yang Dilalui
1. Ambil data tahunan (`yearly_aggregated.csv`) untuk setiap tahun yang memiliki data penuh (`is_partial_year == 0`).
2. Buat layout 2 baris × 7 kolom = 14 panel.
3. Tiap panel menampilkan kondisi aktivitas di 11 WPP untuk satu tahun tertentu.
4. **Skala warna disamakan** (vmax = persentil ke-90 seluruh data) agar perbandingan antar tahun valid.

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Partial Year** | Tahun yang data bulannya tidak lengkap (mis. 2012 hanya Apr–Des). Dieksklusikan agar tidak meremehkan total deteksi. |
| **vmax Persentil 90** | Batas atas skala warna diset ke persentil ke-90 (bukan nilai maksimum). Ini mencegah outlier satu tahun yang sangat tinggi "memutihkan" semua panel lain. |

### Insight yang Diperoleh
- WPP 712 (Laut Jawa) konsisten dominan di seluruh 14 tahun → perairan yang sangat matang eksploitasinya (*mature fishery*).
- Beberapa WPP menunjukkan tren naik yang jelas di panel akhir (2021–2025) → kawasan yang baru terbuka (*frontier fisheries*). Ini dikonfirmasi secara kuantitatif oleh analisis C7 (+167% hingga +194% di WPP timur).
- **Panel 2020 (COVID):** Tidak tampak penurunan yang signifikan secara visual — ini merupakan temuan penting bahwa **armada tangkap ikan tidak terdampak signifikan oleh lockdown**. Sektor perikanan beroperasi sebagai industri esensial selama pandemi.
- **Keterbatasan keterbacaan:** Bubble WPP 712 sangat besar dan menutupi WPP lain di sekitar Laut Jawa (WPP 573, 711). Untuk analisis evolusi WPP kecil, disarankan membuat C3 versi "tanpa WPP 712" sebagai panel komplementer agar tren WPP minority lebih terlihat.

---

## C6 · Persistent Hotspot Map — *Flagship: Inti Daerah Tangkap Abadi*

### Mengapa Dibuat?
Di antara seluruh jutaan titik deteksi, hanya sebagian kecil yang menjadi **"ground truth" daerah tangkap sesungguhnya** — yaitu koordinat yang digunakan nelayan secara terus-menerus selama bertahun-tahun. Peta C6 mengekstrak inti tersebut menggunakan sistem threshold L4–L6 yang sudah dibangun di Fase 0.

### Kolom yang Digunakan
| Kolom | File | Keterangan |
|-------|------|------------|
| `is_L4` | `pixel_grid_L2.csv` | Biner (1/0): area masuk Top 25% persistensi |
| `is_L5` | `pixel_grid_L2.csv` | Biner: area masuk Top 5% persistensi |
| `is_L6` | `pixel_grid_L2.csv` | Biner: area masuk Top 0.5% persistensi |

### Proses yang Dilalui
Layer ditumpuk dari yang paling luas ke paling sempit:
1. **L2/L3 (biru muda):** Backdrop — semua area yang terdeteksi minimal 22 hari.
2. **L4 Kuning:** Area High Persistent (Top 25%) — belum terisi L5.
3. **L5 Oranye:** Area Very High Persistent (Top 5%) — belum terisi L6.
4. **L6 Merah Terang:** Area Extreme Persistent (Top 0.5%) — paling sedikit tapi paling kritis.

### Insight yang Diperoleh
- Titik L6 (Merah) membentuk "urat-urat" daerah tangkap yang mengikuti pola batimetri (kedalaman laut) dan alur migrasi ikan.
- Ini adalah **dasar ilmiah paling kuat** untuk penentuan Kawasan Suaka Perikanan (ZPP/KPA) — lokasi yang harus dilindungi jika stok ikan ingin pulih.

---

## C7 · Hotspot Emergence Map — *Mengidentifikasi Frontier Baru*

### Mengapa Dibuat?
Penelitian perikanan membutuhkan deteksi dini: **WPP mana yang sedang "membuka diri" sebagai daerah tangkap baru (Emerging), dan WPP mana yang mulai ditinggalkan (Declining)?** C7 adalah instrumen kebijakan — menunjukkan ke mana armada bergeser dalam dekade terakhir.

### Proses yang Dilalui
1. Hitung rata-rata tahunan deteksi per WPP untuk dua periode:
   - **Periode Awal:** 2012–2016
   - **Periode Akhir:** 2020–2025
2. Hitung persentase perubahan: $\Delta\% = \frac{D_{akhir} - D_{awal}}{D_{awal}} \times 100$
3. Klasifikasikan setiap WPP:
   - $\Delta\% > +15\%$ → **Emerging** (merah) — pertumbuhan signifikan
   - $\Delta\% < -15\%$ → **Declining** (biru) — penurunan signifikan
   - Lainnya → **Stable** (abu-abu)
4. Panel kiri: Peta bubble berwarna berdasarkan kategori + anotasi persentase.
5. Panel kanan: Bar chart horizontal yang mengurutkan WPP dari penurunan terbesar ke pertumbuhan terbesar.

### Insight yang Diperoleh
- WPP yang Emerging (merah) adalah kandidat zona pengawasan intensif — eksploitasi yang cepat naik tanpa regulasi ketat berpotensi menjadi overfishing dalam 5–10 tahun ke depan.
- WPP yang Declining (biru) perlu investigasi lebih lanjut: apakah turun karena stok ikan yang berkurang, atau karena nelayan beralih ke WPP lain yang lebih menguntungkan?

---

## F1 · Active Fishing Month Map — *Kalender Musim Puncak per WPP*

### Mengapa Dibuat?
Setiap WPP memiliki *ritme musim* tersendiri yang dipengaruhi oleh arus, upwelling lokal, dan migrasi spesies ikan target. **F1 adalah peta kalender** — menunjukkan dalam satu pandang bulan mana yang paling aktif untuk setiap WPP. Ini sangat berguna untuk perencanaan operasional armada, musim tutup tangkap, atau pengelolaan kuota.

### Proses yang Dilalui
1. Hitung rata-rata deteksi per WPP per bulan (agregat 2012–2025).
2. Identifikasi **bulan puncak** (argmax) dan **bulan minimum** (argmin) untuk setiap WPP.
3. Panel kiri: Peta bulan puncak — warna bubble berdasarkan bulan menggunakan **colormap sirkular (HSV)** agar bulan Desember (bulan 12) secara visual berdekatan dengan Januari (bulan 1).
4. Panel kanan: Peta bulan terendah — memperlihatkan kapan tiap WPP paling "sepi".
5. Ukuran bubble ∝ total deteksi pada bulan puncak tersebut.

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Circular Colormap (HSV)** | Colormap yang titik awal dan akhirnya menyambung — sangat cocok untuk data siklus seperti bulan dan jam. Menghindari diskontinuitas visual antara Desember dan Januari. |
| **Peak Month** | Bulan dengan rata-rata deteksi tertinggi untuk WPP tertentu. Ini merepresentasikan puncak musim tangkap historis. |
| **Trough Month** | Bulan dengan rata-rata deteksi terendah — merepresentasikan musim paceklik atau musim tutup tangkap de facto. |

### Insight yang Diperoleh (Berbasis Data Aktual)
- **WPP barat (571, 711) puncak di Mar–Apr (Pancaroba I)**, bukan di musim kemarau seperti yang lazim diasumsikan. Ini menunjukkan bahwa nelayan barat berpuncak saat angin mulai menguat dari selatan — kemungkinan berhubungan dengan pola migrasi ikan pelagis kecil di Selat Malaka dan Laut Cina Selatan.
- **WPP timur (713, 714, 718) puncak di Sep–Okt (Pancaroba II)**, bukan tepat saat Musim Timur (Jun–Agu). Ini mengindikasikan adanya **delay biologis-operasional**: produktivitas oseanografi memuncak saat JJA, namun stok ikan yang siap ditangkap dan armada yang sampai di WPP terpencil baru berpuncak beberapa bulan kemudian.
- **WPP 712 (Laut Jawa) puncak di September, paceklik di Januari** — konsisten dengan gelombang tinggi Musim Barat yang membatasi operasi nelayan kecil di bulan Jan–Feb.
- Kalender trough menunjukkan **Januari sebagai bulan terendah di mayoritas WPP** — implikasi kebijakan: program bantuan nelayan (BPNT, subsidi solar) paling dibutuhkan di bulan Januari.
- Penggabungan peta peak + trough menciptakan **kalender musim pancing nasional berbasis 14 tahun data empiris** yang lebih akurat daripada asumsi teoritis meteorologis.

---