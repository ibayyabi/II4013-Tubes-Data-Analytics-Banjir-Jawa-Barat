# II4013 Tubes Data Analytics - Banjir Jawa Barat

Repositori ini berisi pipeline data analytics untuk menganalisis kejadian banjir di Jawa Barat. Proyek mencakup pengambilan data, pembersihan, penggabungan dataset, feature engineering, klasterisasi kerentanan wilayah, dan dashboard Streamlit.

## Tujuan

Membangun dataset terintegrasi tingkat kabupaten/kota di Jawa Barat untuk melihat hubungan antara kejadian banjir, cuaca historis, dampak bencana, timbulan sampah, dan indikator risiko pendukung.

Kunci wilayah utama yang digunakan adalah kode Kemendagri 4 digit, misalnya:

- `3201` = Kabupaten Bogor
- `3273` = Kota Bandung
- `3279` = Kota Banjar

## Struktur Folder

```text
.
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── raw/
│   │   ├── api_opendata_jabar/
│   │   ├── cuaca_raw/
│   │   ├── cuaca_raw_backup_2024_2025_before_merge/
│   │   ├── IRBIJABAR/
│   │   ├── 200_dampak_bencana.csv
│   │   ├── banjir_desa_opendata_jabar.csv
│   │   ├── banjir_kab_opendata_jabar.csv
│   │   ├── grafisk-potensi-banjir-jABAR.csv
│   │   ├── IRBIJABAR.csv
│   │   ├── Jabar_By_Desa.geojson
│   │   ├── Jabar_By_Kab.geojson
│   │   ├── Jabar_By_Kec.geojson
│   │   └── sampah_opendata_jabar.csv
│   ├── reference/
│   │   ├── Jabar_By_Kab.geojson
│   │   └── master_wilayah_jabar.csv
│   ├── clean/
│   │   ├── banjir_tahunan.csv
│   │   ├── cuaca_bulanan.csv
│   │   ├── dampak_clean.csv
│   │   ├── master_merged.csv
│   │   └── sampah_tahunan.csv
│   └── processed/
│       ├── MASTER_MERGED_CLEANED_DASHBOARD.csv
│       ├── MASTER_MERGED_CLEANED_DASHBOARD.xlsx
│       ├── flood-analytics-jabar.xlsx
│       ├── cluster_profile.csv
│       ├── cluster_tahunan_2015_2023.csv
│       └── cluster_wilayah_summary.csv
├── docs/
├── notebooks/
├── src/
└── tests/
```

## Peran Folder

| Folder | Isi |
|---|---|
| `data/raw/` | Data mentah dari Open Data Jabar, Open-Meteo, BNPB/DIBI, GeoJSON, dan sumber pendukung lain. |
| `data/reference/` | Data referensi wilayah dan batas administrasi yang dipakai untuk standardisasi dan visualisasi peta. |
| `data/clean/` | Hasil pembersihan dan agregasi awal dari masing-masing sumber data. |
| `data/processed/` | Dataset akhir untuk dashboard, file Excel hasil ekspor, dan output klasterisasi. |
| `src/` | Skrip pipeline data dari akuisisi sampai validasi dan klasterisasi. |
| `notebooks/` | Notebook eksplorasi, preprocessing, dan eksperimen klasterisasi. |
| `docs/` | Catatan teknis, rencana, dan spesifikasi pengembangan. |
| `tests/` | Test untuk dashboard dan pipeline analitik. |

## Dataset Utama

Dataset utama untuk dashboard:

```text
data/processed/MASTER_MERGED_CLEANED_DASHBOARD.csv
```

Dataset ini merupakan versi siap pakai dari `data/clean/master_merged.csv` yang sudah disesuaikan untuk kebutuhan visualisasi dan klasterisasi.

Output klasterisasi:

```text
data/processed/cluster_tahunan_2015_2023.csv
data/processed/cluster_wilayah_summary.csv
data/processed/cluster_profile.csv
```

File Excel hasil ekspor:

```text
data/processed/flood-analytics-jabar.xlsx
data/processed/MASTER_MERGED_CLEANED_DASHBOARD.xlsx
```

## Ringkasan Data

