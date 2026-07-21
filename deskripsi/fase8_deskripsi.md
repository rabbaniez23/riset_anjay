# Fase 8 — Deskripsi Lengkap Visualisasi Brightness & Fishing Analysis
## VBD Indonesia 2012–2026 · VIIRS Boat Detection

> Fase 8 menjembatani dua dimensi analitis yang sebelumnya terpisah:
> 1. **Brightness (Radiance)** — memetakan *seberapa terang* cahaya kapal, yang berkorelasi dengan skala operasi (kecil vs industri).
> 2. **Fishing Pattern** — menganalisis *kapan*, *seberapa intens*, dan *seberapa stabil* aktivitas penangkapan ikan terjadi.
>
> Visualisasi fase ini banyak menggunakan **indeks komposit** dan **analisis fenologi**, yang merupakan teknik analisis tingkat lanjut dalam ekologi perikanan.

---

## E2 · Radiance Spatial Map — *Peta Dua-Panel Kecerahan Rata-rata dan Maksimum*

### Mengapa Dibuat?
Fase 5 (B8) sudah menampilkan peta radiance rata-rata. Namun E2 meningkatkan level analisis dengan menambahkan panel **radiance maksimum** — yang menjawab pertanyaan berbeda: *"Di mana pernah muncul kapal PALING terang (kemungkinan kapal industri asing) sepanjang 14 tahun?"*

### Kolom yang Digunakan
| Kolom | File | Keterangan |
|-------|------|------------|
| `lat_grid`, `lon_grid` | `pixel_grid_L2.csv` | Koordinat titik grid |
| `log_rad_mean` | `pixel_grid_L2.csv` | Log-transform dari rata-rata radiance di grid tersebut |
| `rad_max` | `pixel_grid_L2.csv` | Nilai radiance tertinggi yang pernah tercatat di grid tersebut. Ditransformasi menjadi `log(1 + rad_max)` saat plotting. |

