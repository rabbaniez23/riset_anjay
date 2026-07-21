# Fase 5 — Deskripsi Lengkap Visualisasi Spasial Dasar
## VBD Indonesia 2012–2026 · VIIRS Boat Detection

> Visualisasi pada fase ini dirancang untuk menjawab pertanyaan **"di mana?"**. Semua peta yang dihasilkan memanfaatkan teknik **Point-Cloud Pseudo-Mapping**, di mana ratusan ribu titik grid 0.01 derajat (`pixel_grid_L2.csv`) di-plot sangat rapat sehingga secara alami membentuk garis pantai dan batas Zona Ekonomi Eksklusif (ZEE) Indonesia tanpa memerlukan instalasi library spasial eksternal (GIS).
> 
> Seluruh visualisasi menggunakan basis referensi WGS 84 (Longitude/Latitude).

---

## B3 · Fishnet Grid Aggregation — *Kepadatan Hari Operasional*

### Mengapa Dibuat?
Langkah pertama dalam analisis spasial adalah memetakan di mana penangkapan ikan paling sering terjadi. Fishnet Grid membagi lautan menjadi kotak-kotak kecil (grid) dan menghitung jumlah hari di mana ada deteksi cahaya di grid tersebut. Semakin tinggi jumlah harinya, semakin persisten lokasi tersebut dijadikan lahan pancing.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `lon_grid`, `lat_grid` | `pixel_grid_L2.csv` | Koordinat titik (Sumbu X dan Y) |
| `freq_days` | `pixel_grid_L2.csv` | Akumulasi total hari ada deteksi dari 2012–2025 |

### Proses yang Dilalui
1. Menarik seluruh titik spasial yang telah melalui ambang batas penyaringan (L2: $\ge 22$ hari, atau *Persistent Activity*).
2. Mem-plot titik dengan skala sangat kecil (ukuran $s=0.3$) pada *colormap Viridis*.
3. Titik kuning/hijau terang melambangkan *hotspot* persisten.

### Insight yang Diperoleh
- Sebaran tidak merata. Laut Jawa, Laut Arafura, dan area perbatasan (seperti Natuna dan ZEE Samudra Hindia) secara konsisten memiliki frekuensi sangat padat. Area laut dalam seperti Laut Banda relatif sepi.

---

## V1 · KDE Density Map (Nasional Hotspots) — *Peta Densitas Episentrum*

### Mengapa Dibuat?
B3 menunjukkan semua lokasi pancing. V1 menyorot *episentrum* (titik terpusat) dari penangkapan ikan berintensitas sangat tinggi. Ini adalah peta pamungkas (Prioritas P1 / Main Figure) yang sering diminta jurnal ilmiah untuk menyimpulkan: *"Jika Anda harus menjaga 3 kawasan saja di Indonesia, kawasan manakah itu?"*

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `lon_grid`, `lat_grid` | `pixel_grid_L2.csv` | Koordinat titik |
| `is_L4` | `pixel_grid_L2.csv` | Indikator biner: Apakah area ini masuk Kategori High (Top 25%)? |

### Proses yang Dilalui
1. Membuat peta dasar (Base Map) menggunakan seluruh area L2 dengan warna biru gelap semi-transparan.
2. Memfilter data hanya untuk area **L4 (High Activity)**.
3. Melakukan teknik *2D Hexagonal Binning (Hexbin)* (sebagai proksi komputasi cepat untuk KDE - Kernel Density Estimation) pada skala logaritmik dengan *colormap Inferno*.
4. Area bercahaya terang (kuning/putih) menunjukkan di mana hotspot L4 bertumpuk sangat padat.

### Insight yang Diperoleh
- Pemusatan absolut armada tangkap ikan berlabuh pada 2 atau 3 *mega-hotspots*. 
- Membantu pemerintah (KKP) memfokuskan pengerahan kapal patroli pengawas perikanan.

---

## B8 · Radiance Density Map — *Pemetaan Skala Industri Kapal*

### Mengapa Dibuat?
Peta sebelumnya fokus pada "Seberapa Sering" (Frekuensi). Peta B8 fokus pada **"Seberapa Terang" (Radiance)**. Karena Radiance berbanding lurus dengan daya listrik/ukuran kapal, peta ini pada dasarnya adalah peta **"Di mana kapal-kapal kecil vs kapal industri beroperasi?"**.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `lon_grid`, `lat_grid` | `pixel_grid_L2.csv` | Koordinat titik |
| `log_rad_mean` | `pixel_grid_L2.csv` | Rata-rata kecerahan per grid (sudah log-transform) |

