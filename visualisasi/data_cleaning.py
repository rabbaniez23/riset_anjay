"""
data_cleaning.py
-----------------
Script untuk membuat duplikat data VIIRS yang sudah dibersihkan kolom-kolomnya.
- TIDAK mengubah data mentah asli di folder viirs/
- Membuat file baru: viirs_clean.csv (subset kolom yang relevan)

Alasan setiap kolom yang dihapus didokumentasikan di bawah.
"""

import os
import glob
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ─── Path ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
VIIRS_DIR  = os.path.join(BASE_DIR, '..', 'viirs')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
CLEAN_CSV  = os.path.join(OUTPUT_DIR, 'viirs_clean.csv')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Kolom yang DIPAKAI ───────────────────────────────────────────────────────
# Dari 49 kolom asli VIIRS, hanya 11 yang relevan untuk analisis fishing pattern:
KEEP_COLUMNS = [
    'Lat_DNB',    # Latitude koordinat kapal → wajib untuk spasial
    'Lon_DNB',    # Longitude koordinat kapal → wajib untuk spasial
    'Rad_DNB',    # Radiance Day-Night Band → brightness kapal (kelasifikasi ukuran)
    'Date_Mscan', # Tanggal & waktu scan aktual → untuk analisis temporal
    'QF_Detect',  # Quality Flag deteksi: 1=transit, 2/4=fishing, lainnya=noise
    'QF_Bitflag', # Detail bitflag untuk filtering lanjutan (jika perlu)
    'Land_Mask',  # 1=darat, 0=laut → filter hanya deteksi di laut
    'EEZ',        # Zona Ekonomi Eksklusif → identifikasi perairan Indonesia
    'MPA',        # Marine Protected Area → deteksi illegal fishing
    'Rad_I04',    # Radiance infrared band I04 → validasi / deteksi api vs kapal
    'Glint',      # Nilai sunglint → untuk filtering noise refleksi matahari
]

# ─── Dokumentasi Kolom yang DIHAPUS ──────────────────────────────────────────
REMOVED_COLUMNS_REASON = {
    'id':           'ID baris internal NOAA, tidak relevan untuk analisis',
    'id_Key':       'ID string unik granule file, tidak dipakai analisis',
    'Date_Proc':    'Tanggal server NOAA memproses data (bukan tanggal kejadian)',
    'Date_LTZ':     'Waktu lokal (Local Time Zone), redundan dengan Date_Mscan',
    'Line_DNB':     'Koordinat baris pixel pada sensor (internal VIIRS), tidak dipakai',
    'Sample_DNB':   'Koordinat kolom pixel pada sensor (internal VIIRS), tidak dipakai',
    'SMI':          'Sensor Measurement Index – threshold internal, sudah terangkum di QF_Detect',
    'Thr_SMI':      'Threshold SMI – parameter kalibrasi internal sensor',
    'SI':           'Stability Index – indeks internal, tidak dipakai analisis fishing',
    'Thr_SI':       'Threshold SI – parameter internal',
    'SHI':          'Spatial Homogeneity Index – internal, tidak dipakai',
    'Thr_SHI':      'Threshold SHI – parameter internal',
    'LI':           'Lightning Index – jarang relevan untuk kapal nelayan',
    'Thr_LI':       'Threshold LI – parameter internal',
    'Thr_Gl_SMI':   'Threshold glint untuk SMI – parameter kalibrasi internal',
    'Xcorr':        'Cross-correlation score internal algoritma deteksi',
    'FMZ':          'Fisheries Management Zone (basis Philippines/regional), redundan dengan WPP-RI',
    'File_DNB':     'Nama file HDF5 sumber sensor DNB – metadata provenance saja',
    'File_GDNB':    'Nama file GDNBO sumber – metadata provenance saja',
    'File_I04':     'Nama file infrared I04 sumber – metadata provenance saja',
    'File_VNF':     'Nama file VNF (Visible Night Fire) – metadata provenance',
    'File_EEZ':     'Nama file shapefile EEZ yang dipakai NOAA – bukan data analisis',
    'File_FMZ':     'Nama file shapefile FMZ – metadata provenance',
    'File_MPA':     'Nama file shapefile MPA – metadata provenance',
    'File_FLM':     'Nama file bitmask flare/lightning – metadata provenance',
    'File_LSM':     'Nama file land-sea mask – metadata provenance',
    'File_LTZ':     'Nama file timezone shapefile – metadata provenance',
    'File_RLP':     'Nama file recurring light platform – metadata provenance',
    'File_RLV':     'Nama file recurring light vessel – metadata provenance',
    'Dist_RLP':     'Jarak ke recurring light platform (platform permanen) – kurang relevan',
    'Lat_Gring':    'Latitude bounding box granule sensor – metadata teknis sensor',
    'Lon_Gring':    'Longitude bounding box granule sensor – metadata teknis sensor',
    'Gran_List':     'Daftar nama granule yang berkontribusi – metadata teknis',
    'SOLZ_GDNBO':   'Sudut zenith matahari – tidak relevan (data malam hari)',
    'SOLA_GDNBO':   'Sudut azimuth matahari – tidak relevan (data malam hari)',
    'SATZ_GDNBO':   'Sudut zenith satelit – metadata teknis akuisisi sensor',
    'SATA_GDNBO':   'Sudut azimuth satelit – metadata teknis akuisisi sensor',
    'LUNZ_GDNBO':   'Sudut zenith bulan – moonlight bias sudah diatasi melalui QF_Detect',
    'LUNA_GDNBO':   'Sudut azimuth bulan – moonlight bias sudah diatasi melalui QF_Detect',
}


