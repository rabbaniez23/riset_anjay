# Folder Visualisasi — VIIRS Boat Detection (VBD) v2

Folder ini berisi visualisasi **pola penangkapan ikan** dari data VIIRS satelit NOAA,
direvisi berdasarkan komentar dosen.

## Dataset (Unduh Hasil Data Cleaning)

Karena keterbatasan ukuran berkas di GitHub repositori (< 100 MB per file), dataset hasil pembersihan (**cleaned_data**) berukuran total ~3.85 GB diunggah di **GitHub Release**:

* 📦 **[Cleaned Dataset Lengkap (15 Tahun - 2012 s.d. 2026)](https://github.com/rabbaniez23/riset_anjay/releases/download/v1.0.0-dataset/viirs_clean_all.zip)** (~358 MB ZIP / 2.1 GB CSV) — Berisi gabungan 14,2 juta deteksi kapal.
* 📂 **[Dataset Terpisah Per Tahun (2012-2026)](https://github.com/rabbaniez23/riset_anjay/releases/download/v1.0.0-dataset/viirs_clean_yearly.zip)** (~356 MB ZIP / 1.75 GB folder) — Berisi folder data tahunan terpisah.

Silakan unduh berkas di atas dan ekstrak ke folder `visualisasi/output/cleaned_data/` sebelum menjalankan visualisasi.

---

## Cara Menjalankan

### 1. Install Python
Download dari [python.org](https://www.python.org/downloads/) dan install (centang "Add to PATH").

### 2. Install Dependensi
```bash
cd riset_anjay/visualisasi
pip install -r requirements.txt
```

### 3. (Opsional) Buat Data Bersih
```bash
python data_cleaning.py
```
Ini membuat `output/viirs_clean.csv` — duplikat data dengan hanya 11 kolom relevan.
**Data asli di `viirs/` tidak diubah sama sekali.**

### 4. Jalankan Visualisasi Utama
```bash
python visualisasi_v2.py
```

Output gambar ada di folder `output/`:
```
output/
├── 01_spasial/          # Peta kepadatan & sebaran
├── 02_kepadatan_wpp/    # Pareto & perbandingan WPP
├── 03_tren/             # Tren tahunan & bulanan
├── 04_pengelompokan/    # Distribusi cahaya & statistik
└── 05_stabilitas/       # CV stabilitas & peta CFA
```

---

## Daftar Visualisasi

### Section 1 — Spasial Lokasi Berdasarkan Density
| File | Deskripsi |
|------|-----------|
| `s1a_density_heatmap.png` | Heatmap kepadatan 0.5°×0.5° — warna gelap = sedikit, terang = banyak (sesuai komentar dosen) |
| `s1b_scatter_per_wpp.png` | Scatter plot titik kapal berwarna per WPP-RI |

### Section 2 — Perbandingan Kepadatan Antar WPP
| File | Deskripsi |
|------|-----------|
| `s2_pareto_kepadatan_wpp.png` | Bar chart + Pareto diagram dalam **satu gambar** (gabungan sesuai saran dosen). Garis merah = Kumulatif % (diperjelas dengan legend) |

### Section 3 — Evolusi Tren Jangka Panjang
| File | Deskripsi |
|------|-----------|
| `s3a_tren_tahunan_per_wpp.png` | Tren tahunan per WPP, **legend diperjelas** (garis putus-putus = regresi linear), y-axis independen per WPP |
| `s3b_pola_bulanan_per_wpp.png` | Pola musiman bulanan per WPP, **scale independen** agar semua WPP (bukan hanya WPP 712) terlihat fluktuasinya |
| `s3c_tren_agregat_all_wpp.png` | Overview total semua WPP dengan moving average 3 bulan |

### Section 4 — Pengelompokan Berdasarkan Statistik
| File | Deskripsi |
|------|-----------|
| `s4a_distribusi_cahaya.png` | Histogram distribusi Rad_DNB dengan **klasifikasi ukuran kapal** dan **referensi literatur** (Elvidge et al., 2015; NOAA VBD ATBD) |
| `s4b_tabel_statistik_wpp.png` | Tabel statistik deskriptif Rad_DNB per WPP (mean, median, std, IQR, max) |

### Section 5 — Stabilitas Jangka Panjang
| File | Deskripsi |
|------|-----------|
| `s5a_stabilitas_cv_wpp.png` | Koefisien Variasi per WPP: **2 panel** (semua tahun vs 2 tahun terakhir) sesuai saran dosen |
| `s5b_cfa_gradasi_warna.png` | Peta Core Fishing Area dengan **gradasi warna** berdasarkan skor konsistensi (sesuai saran dosen untuk koordinat lebih jelas) |

---

## Penghapusan Kolom VIIRS

File `data_cleaning.py` menduplikasi data VIIRS dengan hanya menyimpan **11 dari 49 kolom** asli.
Lihat `data_cleaning.py` untuk alasan lengkap setiap penghapusan kolom.

**Kolom yang dipakai:**
`Lat_DNB, Lon_DNB, Rad_DNB, Date_Mscan, QF_Detect, QF_Bitflag, Land_Mask, EEZ, MPA, Rad_I04, Glint`

**Kolom yang dihapus (38 kolom):** metadata teknis sensor (nama file, sudut satelit/matahari/bulan, parameter threshold internal) yang tidak relevan untuk analisis pola penangkapan ikan.

---

## Referensi

- Elvidge, C.D., et al. (2015). *Methods for Global Survey of Natural Gas Flaring from Visible Infrared Imaging Radiometer Suite Data*. Energies, 9(1), 14.
- NOAA CoastWatch. (2017). *VIIRS Boat Detection (VBD) Algorithm Theoretical Basis Document*. NOAA Technical Report.
- Kroodsma, D.A., et al. (2018). *Tracking the global footprint of fisheries*. Science, 359(6378), 904–908.