### Proses yang Dilalui
1. Mem-plot seluruh titik L2.
2. Memberikan warna berdasarkan parameter `log_rad_mean` menggunakan *colormap Magma*.
3. Titik berwarna hitam/ungu tua berarti armada tradisional (redup), sementara titik berwarna oranye terang/putih berarti beroperasi kapal-kapal raksasa berluminositas tinggi.

### Insight yang Diperoleh
- Membuktikan secara spasial teori Pareto di Fase 2: Wilayah dekat pesisir dipadati titik redup (nelayan tradisional), sementara titik di wilayah ZEE terluar (seperti Arafura bagian batas, atau ujung utara Natuna) memiliki intensitas cahaya rata-rata sangat ekstrem (kapal pukat cincin komersial / purse seine asing).

---

## G6 · Grid 700m Rasterized VBD (Tiers L4-L6) — *Zonasi Kategori VBD*

### Mengapa Dibuat?
Mengkomunikasikan data spasial ke pembuat kebijakan lebih mudah jika data sudah "diberi label" kategori. G6 menerjemahkan klasifikasi empiris (L4=High, L5=Very High, L6=Extreme) ke dalam peta kategorikal diskrit.

### Proses yang Dilalui
1. Filter data menjadi 4 irisan yang saling eksklusif (mutually exclusive):
   - **Base (L2/L3)**: Warna biru gelap, ukuran kecil.
   - **High (L4)**: Warna kuning emas, ukuran sedang.
   - **Very High (L5)**: Warna oranye kemerahan, ukuran agak besar.
   - **Extreme (L6)**: Warna merah terang, ukuran sangat besar.
2. Ditumpuk (overlaid) dari L2 hingga L6 sehingga titik paling ekstrem tampak di atas.

### Terminologi
| Istilah | Penjelasan |
|---------|------------|
| **Rasterized** | Representasi gambar menggunakan kotak-kotak piksel berukuran tetap. Data mentah VBD (titik vektor) telah di-"rasterized" ke dalam grid $0.01^\circ$ (sekitar $\sim 1.1 \times 1.1$ km). |
| **L6 (Extreme)** | Puncak dari puncak 99.5% (Persistent 99.5th Percentile) — area perairan tersibuk di nusantara. |

### Insight yang Diperoleh
- L6 (Merah Ekstrem) tidak menyebar merata, melainkan membentuk klaster urat spesifik yang biasanya mengikuti pola migrasi/upwelling ikan atau alur laut. 
- Ini peta pamungkas untuk proposal penentuan zonasi *Marine Protected Area* atau zona pelarangan *trawl*.

---

## B9 · WPP Pseudo-Choropleth — *Batas Administratif Berbasis Data*

### Mengapa Dibuat?
Analisis WPP (seperti Fase 2 dan 3) membutuhkan verifikasi visual. Kita perlu memastikan apakah pelabelan "wpp_dominant" dari raw data sudah benar. B9 memplot setiap titik grid dan mewarnainya berdasarkan nama WPP, membuktikan bahwa dataset secara alami telah membentuk poligon WPP Indonesia.

### Kolom yang Digunakan
| Kolom | Sumber File | Keterangan |
|-------|-------------|------------|
| `wpp_dominant` | `pixel_grid_L2.csv` | WPP pemenang mayoritas di grid tersebut |

### Proses yang Dilalui
1. Identifikasi nama-nama unik dari 11 WPP NRI utama.
2. Buat palette warna diskrit (Categorical Color).
3. Warnai titik dengan warna berbeda-beda untuk tiap WPP.

### Insight yang Diperoleh
- Menegaskan bahwa pengelompokan yang kita lakukan dari Fase 1 hingga 4 sangat akurat secara geometris (misalnya WPP 711 berada tepat di barat Sumatera dan utara Bangka Belitung, WPP 718 tepat di Laut Aru/Arafura).
- "Pseudo-Choropleth" ini menghilangkan kebutuhan dependensi file *Shapefile (.shp)*, memperingan pipeline analisis data, namun hasil visualisasinya memiliki akurasi resolusi tinggi.

---

> **Semua hasil Fase 5 dapat diandalkan sebagai Main Figures untuk disajikan pada Jurnal Internasional.**