def print_column_removal_report():
    """Cetak laporan kolom yang dihapus dan alasannya."""
    print("\n" + "="*70)
    print("LAPORAN KOLOM YANG DIHAPUS DARI DATA VIIRS")
    print("="*70)
    print(f"Total kolom asli  : 49 kolom")
    print(f"Kolom yang dipakai: {len(KEEP_COLUMNS)} kolom")
    print(f"Kolom yang dihapus: {len(REMOVED_COLUMNS_REASON)} kolom")
    print("\n[KOLOM DIPAKAI]:")
    for i, col in enumerate(KEEP_COLUMNS, 1):
        print(f"  {i:2}. {col}")
    print("\n[KOLOM DIHAPUS & ALASAN]:")
    for i, (col, reason) in enumerate(REMOVED_COLUMNS_REASON.items(), 1):
        print(f"  {i:2}. {col:<20} -> {reason}")
    print("="*70 + "\n")


def load_and_clean_viirs_by_year():
    """
    Membaca data VIIRS per folder tahun (2012, 2013, ...), 
    membersihkan kolom, melakukan spatial join WPP_RI, dan menyimpan per tahun.
    Contoh: output/cleaned_data/2014/viirs_clean_2014.csv
    """
    import shapefile
    import shapely
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    from shapely.ops import unary_union

    clean_base_dir = os.path.join(OUTPUT_DIR, 'cleaned_data')
    os.makedirs(clean_base_dir, exist_ok=True)

    # Load shapefiles WPP-RI
    shp_dir = os.path.join(BASE_DIR, '..', 'shp&shx')
    wpp_tree = None
    wpp_codes_list = []
    if os.path.exists(shp_dir):
        geoms_list = []
        for fn in sorted(os.listdir(shp_dir)):
            if fn.endswith('.shp'):
                m = re.search(r'WPP-RI\s+(\d+)', fn)
                code = m.group(1) if m else fn.replace('.shp','')
                sf = shapefile.Reader(shp=os.path.join(shp_dir, fn))
                shapes_in_file = [shape(s) for s in sf.shapes() if s.shapeType != 0]
                if shapes_in_file:
                    u = shapes_in_file[0] if len(shapes_in_file) == 1 else unary_union(shapes_in_file)
                    geoms_list.append(u)
                    wpp_codes_list.append(code)
        if geoms_list:
            wpp_tree = STRtree(geoms_list)
            print(f"Shapefile WPP-RI berhasil dimuat ({len(wpp_codes_list)} wilayah WPP).")

    # Cari semua folder tahun di VIIRS_DIR
    year_dirs = sorted([d for d in os.listdir(VIIRS_DIR) 
                        if os.path.isdir(os.path.join(VIIRS_DIR, d)) and d.isdigit()])

    all_dfs = []

    print(f"Ditemukan {len(year_dirs)} folder tahun: {year_dirs}\n")

    for yr in year_dirs:
        yr_dir_path = os.path.join(VIIRS_DIR, yr)
        csv_files = sorted(glob.glob(os.path.join(yr_dir_path, '*.csv')))

        if not csv_files:
            continue

        print(f"--- Memproses Tahun {yr} ({len(csv_files)} file CSV) ---")
        dfs_year = []
        for fpath in csv_files:
            try:
                df_raw = pd.read_csv(fpath, low_memory=False)
                cols_available = [c for c in KEEP_COLUMNS if c in df_raw.columns]
                df_sub = df_raw[cols_available].copy()

                if 'Date_Mscan' in df_sub.columns:
                    df_sub['Date'] = pd.to_datetime(df_sub['Date_Mscan'], errors='coerce').dt.date
                else:
                    fname = os.path.basename(fpath)
                    date_str = fname[10:18]
                    try:
                        df_sub['Date'] = pd.to_datetime(date_str, format='%Y%m%d').date()
                    except:
                        df_sub['Date'] = None

                df_sub['Year']  = pd.to_datetime(df_sub['Date'], errors='coerce').dt.year
                df_sub['Month'] = pd.to_datetime(df_sub['Date'], errors='coerce').dt.month
                df_sub['Day']   = pd.to_datetime(df_sub['Date'], errors='coerce').dt.day

                dfs_year.append(df_sub)
            except Exception as e:
                print(f"  SKIP {os.path.basename(fpath)}: {e}")
                continue

        if not dfs_year:
            print(f"  Tidak ada data valid di tahun {yr}.")
            continue

        df_yr_clean = pd.concat(dfs_year, ignore_index=True)

        # Filter QF_Detect valid (1=transit, 2/4=fishing)
        if 'QF_Detect' in df_yr_clean.columns:
            df_yr_clean = df_yr_clean[df_yr_clean['QF_Detect'].isin([1, 2, 4])]

        # Assign WPP_RI
        if wpp_tree is not None and not df_yr_clean.empty:
            pts = shapely.points(df_yr_clean['Lon_DNB'].values, df_yr_clean['Lat_DNB'].values)
            res = wpp_tree.query(pts, predicate='intersects')
            wpp_arr = ['Outside'] * len(df_yr_clean)
            for pt_idx, geom_idx in zip(res[0], res[1]):
                wpp_arr[pt_idx] = wpp_codes_list[geom_idx]
            df_yr_clean['WPP_RI'] = wpp_arr

        # Buat folder per tahun
        yr_output_dir = os.path.join(clean_base_dir, yr)
        os.makedirs(yr_output_dir, exist_ok=True)
        yr_csv_path = os.path.join(yr_output_dir, f'viirs_clean_{yr}.csv')

        df_yr_clean.to_csv(yr_csv_path, index=False)
        print(f"  [OK] Tersimpan: {yr_csv_path} ({len(df_yr_clean):,} baris)")

        all_dfs.append(df_yr_clean)

    if all_dfs:
        df_all = pd.concat(all_dfs, ignore_index=True)
        all_csv_path = os.path.join(clean_base_dir, 'viirs_clean_all.csv')
        df_all.to_csv(all_csv_path, index=False)
        print(f"\n" + "="*70)
        print(f"[SELESAI TOTAL] {len(df_all):,} baris gabungan tersimpan di:")
        print(f"  -> {all_csv_path}")
        print("="*70)
        return df_all
    else:
        print("ERROR: Tidak ada data berhasil dibersihkan.")
        return pd.DataFrame()


def main():
    print_column_removal_report()
    print("Memproses dan memisahkan data hasil cleaning per folder tahun...\n")
    load_and_clean_viirs_by_year()


if __name__ == '__main__':
    main()
