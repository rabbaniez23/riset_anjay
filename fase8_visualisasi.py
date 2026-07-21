"""
FASE 8: BRIGHTNESS & FISHING ANALYSIS -- 6 Visualisasi
========================================================
  E2  -- Radiance Spatial Map (peta kecerahan rata-rata per grid)
  E6  -- Radiance Percentile per WPP (box+whisker percentile)
  F2  -- Fishing Season Phenology (onset/offset/durasi musim tangkap)
  F4  -- Fishing Intensity Index (indeks komposit per WPP per tahun)
  F5  -- Recurring Hotspot (konsistensi hotspot lintas tahun)
  F6  -- Vessel Activity Evolution (evolusi komposisi armada)

Input:
  pixel_grid_L2.csv       -> E2, F5
  monthly_aggregated.csv  -> F2, F4, F6
  yearly_aggregated.csv   -> E6, F4, F6

Output: output/fase8/*.png
"""

import matplotlib
matplotlib.use('Agg')

import os, sys, time, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.cm as cm
import seaborn as sns

warnings.filterwarnings('ignore')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ============================================================
# KONFIGURASI
# ============================================================
BASE     = r"e:\UNIVERSITAS PENDIDIKAN INDONESIA\PENELITIAN\FISHING GROUND PATTERN\riset_viirs"
OUT_DIR  = os.path.join(BASE, "output")
F8_DIR   = os.path.join(OUT_DIR, "fase8")
os.makedirs(F8_DIR, exist_ok=True)

GRID_L2  = os.path.join(OUT_DIR, "pixel_grid_L2.csv")
MONTHLY  = os.path.join(OUT_DIR, "monthly_aggregated.csv")
YEARLY   = os.path.join(OUT_DIR, "yearly_aggregated.csv")

WPP_ORDER = ['WPP571','WPP572','WPP573','WPP711','WPP712','WPP713',
             'WPP714','WPP715','WPP716','WPP717','WPP718']

WPP_SHORT = {w: w.replace('WPP','') for w in WPP_ORDER}

MONTH_NAMES = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'Mei',6:'Jun',
               7:'Jul',8:'Agu',9:'Sep',10:'Okt',11:'Nov',12:'Des'}

MAP_XLIM = (94, 142)
MAP_YLIM = (-12, 7)

plt.rcParams.update({
    'font.size': 9, 'font.family': 'DejaVu Sans',
    'axes.titlesize': 10, 'axes.labelsize': 9,
    'figure.dpi': 120, 'savefig.dpi': 180,
    'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
})

t0 = time.time()
print("=" * 68)
print("FASE 8: BRIGHTNESS & FISHING ANALYSIS -- 6 Visualisasi")
print("=" * 68)


def format_map(ax, title=''):
    ax.set_xlim(*MAP_XLIM); ax.set_ylim(*MAP_YLIM)
    ax.set_aspect('equal', adjustable='box')
    if title: ax.set_title(title, pad=8, fontweight='bold', fontsize=9)
    ax.tick_params(labelsize=7)
    ax.grid(True, color='#BDC3C7', linestyle=':', alpha=0.4)

def load_monthly_clean():
    df = pd.read_csv(MONTHLY)
    return df[(df['month'] > 0) & (df['is_partial_year'] == 0) &
              df['wpp'].isin(WPP_ORDER)].copy()


