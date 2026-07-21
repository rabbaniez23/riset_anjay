# Laporan Analisis Threshold Empiris

## Data VIIRS Boat Detection — Indonesia 2012–2026

### Berbasis 17.833.394 Baris Data Aktual (bukan estimasi)

---

> Seluruh angka dalam dokumen ini berasal dari **komputasi riil** terhadap 5.041 file CSV
> (2012–2026), total 17.833.394 baris VBD, 1.923.499 piksel unik pada grid 0.01° (~1.1 km).
> Laporan lengkap tersimpan di [threshold_analysis_report.txt]

---

## Statistik Dasar Distribusi Frekuensi Piksel

| Metrik                     | Nilai           |
| -------------------------- | --------------- |
| Total baris VBD            | **17.833.394**  |
| Total file diproses        | 5.041           |
| Piksel unik (grid 0.01°)   | **1.923.499**   |
| Frekuensi Minimum          | 1 hari          |
| Frekuensi Maximum          | **13.279 hari** |
| Frekuensi Mean             | 9,3 hari        |
| **Frekuensi Median (P50)** | **2,0 hari**    |

> [!NOTE]
> Distribusi sangat **right-skewed ekstrem** — median hanya 2 hari, mean 9,3 hari,
> tapi nilai maksimum mencapai 13.279 hari. Ini berarti sebagian besar piksel
> sangat jarang dikunjungi, dan sedikit sekali piksel yang benar-benar menjadi
> fishing ground permanen.

---

## Tabel Persentil Frekuensi (Empiris)

| Persentil | Threshold (hari) | Interpretasi                        |
| --------- | ---------------- | ----------------------------------- |
| P50       | **2 hari**       | Setengah piksel dikunjungi ≤ 2 kali |
| P60       | **3 hari**       |                                     |
| P70       | **5 hari**       |                                     |
| P75       | **7 hari**       | 75% piksel dikunjungi ≤ 7 hari      |
| P80       | **10 hari**      |                                     |
| P85       | **15 hari**      |                                     |
| P90       | **22 hari**      | Hanya 10% piksel yang ≥ 22 hari     |
| P91       | **24 hari**      |                                     |
| P92       | **26 hari**      |                                     |
| P93       | **29 hari**      |                                     |
| P94       | **33 hari**      |                                     |
| P95       | **37 hari**      | Hanya 5% piksel yang ≥ 37 hari      |
| P96       | **44 hari**      |                                     |
| P97       | **53 hari**      |                                     |
| P98       | **68 hari**      |                                     |
| **P99**   | **101 hari**     | **Hanya 1% piksel yang ≥ 101 hari** |
| P99.5     | **146 hari**     |                                     |
| P99.9     | **322 hari**     |                                     |

---

## Distribusi Piksel per Bracket Frekuensi

| Bracket                         | Jumlah Piksel | % Piksel   | % Kumulatif |
| ------------------------------- | ------------- | ---------- | ----------- |
| Sangat Jarang (1–4 hari)        | **1.283.156** | **66,71%** | 66,71%      |
| Jarang (5–9 hari)               | 233.584       | 12,14%     | 78,85%      |
| Kadang (10–19 hari)             | 191.360       | 9,95%      | 88,80%      |
| Aktif Rendah (20–49 hari)       | 150.863       | 7,84%      | 96,64%      |
| Aktif Sedang (50–99 hari)       | 44.775        | 2,33%      | 98,97%      |
| **Aktif Tinggi (100–199 hari)** | **14.568**    | **0,76%**  | 99,73%      |
| Hotspot (200–499 hari)          | 4.386         | 0,23%      | 99,96%      |
| Core Hotspot (500–999 hari)     | 579           | 0,03%      | 99,99%      |
| **Inti Permanen (≥1000 hari)**  | **227**       | **0,01%**  | 100,00%     |

---

## ⚠️ Kritik terhadap Threshold 100 Hari

> [!CAUTION]
> **Threshold 100 hari yang diusulkan = Persentil ke-99,0.**
> Artinya hanya **19.761 piksel (1,03%)** yang lolos dari total 1,9 juta piksel.
> Ini adalah threshold yang **sangat agresif**, lebih cocok untuk identifikasi
> "inti permanen" bukan untuk visualisasi eksplorasi awal.

| Threshold (hari) | Persentil setara | Piksel lolos      | % Piksel  |
| ---------------- | ---------------- | ----------------- | --------- |
| 50 hari          | ~P97             | 64.536 piksel     | 3,36%     |
| **100 hari**     | **~P99,0**       | **19.761 piksel** | **1,03%** |
| 200 hari         | ~P99,7           | 5.193 piksel      | 0,27%     |