| Dataset | Lokasi | Rentang tahun |
|---|---|---:|
| Kejadian banjir kabupaten/kota | `data/raw/banjir_kab_opendata_jabar.csv` | 2012-2025 |
| Kejadian banjir desa/kelurahan | `data/raw/banjir_desa_opendata_jabar.csv` | 2019-2024 |
| Cuaca historis Open-Meteo | `data/raw/cuaca_raw/` | 2012-2023 |
| Dampak bencana banjir | `data/raw/200_dampak_bencana.csv` | 2008-2026 |
| Timbulan sampah | `data/raw/sampah_opendata_jabar.csv` | 2015-2023 |
| IRBI Jawa Barat | `data/raw/IRBIJABAR.csv` | 2015-2024 |
| Master gabungan | `data/clean/master_merged.csv` | 2008-2026 |
| Dataset dashboard | `data/processed/MASTER_MERGED_CLEANED_DASHBOARD.csv` | 2015-2023 untuk analisis utama |

Periode yang paling stabil untuk analisis lintas variabel adalah `2015-2023`, karena data banjir, cuaca, sampah, dan sebagian besar data dampak tersedia pada rentang tersebut.

## Cara Menjalankan

Install dependency:

```bash
pip install -r requirements.txt
```

Bangun ulang data clean:

```bash
python src/05_build_clean_data.py
```

Tambahkan fitur analitik untuk dashboard:

```bash
python src/07_feature_engineering.py
```

Ekspor workbook Excel:

```bash
python src/08_export_excel.py
```

Validasi output:

```bash
python src/09_validate_outputs.py
```

Jalankan klasterisasi:

```bash
python src/10_cluster_kerentanan_banjir.py
```

Jalankan dashboard Streamlit:

```bash
streamlit run app.py
```

## Pipeline

Urutan pipeline utama:

1. `src/01a_fetch_banjir_kab_opendata_api.py` mengambil data banjir kabupaten/kota dari API Open Data Jabar.
2. `src/02_ingest_cuaca_openmeteo.py` mengambil data cuaca historis dari Open-Meteo.
3. `src/05_build_clean_data.py` membersihkan dan menggabungkan data mentah menjadi dataset clean.
4. `src/07_feature_engineering.py` membuat fitur tambahan untuk kebutuhan dashboard.
5. `src/08_export_excel.py` mengekspor data ke workbook Excel di `data/processed/`.
6. `src/09_validate_outputs.py` memeriksa konsistensi output.
7. `src/10_cluster_kerentanan_banjir.py` membuat segmentasi kerentanan banjir per wilayah.

## Catatan Missing Value

Nilai kosong pada dataset gabungan tidak selalu berarti nol. Penyebab utamanya adalah perbedaan cakupan tahun antar sumber data:

- Data cuaca tersedia sampai 2023 pada pipeline saat ini.
- Data sampah tersedia untuk 2015-2023.
- Data dampak bencana tidak selalu lengkap untuk setiap wilayah dan tahun.
- Data banjir Open Data Jabar tersedia sampai 2025.

Jika nilai kosong pada data dampak ingin diisi nol, asumsi metodologinya perlu ditulis jelas dalam laporan atau dashboard.

## Dashboard

Dashboard membaca file berikut:

```text
data/processed/MASTER_MERGED_CLEANED_DASHBOARD.csv
data/processed/cluster_wilayah_summary.csv
data/processed/cluster_tahunan_2015_2023.csv
data/processed/cluster_profile.csv
data/reference/Jabar_By_Kab.geojson
data/clean/cuaca_bulanan.csv
data/raw/grafisk-potensi-banjir-jABAR.csv
```

Jika dashboard gagal berjalan, pastikan file-file di atas sudah tersedia dan jalankan ulang pipeline sesuai urutan.

## Status Pengembangan

Sudah tersedia:

- Data mentah dan referensi wilayah Jawa Barat.
- Data clean untuk banjir, cuaca, dampak bencana, dan sampah.
- Dataset dashboard di `data/processed/`.
- Output klasterisasi kerentanan banjir.
- Dashboard Streamlit.
- Test dasar untuk dashboard dan klasterisasi.

Pengembangan lanjutan yang masih bisa dilakukan:

- Integrasi IRBI ke dataset utama.
- Integrasi data potensi bahaya banjir ke fitur analitik utama.
- Pembaruan data cuaca setelah 2023.
- Penyempurnaan asumsi missing value untuk laporan akhir.