# ============================================================
# E2: RADIANCE SPATIAL MAP
# ============================================================
def vis_E2():
    print("\n[1/6] E2 -- Radiance Spatial Map...")
    t = time.time()

    df = pd.read_csv(GRID_L2, usecols=['lat_grid','lon_grid','rad_mean','log_rad_mean',
                                        'rad_max','wpp_dominant'],
                     dtype={'lat_grid':'float32','lon_grid':'float32',
                            'rad_mean':'float32','log_rad_mean':'float32',
                            'rad_max':'float32'})

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(
        'E2 · Radiance Spatial Map — Distribusi Spasial Kecerahan Cahaya Kapal\n'
        'Rata-rata (kiri) dan Maksimum (kanan) per Grid 0.01° (2012–2025)',
        fontsize=11, fontweight='bold', y=1.01)

    # Panel kiri: log_rad_mean
    ax = axes[0]
    ax.set_facecolor('#0D2137')
    sc = ax.scatter(df['lon_grid'], df['lat_grid'], c=df['log_rad_mean'],
                    cmap='inferno', s=0.25, alpha=0.8, vmin=0.5, vmax=4.5)
    format_map(ax, 'Rata-rata Radiance (log scale)')
    cb = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label('log(1 + Radiance Rata-rata)', fontsize=8)

    # Panel kanan: rad_max (log-transformed)
    ax2 = axes[1]
    ax2.set_facecolor('#0D2137')
    log_max = np.log1p(df['rad_max'])
    sc2 = ax2.scatter(df['lon_grid'], df['lat_grid'], c=log_max,
                      cmap='hot', s=0.25, alpha=0.8, vmin=1, vmax=7)
    format_map(ax2, 'Radiance Maksimum (log scale)')
    cb2 = plt.colorbar(sc2, ax=ax2, fraction=0.03, pad=0.02)
    cb2.set_label('log(1 + Radiance Maksimum)', fontsize=8)

    plt.tight_layout()
    out = os.path.join(F8_DIR, 'E2_radiance_spatial.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# E6: RADIANCE PERCENTILE PER WPP
# ============================================================
def vis_E6():
    print("\n[2/6] E6 -- Radiance Percentile per WPP...")
    t = time.time()

    df = pd.read_csv(GRID_L2, usecols=['rad_mean','wpp_dominant'],
                     dtype={'rad_mean':'float32'})
    df = df[df['wpp_dominant'].isin(WPP_ORDER)]
    df['log_rad'] = np.log1p(df['rad_mean'])

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(
        'E6 · Radiance Percentile per WPP\n'
        'Distribusi Statistik Kecerahan Kapal di Setiap Wilayah Pengelolaan Perikanan',
        fontsize=11, fontweight='bold', y=1.01)

    # Panel kiri: Box + Whisker (log scale)
    ax = axes[0]
    ax.set_facecolor('#FAFAFA')
    order = df.groupby('wpp_dominant')['rad_mean'].median().sort_values(ascending=False).index
    sns.boxplot(data=df, x='wpp_dominant', y='log_rad', order=order, ax=ax,
                palette='YlOrRd', showfliers=False, linewidth=0.8)
    ax.set_xlabel('WPP')
    ax.set_ylabel('log(1 + Radiance Rata-rata)')
    ax.set_title('Distribusi Radiance per WPP (Box Plot)', fontsize=9)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, axis='y', alpha=0.3)

    # Panel kanan: Heatmap percentile (P10, P25, P50, P75, P90, P95, P99)
    ax2 = axes[1]
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    pct_data = {}
    for wpp in WPP_ORDER:
        sub = df[df['wpp_dominant'] == wpp]['rad_mean']
        pct_data[WPP_SHORT[wpp]] = [np.percentile(sub, p) for p in percentiles]

    pct_df = pd.DataFrame(pct_data, index=[f'P{p}' for p in percentiles])
    sns.heatmap(pct_df, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax2,
                linewidths=0.5, cbar_kws={'label': 'Radiance (nW/cm²/sr)'})
    ax2.set_title('Tabel Persentil Radiance per WPP', fontsize=9)
    ax2.set_ylabel('Persentil')

    plt.tight_layout()
    out = os.path.join(F8_DIR, 'E6_radiance_percentile.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# F2: FISHING SEASON PHENOLOGY
# ============================================================
def vis_F2():
    print("\n[3/6] F2 -- Fishing Season Phenology...")
    t = time.time()

    df = load_monthly_clean()

    # Rata-rata bulanan per WPP (lintas tahun)
    monthly_avg = df.groupby(['wpp','month'])['detection_count'].mean().reset_index()

    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle(
        'F2 · Fishing Season Phenology — Fenologi Musim Tangkap per WPP\n'
        'Onset (Awal Musim), Peak (Puncak), Offset (Akhir) Berdasarkan Threshold 50% dari Peak',
        fontsize=11, fontweight='bold', y=0.99)

    # Panel atas: Profil bulanan per WPP (normalized 0-1)
    ax = axes[0]
    ax.set_facecolor('#FAFAFA')
    cmap = cm.get_cmap('tab20', len(WPP_ORDER))
    phenology_data = []

    for i, wpp in enumerate(WPP_ORDER):
        sub = monthly_avg[monthly_avg['wpp'] == wpp].sort_values('month')
        vals = sub['detection_count'].values
        if len(vals) < 12:
            continue
        # Normalisasi ke 0-1
        vmin, vmax = vals.min(), vals.max()
        norm_vals = (vals - vmin) / (vmax - vmin + 1e-9)
        months = sub['month'].values

        color = cmap(i)
        ax.plot(months, norm_vals, marker='o', markersize=4, linewidth=1.5,
                color=color, label=WPP_SHORT[wpp], alpha=0.8)

        # Hitung onset/peak/offset (threshold = 50% dari peak normalized)
        peak_month = months[np.argmax(norm_vals)]
        threshold = 0.5
        above = months[norm_vals >= threshold]
        onset  = above[0] if len(above) > 0 else peak_month
        offset = above[-1] if len(above) > 0 else peak_month
        duration = offset - onset + 1 if offset >= onset else (12 - onset + offset + 1)
        phenology_data.append({
            'WPP': WPP_SHORT[wpp], 'Onset': onset, 'Peak': peak_month,
            'Offset': offset, 'Duration': duration
        })

    ax.axhline(0.5, color='red', linestyle='--', alpha=0.6, label='Threshold 50%')
    ax.set_xlabel('Bulan')
    ax.set_ylabel('Normalized Activity (0–1)')
    ax.set_xticks(range(1,13))
    ax.set_xticklabels([MONTH_NAMES[m] for m in range(1,13)])
    ax.set_title('Profil Bulanan Aktivitas (Normalized per WPP)', fontsize=9)
    ax.legend(ncol=6, fontsize=7, loc='upper right')
    ax.grid(True, alpha=0.3)

    # Panel bawah: Gantt chart fenologi
    ax2 = axes[1]
    ax2.set_facecolor('#FAFAFA')
    phen_df = pd.DataFrame(phenology_data)

    colors_gantt = [cmap(i) for i in range(len(phen_df))]
    for i, row in phen_df.iterrows():
        onset  = row['Onset']
        offset = row['Offset']
        peak   = row['Peak']

        # Gambar bar musim tangkap
        if offset >= onset:
            ax2.barh(i, offset - onset + 1, left=onset - 0.5,
                     color=colors_gantt[i], alpha=0.6, edgecolor='black', linewidth=0.5)
        else:
            # Wrap-around (mis. Nov-Feb)
            ax2.barh(i, 12 - onset + 1, left=onset - 0.5,
                     color=colors_gantt[i], alpha=0.6, edgecolor='black', linewidth=0.5)
            ax2.barh(i, offset, left=0.5,
                     color=colors_gantt[i], alpha=0.6, edgecolor='black', linewidth=0.5)

        # Tandai peak
        ax2.scatter(peak, i, color='red', s=60, zorder=5, marker='D', edgecolors='black')
        # Anotasi
        ax2.text(12.8, i, f"{row['Duration']} bln", va='center', fontsize=8, fontweight='bold')

    ax2.set_yticks(range(len(phen_df)))
    ax2.set_yticklabels(phen_df['WPP'])
    ax2.set_xticks(range(1,13))
    ax2.set_xticklabels([MONTH_NAMES[m] for m in range(1,13)])
    ax2.set_xlabel('Bulan')
    ax2.set_title('Gantt Chart Musim Tangkap per WPP (◆ = Bulan Puncak, Bar = Durasi ≥50% Peak)',
                  fontsize=9)
    ax2.set_xlim(0.3, 13.5)
    ax2.grid(True, axis='x', alpha=0.3)
    ax2.invert_yaxis()

    plt.tight_layout()
    out = os.path.join(F8_DIR, 'F2_phenology.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# F4: FISHING INTENSITY INDEX
# ============================================================
def vis_F4():
    print("\n[4/6] F4 -- Fishing Intensity Index...")
    t = time.time()

    yearly = pd.read_csv(YEARLY)
    yearly = yearly[(yearly['is_partial_year'] == 0) & yearly['wpp'].isin(WPP_ORDER)]

    # Indeks Intensitas = detection_count × rad_mean (Volume × Kecerahan)
    yearly['intensity_index'] = yearly['detection_count'] * yearly['rad_mean']
    yearly['log_intensity']   = np.log10(yearly['intensity_index'] + 1)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(
        'F4 · Fishing Intensity Index — Indeks Komposit Penangkapan Ikan\n'
        'FII = Detection Count × Radiance Mean (Volume Kapal × Skala Operasi)',
        fontsize=11, fontweight='bold', y=1.01)

    # Panel kiri: Heatmap FII per WPP per tahun
    ax = axes[0]
    pivot = yearly.pivot_table(index='wpp', columns='year', values='log_intensity', aggfunc='sum')
    pivot = pivot.reindex(WPP_ORDER)
    pivot.index = [WPP_SHORT[w] for w in pivot.index]
    sns.heatmap(pivot, cmap='YlOrRd', ax=ax, linewidths=0.3,
                cbar_kws={'label': 'log₁₀(FII)'}, annot=False)
    ax.set_title('Heatmap FII per WPP per Tahun', fontsize=9)
    ax.set_xlabel('Tahun')
    ax.set_ylabel('WPP')
    ax.tick_params(axis='x', rotation=45, labelsize=7)

    # Panel kanan: Line trend FII nasional + top 3 WPP
    ax2 = axes[1]
    ax2.set_facecolor('#FAFAFA')
    national = yearly.groupby('year')['intensity_index'].sum()
    ax2.plot(national.index, np.log10(national.values + 1), marker='o', linewidth=2.5,
             color='#2C3E50', label='Nasional', zorder=5)

    top3 = yearly.groupby('wpp')['intensity_index'].sum().nlargest(3).index
    colors_top = ['#E74C3C', '#3498DB', '#27AE60']
    for wpp, color in zip(top3, colors_top):
        sub = yearly[yearly['wpp'] == wpp].groupby('year')['intensity_index'].sum()
        ax2.plot(sub.index, np.log10(sub.values + 1), marker='s', linewidth=1.5,
                 color=color, label=WPP_SHORT[wpp], alpha=0.8, linestyle='--')

    ax2.set_xlabel('Tahun')
    ax2.set_ylabel('log₁₀(Fishing Intensity Index)')
    ax2.set_title('Tren FII: Nasional + Top 3 WPP', fontsize=9)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out = os.path.join(F8_DIR, 'F4_intensity_index.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# F5: RECURRING HOTSPOT
# ============================================================
def vis_F5():
    print("\n[5/6] F5 -- Recurring Hotspot...")
    t = time.time()

    df = pd.read_csv(GRID_L2, usecols=['lat_grid','lon_grid','freq_days',
                                        'is_L4','is_L5','is_L6'],
                     dtype={'lat_grid':'float32','lon_grid':'float32',
                            'freq_days':'float32','is_L4':'int8',
                            'is_L5':'int8','is_L6':'int8'})

    # "Recurring" = titik yang muncul di L4+ DAN memiliki freq_days tinggi
    # Buat skor recurring: freq_days × (1 + is_L4 + is_L5 + is_L6)
    df['recur_score'] = df['freq_days'] * (1 + df['is_L4'] + df['is_L5'] + df['is_L6'])

    # Hanya L4+
    hotspots = df[df['is_L4'] == 1].copy()

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(
        'F5 · Recurring Hotspot Analysis — Stabilitas Daerah Tangkap Ikan\n'
        'Kombinasi Frekuensi Hari (Persistensi) × Tier Level (L4/L5/L6)',
        fontsize=11, fontweight='bold', y=1.01)

    # Panel kiri: Peta recurring score
    ax = axes[0]
    ax.set_facecolor('#0D2137')
    # Background L2
    bg = df.sample(n=min(50_000, len(df)), random_state=42)
    ax.scatter(bg['lon_grid'], bg['lat_grid'], c='#1A3A52', s=0.05, alpha=0.3)

    sc = ax.scatter(hotspots['lon_grid'], hotspots['lat_grid'],
                    c=np.log1p(hotspots['recur_score']),
                    cmap='plasma', s=0.8, alpha=0.85, vmin=3, vmax=8)
    format_map(ax, 'Peta Skor Rekurensi Hotspot (L4+ Area)')
    cb = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label('log(1 + Recurrence Score)', fontsize=8)

    # Panel kanan: Distribusi skor per tier
    ax2 = axes[1]
    ax2.set_facecolor('#FAFAFA')
    tier_data = []
    for label, mask_col in [('L4 Only', 'l4_only'), ('L5 Only', 'l5_only'), ('L6', 'is_L6')]:
        if label == 'L4 Only':
            sub = df[(df['is_L4']==1) & (df['is_L5']==0)]
        elif label == 'L5 Only':
            sub = df[(df['is_L5']==1) & (df['is_L6']==0)]
        else:
            sub = df[df['is_L6']==1]
        if len(sub) > 0:
            tier_data.append({'Tier': label, 'N': len(sub),
                              'Median Score': sub['recur_score'].median(),
                              'Mean Score': sub['recur_score'].mean(),
                              'Max Score': sub['recur_score'].max()})

    tier_df = pd.DataFrame(tier_data)
    x = np.arange(len(tier_df))
    width = 0.25
    ax2.bar(x - width, tier_df['N'], width, label='Jumlah Piksel', color='#3498DB', alpha=0.8)
    ax2_r = ax2.twinx()
    ax2_r.bar(x, tier_df['Median Score'], width, label='Median Score', color='#E67E22', alpha=0.8)
    ax2_r.bar(x + width, tier_df['Mean Score'], width, label='Mean Score', color='#E74C3C', alpha=0.8)

    ax2.set_xticks(x)
    ax2.set_xticklabels(tier_df['Tier'])
    ax2.set_ylabel('Jumlah Piksel', color='#3498DB')
    ax2_r.set_ylabel('Recurrence Score', color='#E74C3C')
    ax2.set_title('Statistik Rekurensi per Tier (L4/L5/L6)', fontsize=9)

    # Combined legend
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2_r.get_legend_handles_labels()
    ax2.legend(h1+h2, l1+l2, fontsize=8, loc='upper left')
    ax2.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    out = os.path.join(F8_DIR, 'F5_recurring_hotspot.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# F6: VESSEL ACTIVITY EVOLUTION
# ============================================================
def vis_F6():
    print("\n[6/6] F6 -- Vessel Activity Evolution...")
    t = time.time()

    yearly = pd.read_csv(YEARLY)
    yearly = yearly[(yearly['is_partial_year'] == 0) & yearly['wpp'].isin(WPP_ORDER)]

    # Klasifikasi kelas armada berdasarkan rad_mean per WPP per tahun
    # Tradisional: rad_mean < 5, Menengah: 5-20, Industri: > 20
    def armada_class(rad):
        if rad < 5:  return 'Tradisional (<5 nW)'
        if rad < 20: return 'Menengah (5–20 nW)'
        return 'Industri (>20 nW)'

    yearly['armada'] = yearly['rad_mean'].apply(armada_class)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(
        'F6 · Vessel Activity Evolution — Evolusi Komposisi Armada Penangkapan\n'
        'Perubahan Profil Kecerahan Kapal (Tradisional vs Menengah vs Industri) per Tahun',
        fontsize=11, fontweight='bold', y=1.01)

    # Panel kiri: Stacked Area Chart (proporsi)
    ax = axes[0]
    ax.set_facecolor('#FAFAFA')
    class_order = ['Tradisional (<5 nW)', 'Menengah (5–20 nW)', 'Industri (>20 nW)']
    colors_class = ['#3498DB', '#F39C12', '#E74C3C']

    # Hitung jumlah WPP per kelas per tahun
    class_counts = yearly.groupby(['year','armada']).size().unstack(fill_value=0)
    for c in class_order:
        if c not in class_counts: class_counts[c] = 0
    class_counts = class_counts[class_order]

    # Normalisasi ke 100%
    totals = class_counts.sum(axis=1)
    class_pct = class_counts.div(totals, axis=0) * 100

    ax.stackplot(class_pct.index, [class_pct[c] for c in class_order],
                 labels=class_order, colors=colors_class, alpha=0.8)
    ax.set_xlabel('Tahun')
    ax.set_ylabel('Proporsi WPP (%)')
    ax.set_title('Evolusi Komposisi Kelas Armada per Tahun', fontsize=9)
    ax.legend(loc='center right', fontsize=8)
    ax.set_ylim(0, 100)
    ax.grid(True, axis='y', alpha=0.3)

    # Panel kanan: Heatmap radiance per WPP per tahun
    ax2 = axes[1]
    pivot_rad = yearly.pivot_table(index='wpp', columns='year', values='rad_mean')
    pivot_rad = pivot_rad.reindex(WPP_ORDER)
    pivot_rad.index = [WPP_SHORT[w] for w in pivot_rad.index]
    sns.heatmap(pivot_rad, cmap='YlOrRd', ax=ax2, linewidths=0.3,
                annot=True, fmt='.0f', annot_kws={'fontsize': 6},
                cbar_kws={'label': 'Radiance Mean (nW/cm²/sr)'})
    ax2.set_title('Evolusi Radiance per WPP per Tahun', fontsize=9)
    ax2.set_xlabel('Tahun')
    ax2.set_ylabel('WPP')
    ax2.tick_params(axis='x', rotation=45, labelsize=7)

    plt.tight_layout()
    out = os.path.join(F8_DIR, 'F6_vessel_evolution.png')
    plt.savefig(out, facecolor='white')
    plt.close()
    print(f"  Tersimpan: {out} ({time.time()-t:.1f}s)")
    return out


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    results = {}
    results['E2'] = vis_E2()
    results['E6'] = vis_E6()
    results['F2'] = vis_F2()
    results['F4'] = vis_F4()
    results['F5'] = vis_F5()
    results['F6'] = vis_F6()

    elapsed = time.time() - t0
    print()
    print("=" * 68)
    print(f"FASE 8 SELESAI -- {elapsed:.0f} detik")
    print("=" * 68)
    for code, path in results.items():
        status = "OK" if path else "SKIP"
        print(f"  [{status}] {code}: {os.path.basename(path) if path else '-'}")
    print(f"\nSemua gambar di: {F8_DIR}")
    print("=" * 68)