---

## Rekomendasi Threshold Berlapis — Berbasis Data Empiris

### Sistem 5-Level Threshold

| Level  | Nama            | Threshold            | Piksel Tampil  | Digunakan Untuk                |
| ------ | --------------- | -------------------- | -------------- | ------------------------------ |
| **L1** | **Eksplorasi**  | **≥ 10 hari** (P80)  | ~385.000 (20%) | EDA awal, heat map exploratory |
| **L2** | **Aktif**       | **≥ 22 hari** (P90)  | ~193.000 (10%) | Visualisasi utama, density map |
| **L3** | **Significant** | **≥ 37 hari** (P95)  | ~96.000 (5%)   | Hotspot kandidat, untuk paper  |
| **L4** | **Hotspot**     | **≥ 68 hari** (P98)  | ~38.000 (2%)   | Fishing ground terkonfirmasi   |
| **L5** | **Core**        | **≥ 101 hari** (P99) | ~19.761 (1%)   | Inti permanen, publikasi       |

> **Rekomendasi untuk visualisasi:**
>
> - **Default display map**: gunakan **L2 (≥ 22 hari)** — 10% piksel, tidak terlalu crowded, tidak terlalu sepi
> - **Untuk paper/figure utama**: gunakan **L3 (≥ 37 hari)** + **L4 (≥ 68 hari)** sebagai dua layer berbeda
> - **Untuk hotspot inti**: gunakan **L5 (≥ 101 hari)** — seperti yang diusulkan di Instruksi1.md
> - Jika masih crowded di L2: naik ke L3. Jika terlalu sepi: turun ke L1.

### Kenapa BUKAN Threshold Absolut Global?

Perlu dipertimbangkan: karena **WPP712 mendominasi 41,8%** dari total deteksi, threshold absolut global akan sangat bias terhadap Laut Jawa. Pertimbangkan **threshold adaptif per WPP** untuk visualisasi per-wilayah.

---

## Distribusi Radiance (nW/cm²/sr)

| Metrik           | Nilai                                   |
| ---------------- | --------------------------------------- |
| Sample n         | 500.000 titik                           |
| Mean             | 377,58 (**sangat dipengaruhi outlier**) |
| **Median (P50)** | **6,38**                                |

### Persentil Radiance

| Persentil | Radiance (nW/cm²/sr) |
| --------- | -------------------- |
| P25       | 2,12                 |
| P50       | **6,38**             |
| P75       | 20,14                |
| P90       | 69,09                |
| P95       | 118,90               |
| **P99**   | **344,69**           |
| P99.5     | 779,76               |

### Distribusi Kelas Radiance

| Kelas     | Range    | Jumlah      | %          | Interpretasi Armada            |
| --------- | -------- | ----------- | ---------- | ------------------------------ |
| Ultra-low | < 0.5    | 7.139       | 1,43%      | Mungkin noise / glint          |
| Very low  | 0.5–2    | 111.695     | 22,34%     | Kapal tradisional kecil        |
| **Low**   | **2–10** | **184.483** | **36,90%** | **Nelayan lokal (dominan)**    |
| Med-low   | 10–50    | 129.746     | 25,95%     | Kapal skala menengah           |
| Medium    | 50–200   | 56.535      | 11,31%     | Kapal komersial                |
| High      | 200–1000 | 8.378       | 1,68%      | Kapal industri                 |
| Very High | > 1000   | 2.024       | 0,40%      | Kapal industri besar / anomali |

> [!NOTE]
> Mayoritas (36,9%) berada di kelas **Low (2–10 nW/cm²/sr)** → mayoritas armada adalah kapal nelayan tradisional lokal.
> Kelas "High" (>200) hanya 2,08% → kapal industri besar adalah minoritas.
>
> **Batas kelas radiance yang direkomendasikan (berbasis data):**
>
> - Kecil: < 10 nW/cm²/sr (P50 = 6,4)
> - Menengah: 10–100 nW/cm²/sr (P50–P92 range)
> - Besar: 100–1000 nW/cm²/sr (P95–P99.5)
> - Industrial/Anomali: > 1000 nW/cm²/sr (P99.5+)

---

## Distribusi per WPP (Empiris)