### Proses yang Dilalui
1. **Panel Kiri (Rata-rata):** Plot seluruh titik L2 dengan warna berdasarkan `log_rad_mean`. Colormap: *inferno* (gelap→kuning). Latar belakang gelap (#0D2137) agar kontras.
2. **Panel Kanan (Maksimum):** Plot seluruh titik L2 dengan warna berdasarkan `log(1 + rad_max)`. Colormap: *hot* (hitam→merah→kuning→putih).

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **rad_max** | Nilai radiance puncak yang pernah tercatat di satu grid selama 14 tahun. Satu kali kemunculan kapal super-terang sudah cukup untuk membuat nilai ini sangat tinggi. |
| **Inferno vs Hot** | Dua colormap berbeda digunakan agar pembaca bisa membedakan panel dengan cepat. Inferno untuk data rata-rata (lebih smooth), Hot untuk data ekstrem (lebih dramatis). |

### Insight yang Diharapkan
- Peta rata-rata menunjukkan *pola operasional rutin* — di mana kapal beroperasi sehari-hari.
- Peta maksimum menunjukkan *kejadian anomali* — titik-titik terang yang tidak biasa. Perbedaan antara kedua panel mengungkapkan lokasi di mana sesekali muncul kapal industri besar di perairan yang biasanya hanya dihuni nelayan tradisional.

---

## E6 · Radiance Percentile per WPP — *Profil Statistik Kecerahan per Wilayah*

### Mengapa Dibuat?
Box plot memberikan gambaran distribusi yang cepat, namun sering menyembunyikan ekor distribusi (tail). Panel heatmap persentil melengkapinya dengan menyajikan **7 titik distribusi kunci** (P10 hingga P99) dalam satu tabel visual yang mudah dibandingkan antar WPP.

### Proses yang Dilalui
1. **Panel Kiri (Box Plot):** Menampilkan distribusi `log(1 + rad_mean)` per WPP. WPP diurutkan berdasarkan median radiance tertinggi → terendah. Outlier dihilangkan agar kotak terlihat jelas.
2. **Panel Kanan (Heatmap Persentil):** Menghitung 7 persentil (P10, P25, P50, P75, P90, P95, P99) dari `rad_mean` mentah (bukan log) untuk tiap WPP. Hasil ditampilkan sebagai heatmap beranotasi.

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **P99 (Persentil ke-99)** | Hanya 1% titik grid yang memiliki radiance di atas nilai ini. Mewakili kehadiran kapal sangat besar atau kumpulan kapal (*vessel cluster*). |
| **P50 (Median)** | Nilai tengah: 50% titik berada di atas, 50% di bawah. Lebih robust dari mean terhadap outlier. |
| **Box Plot tanpa outlier** | Outlier (titik di luar 1.5× IQR) dihilangkan secara visual agar kotak distribusi utama tidak terkompresi. Data outlier tetap ada di heatmap P99. |

### Insight yang Diperoleh (Berbasis Data Aktual)
- **WPP718 (Arafura) memiliki P99 tertinggi (95.2 nW) dan P50 tertinggi (42.5 nW)** — konfirmasi kuantitatif bahwa Arafura didominasi armada industri besar, konsisten dengan laporan IUU fishing di perairan ini.
- **WPP711 (Natuna) di urutan kedua (P99=89.0 nW)** — perairan perbatasan yang diketahui sering dimasuki kapal asing dari Vietnam dan Tiongkok.
- WPP dengan P99 >80 nW (WPP718, WPP711) perlu pengawasan intensif karena kehadiran kapal berradiance sangat tinggi mengindikasikan operasi skala industri.
- Perbandingan P50 antar WPP menunjukkan profil "tipikal" armada: WPP718 (P50=42.5) vs WPP573 (P50=2.7) — **15× lipat perbedaan** yang mencerminkan segregasi armada tradisional-industri secara geografis.

---

## F2 · Fishing Season Phenology — *Kalender Musim Tangkap dengan Gantt Chart*

### Mengapa Dibuat?
Visualisasi F1 (Fase 7) menunjukkan *bulan puncak* per WPP. Namun satu bulan tidak cukup untuk menggambarkan musim tangkap. **Fenologi (Phenology)** menambahkan tiga komponen kritis:
- **Onset:** Kapan musim tangkap dimulai?
- **Peak:** Kapan puncaknya?
- **Offset:** Kapan musim tangkap berakhir?
- **Durasi:** Berapa bulan musim tangkap berlangsung?

### Proses yang Dilalui
1. Hitung rata-rata `detection_count` per WPP per bulan (agregat lintas 2012–2025).
2. Normalisasi nilai tiap WPP ke skala 0–1 (0 = bulan terendah, 1 = bulan tertinggi untuk WPP tersebut).
3. Tentukan threshold 50% dari nilai puncak. Bulan-bulan yang nilainya ≥ 50% dari puncak dianggap sebagai *musim tangkap aktif*.
4. **Panel Atas:** Kurva profil bulanan (normalized) untuk setiap WPP.
5. **Panel Bawah:** **Gantt Chart** — bar horizontal per WPP yang menunjukkan durasi musim tangkap. Diamond merah (◆) menandai bulan puncak. Anotasi di sisi kanan menunjukkan durasi (dalam bulan).

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Fenologi (Phenology)** | Studi tentang waktu kejadian biologis/ekologis yang berulang secara siklis. Dalam konteks perikanan: kapan musim buka/tutup tangkap terjadi. |
| **Onset** | Bulan pertama dalam setahun di mana aktivitas penangkapan melebihi 50% dari puncak. |
| **Offset** | Bulan terakhir dalam setahun di mana aktivitas masih di atas 50% dari puncak. |
| **Threshold 50%** | Pilihan operasional: di bawah 50% dari aktivitas puncak dianggap "off-season". Nilai ini digunakan di berbagai studi fenologi laut (Platt et al., 2009). |
| **Gantt Chart** | Diagram bar horizontal yang biasa digunakan dalam manajemen proyek. Di sini dipakai untuk mevisualisasikan rentang waktu musim tangkap per wilayah. |

### Insight yang Diperoleh (Berbasis Data Aktual)
- **WPP dengan durasi musim paling panjang (9 bulan):** WPP711 (Natuna), WPP712 (Laut Jawa), WPP716 (Sulawesi) — hampir sepanjang tahun tanpa periode istirahat, berpotensi **eksploitasi berlebih** dengan recovery time minimal.
- **WPP dengan durasi paling pendek (3 bulan):** WPP571 (Samudera Hindia), WPP714 (Maluku) — sangat tergantung pada satu musim, **rentan terhadap variabilitas iklim** (El Niño/La Niña).
- **WPP718 (Arafura) hanya 4 bulan** (Sep–Des) meski merupakan daerah tangkap utama — musim sangat terkonsentrasi, cocok untuk kebijakan *closed season* di luar periode tersebut.
- Gantt chart ini menjadi **dasar ilmiah rekomendasi closed fishing season**: WPP dengan offset di bulan X sebaiknya ditutup mulai bulan X+1 untuk memberikan waktu recovery pada stok ikan.

---

## F4 · Fishing Intensity Index (FII) — *Indeks Komposit Beban Eksploitasi*

### Mengapa Dibuat?
Sampai saat ini, analisis hanya menggunakan `detection_count` (jumlah kapal) atau `rad_mean` (kecerahan) secara terpisah. Namun **beban eksploitasi sesungguhnya** adalah kombinasi keduanya: 10 kapal industri besar (radiance tinggi) memberikan tekanan ekologis yang jauh lebih besar dari 10 perahu tradisional (radiance rendah). FII menggabungkan kedua dimensi ini.

### Formula
$$FII = Detection\,Count \times Radiance\,Mean$$

Interpretasi:
- FII rendah = sedikit kapal DAN/ATAU kapal kecil
- FII tinggi = banyak kapal DAN/ATAU kapal besar
- Plotting menggunakan $\log_{10}(FII + 1)$ agar skala terbaca

### Proses yang Dilalui
1. Hitung FII per WPP per tahun dari `yearly_aggregated.csv`.
2. **Panel Kiri (Heatmap):** Matriks WPP × Tahun dengan warna berdasarkan `log₁₀(FII)`. Sel paling gelap = beban eksploitasi paling rendah; paling terang = paling berat.
3. **Panel Kanan (Line Chart):** Tren FII nasional (garis hitam tebal) + tren 3 WPP dengan FII tertinggi (garis putus-putus berwarna).

### Insight yang Diperoleh (Berbasis Data Aktual)
- **Heatmap:** WPP712 (Laut Jawa) konsisten berwarna paling gelap (FII tertinggi) di seluruh 14 tahun — wilayah dengan **tekanan ekologis kumulatif terberat** di Indonesia.
- **Tren nasional menunjukkan puncak FII di 2017–2018**, diikuti **penurunan bertahap** hingga 2020 (COVID), sedikit pulih 2021–2023, lalu turun lagi di 2025. Pola ini mengindikasikan bahwa kebijakan moratorium kapal (2014–2015) memiliki efek tertunda yang baru terlihat secara FII sekitar 2019–2020.
- **Top 3 WPP (712, 711, 718):** WPP712 mendominasi sepanjang waktu. WPP718 (Arafura) menunjukkan tren naik tajam 2015–2023, mengkonfirmasi ekspansi armada industri ke timur.
- FII menggabungkan volume dan skala — WPP dengan FII tinggi tapi detection_count rendah (mis. WPP718) berarti sedikit kapal tapi berskala besar → **tekanan per-unit-area sangat tinggi**.

---

## F5 · Recurring Hotspot — *Stabilitas dan Konsistensi Daerah Tangkap*

### Mengapa Dibuat?
Sebuah daerah tangkap bisa menjadi "hot" karena dua alasan berbeda:
1. **Persisten:** Dikunjungi berulang-ulang selama bertahun-tahun di koordinat yang sama (stabil).
2. **Sesaat (Ephemeral):** Sangat ramai di satu tahun tertentu tapi tidak di tahun lain.

F5 membedakan keduanya dengan menciptakan **Recurrence Score** — indeks gabungan frekuensi × tier level.

### Formula
$$Recurrence\,Score = freq\_days \times (1 + is\_L4 + is\_L5 + is\_L6)$$

Interpretasi:
- Titik L2 biasa: skor = freq_days × 1 (pengali 1)
- Titik L4: skor = freq_days × 2 (pengali 2)
- Titik L5: skor = freq_days × 3 (pengali 3)
- Titik L6: skor = freq_days × 4 (pengali 4, skor tertinggi)

### Proses yang Dilalui
1. Hitung Recurrence Score untuk setiap grid.
2. **Panel Kiri (Peta):** Plot area L4+ di atas backdrop gelap, warna berdasarkan `log(1 + Recurrence Score)` menggunakan colormap *plasma*.
3. **Panel Kanan (Bar Chart):** Bandingkan statistik (Jumlah Piksel, Median Score, Mean Score) per tier (L4 Only, L5 Only, L6).

### Insight yang Diperoleh (Berbasis Data Aktual)
- **Pola progresif yang jelas:** Semakin tinggi tier, semakin sedikit pikselnya TETAPI semakin tinggi skor rekurensinya. L4 Only (~10.600 piksel, median ~180), L5 Only (~4.800 piksel, median ~380), L6 (~4.200 piksel, median ~800). Ini memvalidasi bahwa sistem tier L4–L6 memang menangkap gradien persistensi yang benar.
- **Mean > Median di semua tier** — distribusi right-skewed, ada beberapa titik "super-recurring" di setiap tier. Titik-titik ekstrem ini adalah kandidat utama untuk zonasi kawasan suaka perikanan.
- **Peta menunjukkan konsentrasi skor tinggi (kuning terang)** di pesisir utara Jawa dan Selat Makassar — konsisten dengan temuan Gi* (Fase 6) tentang persistensi tinggi di area tersebut.

---

## F6 · Vessel Activity Evolution — *Evolusi Profil Kecerahan Armada*

### Mengapa Dibuat?
Apakah komposisi armada tangkap Indonesia berubah selama 14 tahun? Apakah makin banyak kapal industri besar atau justru armada tetap didominasi nelayan tradisional? F6 menjawabnya dengan melacak **evolusi radiance rata-rata per WPP** dari tahun ke tahun.

### Klasifikasi Armada (Berdasarkan Radiance Mean)
| Kelas | Radiance Mean | Interpretasi |
|-------|---------------|-------------|
| **Tradisional** | < 5 nW/cm²/sr | Perahu kecil, lampu sederhana (5–15 watt) |
| **Menengah** | 5–20 nW/cm²/sr | Kapal motor ukuran sedang dengan lampu halogen/LED |
| **Industri** | > 20 nW/cm²/sr | Kapal besar (>30 GT), purse seine, squid jigger dengan array lampu ratusan watt |

### Proses yang Dilalui
1. Klasifikasikan setiap kombinasi WPP×tahun berdasarkan `rad_mean` ke dalam 3 kelas.
2. **Panel Kiri (Stacked Area Chart):** Proporsi (%) WPP yang masuk kategori masing-masing kelas per tahun. Menunjukkan apakah proporsi "Industri" meningkat atau menurun.
3. **Panel Kanan (Heatmap):** Matriks WPP × Tahun dengan angka radiance mean aktual. Sel beranotasi memungkinkan pembaca membaca nilai presisi per sel.

### Insight yang Diperoleh (Berbasis Data Aktual) — KONTRADIKSI PREDIKSI

> **Temuan ini kontradiktif dengan hipotesis awal (industrialisasi). Justru itulah nilainya — temuan yang berlawanan dengan ekspektasi jauh lebih menarik bagi reviewer jurnal.**

- **Tren konvergensi dua arah, BUKAN industrialisasi satu arah:**
  - WPP yang dulunya "Industri" (712: 45→13 nW, 711: 41→22 nW, 714: 36→8 nW) justru **makin redup** secara drastis selama 14 tahun.
  - WPP yang dulunya "Tradisional" (571: 1→12 nW, 573: 1→8 nW) **makin terang** akibat modernisasi armada kecil.
  - Hasil akhir: **mayoritas WPP konvergen ke kelas "Menengah" (5–20 nW)**.
- **Stacked area chart mengkonfirmasi:** Proporsi "Tradisional" turun dari ~40% (2012) ke hampir 0% (2025), TAPI bukan digantikan "Industri" — digantikan oleh "Menengah". Proporsi "Industri" justru juga menurun.
- **Kemungkinan penyebab redupnya WPP besar:**
  1. Moratorium kapal besar (2014–2015) yang mengurangi armada >30 GT di Laut Jawa.
  2. Transisi teknologi: LED menggantikan halogen — lebih hemat daya sehingga radiance turun meski efektivitas tangkap tetap.
  3. Perpindahan kapal industri dari WPP 712 ke WPP timur (dikonfirmasi oleh C7: WPP717 +194%, WPP718 +167%).
- **WPP718 (Arafura) relatif stabil (29–51 nW)** di kisaran Industri sepanjang 14 tahun — konsisten dengan temuan E6 (P99=95.2 nW) bahwa armada di sana memang berskala besar secara persisten.
- **Implikasi kebijakan sosial-ekonomi:** Hilangnya kategori "Tradisional" bukan berarti nelayan kecil punah — melainkan mereka memodernisasi peralatan (LED). Namun efek sampingnya: mereka kini bersaing di segmen radiance yang sama dengan kapal menengah, yang bisa meningkatkan tekanan kompetitif.

---

> **Catatan:** F2 (Fenologi) dan F4 (FII) merupakan kontribusi metodologis baru yang bisa menjadi novelty paper — indeks dan analisis ini jarang diterapkan pada data VBD VIIRS dalam konteks perairan Indonesia.