| WPP        | Deteksi       | %          | Keterangan                              |
| ---------- | ------------- | ---------- | --------------------------------------- |
| **WPP712** | **4.754.207** | **41,80%** | Laut Jawa — **DOMINAN MUTLAK**          |
| WPP711     | 1.867.481     | 16,42%     | Selat Makassar, Teluk Bone              |
| WPP713     | 1.153.715     | 10,14%     | Selat Makassar, Laut Sulawesi           |
| WPP718     | 868.494       | 7,64%      | Laut Aru, Arafura, Timor Timur          |
| WPP572     | 629.126       | 5,53%      | Samudera Hindia Barat Sumatra           |
| WPP571     | 518.182       | 4,56%      | Selat Malaka, Andaman                   |
| WPP573     | 463.940       | 4,08%      | Samudera Hindia Selatan Jawa            |
| ARMM\*     | 361.135       | 3,18%      | \*Data Filipina (ARMM) — perlu difilter |
| WPP714     | 227.086       | 2,00%      | Teluk Tolo, Laut Banda                  |
| WPP716     | 216.815       | 1,91%      | Laut Sulawesi, Teluk Tomini             |
| WPP715     | 112.156       | 0,99%      | Teluk Tomini, Laut Maluku               |
| WPP717     | 44.689        | 0,39%      | Laut Seram, Teluk Berau                 |

> [!WARNING]
> Ditemukan deteksi berlabel **ARMM** (Autonomous Region in Muslim Mindanao — Filipina)
> dan **Region IX, XI, XII, XIII** dalam dataset. Ini bukan WPP Indonesia.
> Perlu difilter menggunakan kolom `EEZ` = "Indonesian Exclusive Economic Zone"
> sebelum analisis lebih lanjut.

---

## Distribusi per Tahun

| Tahun    | Deteksi       | %         | Catatan                     |
| -------- | ------------- | --------- | --------------------------- |
| 2012     | 878.381       | 4,93%     | Data mulai April 2012       |
| 2013     | 1.051.962     | 5,90%     |                             |
| 2014     | 1.266.049     | 7,10%     | Tren naik                   |
| 2015     | 1.332.579     | 7,47%     |                             |
| 2016     | 1.228.336     | 6,89%     | Sedikit turun               |
| 2017     | 1.128.860     | 6,33%     |                             |
| 2018     | 1.279.513     | 7,17%     | Rebound                     |
| **2019** | **1.546.490** | **8,67%** | **Puncak tertinggi**        |
| 2020     | 1.501.132     | 8,42%     | COVID — turun sedikit       |
| 2021     | 1.443.713     | 8,10%     |                             |
| 2022     | 1.164.335     | 6,53%     | Penurunan signifikan        |
| **2023** | **1.422.510** | **7,98%** | Recovery                    |
| 2024     | 1.054.522     | 5,91%     |                             |
| 2025     | 1.074.187     | 6,02%     |                             |
| 2026     | 460.825       | 2,58%     | Data parsial (s/d Jul 2026) |

---

## Ringkasan Keputusan Threshold

```
REKOMENDASI FINAL THRESHOLD SISTEM BERLAPIS:

   LEVEL      THRESHOLD      PIKSEL LOLOS    GUNAKAN UNTUK
   ─────────────────────────────────────────────────────────
   Eksplorasi  >= 10 hari    ~20% piksel     EDA, heat map awal
   Aktif       >= 22 hari    ~10% piksel     Visualisasi umum (DEFAULT)
   Significant >= 37 hari    ~ 5% piksel     Hotspot kandidat
   Hotspot     >= 68 hari    ~ 2% piksel     Fishing ground terkonfirmasi
   Core        >= 101 hari   ~ 1% piksel     Inti permanen (paper)
   Apex        >= 146 hari   ~0.5% piksel    Main figure publikasi
```

---

## Temuan Penting yang Perlu Ditindaklanjuti

1. **WPP712 (Laut Jawa) = 41,8% dari seluruh deteksi** — dominasi ini akan sangat terlihat di peta nasional; pertimbangkan visualisasi terpisah agar WPP lain tidak "tertutup"

2. **Data non-Indonesia ditemukan** — baris berlabel ARMM, Region IX/XI/XII/XIII (Filipina) perlu difilter

3. **2019 adalah puncak aktivitas** (8,67%) — sangat menarik untuk diteliti faktor penyebabnya

4. **2022 mengalami penurunan tajam** dari 2021 (8,1% → 6,5%) — kandidat change-point analysis

5. **Radiance sangat skewed** — mean 377 vs median 6,4 → log-transform wajib sebelum visualisasi distribusi

6. **227 piksel dikunjungi ≥ 1000 hari** selama 14 tahun — ini adalah fishing ground inti sejati Indonesia

---

_Analisis dihasilkan dari 17.833.394 baris VBD · 5.041 file · 1.923.499 piksel unik · Grid 0.01° · Durasi komputasi: 504 detik_
