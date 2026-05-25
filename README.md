# II4013 Tubes Data Analytics — Banjir Jawa Barat

Repositori ini berisi persiapan data untuk analitik banjir di Jawa Barat. Fokus pekerjaan saat ini adalah akuisisi, pembersihan, standarisasi, dan penggabungan data dari beberapa sumber menjadi dataset siap analisis.

## Tujuan

Membangun dataset terintegrasi berbasis wilayah kabupaten/kota di Jawa Barat untuk mendukung analisis hubungan antara kejadian banjir, cuaca historis, dampak bencana, dan faktor pendukung lain seperti timbulan sampah.

Primary key lintas dataset menggunakan kode wilayah Kemendagri 4 digit, misalnya:

- `3201` = Kabupaten Bogor
- `3273` = Kota Bandung
- `3279` = Kota Banjar

## Struktur Data

```text
data/
├── raw/
│   ├── banjir_kab_opendata_jabar.csv
│   ├── banjir_desa_opendata_jabar.csv
│   ├── sampah_opendata_jabar.csv
│   ├── 200_dampak_bencana.csv
│   ├── IRBIJABAR.csv
│   ├── grafisk-potensi-banjir-jABAR.csv
│   ├── Jabar_By_Kab.geojson
│   ├── Jabar_By_Kec.geojson
│   ├── Jabar_By_Desa.geojson
│   └── cuaca_raw/
│       ├── 3201_bogor.json
│       ├── 3202_sukabumi.json
│       └── ... 27 file JSON
├── reference/
│   ├── master_wilayah_jabar.csv
│   └── Jabar_By_Kab.geojson
└── clean/
    ├── banjir_tahunan.csv
    ├── cuaca_bulanan.csv
    ├── dampak_clean.csv
    ├── sampah_tahunan.csv
    └── master_merged.csv
```

## Dokumentasi Data Mentah

### 1. Data kejadian banjir kabupaten/kota

File:

```text
data/raw/banjir_kab_opendata_jabar.csv
```

Sumber: Open Data Jawa Barat.

Isi data:

- Jumlah kejadian bencana banjir per kabupaten/kota.
- Level agregasi: kabupaten/kota per tahun.
- Rentang tahun tersedia di data saat ini: **2012–2025**.
- Jumlah baris: **378**.

Kolom utama:

- `kode_kabupaten_kota`
- `nama_kabupaten_kota`
- `jumlah_banjir`
- `tahun`

Catatan:

- Dataset ini menjadi sumber utama variabel target kejadian banjir.
- Data 2024–2025 tersedia di file mentah, tetapi belum tentu semua dataset lain memiliki rentang tahun yang sama.

### 2. Data kejadian banjir desa/kelurahan

File:

```text
data/raw/banjir_desa_opendata_jabar.csv
```

Sumber: Open Data Jawa Barat.

Isi data:

- Jumlah kejadian banjir pada level desa/kelurahan.
- Rentang tahun tersedia: **2019–2024**.
- Jumlah baris: **31.870**.

Catatan:

- Data ini berguna untuk analisis spasial lebih detail.
- Dalam pipeline saat ini, data utama yang digunakan untuk `master_merged.csv` adalah data banjir level kabupaten/kota, bukan level desa.

### 3. Data cuaca historis

Folder:

```text
data/raw/cuaca_raw/
```

Sumber: Open-Meteo Archive API.

Endpoint:

```text
https://archive-api.open-meteo.com/v1/archive
```

Isi data:

- 27 file JSON, satu file untuk setiap kabupaten/kota di Jawa Barat.
- Rentang waktu yang diambil saat ini: **2012-01-01 sampai 2023-12-31**.
- Level data mentah: harian dan hourly.

Variabel harian:

- `precipitation_sum`
- `rain_sum`
- `precipitation_hours`
- `wind_gusts_10m_max`
- `et0_fao_evapotranspiration`

Variabel hourly:

- `soil_moisture_0_to_7cm`

Catatan situasi nyata:

- Data cuaca hanya sampai 2023 karena mengikuti rancangan awal PRD, bukan karena pasti terbatas oleh API.
- Open-Meteo kemungkinan dapat menyediakan data setelah 2023, tetapi perlu dilakukan penarikan ulang dengan `END_DATE` yang lebih baru dan validasi ketersediaan variabel.
- Variabel `soil_moisture_0_to_7cm` tidak tersedia sebagai variabel harian pada API Open-Meteo Archive. Karena itu, variabel ini diambil sebagai data hourly, lalu diagregasi menjadi rata-rata harian dan bulanan.

### 4. Data dampak bencana BNPB/DIBI

File:

```text
data/raw/200_dampak_bencana.csv
```

Sumber: BNPB/DIBI atau rekap dampak bencana yang tersedia.

Isi data:

- Data kejadian dan dampak bencana di Jawa Barat.
- Rentang tahun tersedia: **2008–2026**.
- Jumlah baris mentah: **2.243**.
- Dalam pipeline clean, data difilter hanya untuk `Jenis Bencana = Banjir`.

Kolom dampak utama:

- `Jumlah Kejadian`
- `Meninggal`
- `Hilang`
- `Luka / Sakit`
- `menderita_mengungsi`
- `Rumah Rusak Berat`
- `Rumah Rusak Sedang`
- `Rumah Rusak Ringan`
- `Rumah Terendam`
- `Satuan Pendidikan Rusak`
- `Rumah Ibadat Rusak`
- `Fasilitas Pelayanan Kesehatan Rusak`
- `Kantor Rusak`
- `Jembatan Rusak`

Catatan situasi nyata:

- Data dampak bencana tidak selalu lengkap untuk setiap kombinasi wilayah dan tahun.
- Nilai kosong pada hasil join tidak selalu berarti tidak ada dampak. Nilai kosong dapat berarti data tidak tercatat, tidak tersedia, atau tidak ada kejadian yang dilaporkan.
- Karena itu, interpretasi `null` pada variabel dampak harus hati-hati.
- Untuk analisis yang membutuhkan angka lengkap, dapat digunakan asumsi metodologis bahwa tidak adanya catatan kejadian berarti nilai dampak nol. Namun asumsi ini harus ditulis eksplisit dalam laporan.

### 5. Data sampah tahunan

File:

```text
data/raw/sampah_opendata_jabar.csv
```

Sumber: Open Data Jawa Barat.

Isi data:

- Data jumlah sampah per kabupaten/kota per tahun.
- Rentang tahun tersedia: **2015–2023**.
- Jumlah baris: **243**.

Kolom utama:

- `kode_kabupaten_kota`
- `nama_kabupaten_kota`
- `jumlah_sampah`
- `satuan`
- `tahun`

Catatan:

- Rentang data sampah lebih pendek dibanding data banjir dan dampak bencana.
- Ini menyebabkan nilai kosong pada `master_merged.csv` untuk tahun di luar 2015–2023.

### 6. Data IRBI

File:

```text
data/raw/IRBIJABAR.csv
```

Isi data:

- Indeks Risiko Bencana Indonesia untuk kabupaten/kota di Jawa Barat.
- Rentang tahun tersedia: **2015–2024**.
- Jumlah baris: **270**.

Catatan:

- Data ini sudah tersedia sebagai data pendukung.
- Saat ini belum dimasukkan ke `master_merged.csv`.
- Dapat digunakan untuk pengembangan fitur lanjutan.

### 7. Data risiko/potensi banjir

File:

```text
data/raw/grafisk-potensi-banjir-jABAR.csv
```

Isi data:

- Potensi bahaya banjir per wilayah.
- Kolom mencakup luas bahaya, jiwa terpapar, estimasi kerugian fisik, ekonomi, dan lingkungan.

Catatan:

- Data ini bersifat pendukung.
- Saat ini belum dimasukkan ke `master_merged.csv`.

### 8. Data spasial GeoJSON

File mentah:

```text
data/raw/Jabar_By_Kab.geojson
data/raw/Jabar_By_Kec.geojson
data/raw/Jabar_By_Desa.geojson
```

File referensi utama:

```text
data/reference/Jabar_By_Kab.geojson
```

Catatan:

- GeoJSON kabupaten/kota sudah disalin ke folder `data/reference/`.
- File ini dapat digunakan untuk peta di Looker Studio, GIS, atau validasi spasial.

## Dokumentasi Data Referensi

### Master wilayah Jawa Barat

File:

```text
data/reference/master_wilayah_jabar.csv
```

Isi:

- 27 wilayah kabupaten/kota Jawa Barat.
- 18 kabupaten dan 9 kota.

Kolom:

- `kode_kemendagri`
- `nama_clean`
- `nama_singkat`
- `tipe`
- `latitude`
- `longitude`
- `bps_kode`

Fungsi:

- Menjadi referensi utama untuk standardisasi nama wilayah.
- Menjadi sumber koordinat untuk request data cuaca Open-Meteo.
- Menjadi basis join antar dataset.

## Dokumentasi Data Bersih

### 1. `banjir_tahunan.csv`

Path:

```text
data/clean/banjir_tahunan.csv
```

Isi:

- Agregasi jumlah kejadian banjir per kabupaten/kota per tahun.
- Sumber: `banjir_kab_opendata_jabar.csv`.

Ukuran data saat ini:

- Rows: **378**
- Wilayah: **27**
- Tahun: **2012–2025**

Kolom utama:

- `kode_kemendagri`
- `nama_clean`
- `tipe`
- `tahun`
- `jumlah_banjir`

### 2. `cuaca_bulanan.csv`

Path:

```text
data/clean/cuaca_bulanan.csv
```

Isi:

- Agregasi cuaca bulanan per kabupaten/kota.
- Sumber: 27 file JSON Open-Meteo di `data/raw/cuaca_raw/`.

Ukuran data saat ini:

- Rows: **3.888**
- Wilayah: **27**
- Tahun: **2012–2023**

Kolom fitur utama:

- `precipitation_sum_mm`
- `rain_sum_mm`
- `precipitation_hours_total`
- `rainy_days`
- `heavy_rain_days_50mm`
- `max_daily_precipitation_mm`
- `wind_gusts_10m_max_kmh`
- `et0_fao_evapotranspiration_mm_avg`
- `soil_moisture_0_to_7cm_avg`
- `rain_intensity_mm_per_hour_avg`

### 3. `dampak_clean.csv`

Path:

```text
data/clean/dampak_clean.csv
```

Isi:

- Agregasi dampak bencana banjir per kabupaten/kota per tahun.
- Sumber: `200_dampak_bencana.csv`.
- Filter: hanya baris dengan `Jenis Bencana = Banjir`.

Ukuran data saat ini:

- Rows: **390**
- Wilayah: **27**
- Tahun: **2008–2026**

Catatan:

- Tidak semua wilayah-tahun memiliki catatan dampak.
- Missing value pada hasil gabungan harus dibedakan antara tidak ada kejadian dan tidak ada data.

### 4. `sampah_tahunan.csv`

Path:

```text
data/clean/sampah_tahunan.csv
```

Isi:

- Agregasi jumlah sampah per kabupaten/kota per tahun.
- Sumber: `sampah_opendata_jabar.csv`.

Ukuran data saat ini:

- Rows: **243**
- Wilayah: **27**
- Tahun: **2015–2023**

### 5. `master_merged.csv`

Path:

```text
data/clean/master_merged.csv
```

Isi:

- Dataset gabungan tahunan lintas sumber.
- Level agregasi: kabupaten/kota per tahun.
- Join key: `kode_kemendagri` dan `tahun`.

Ukuran data saat ini:

- Rows: **469**
- Wilayah: **27**
- Tahun: **2008–2026**

Sumber yang digabung:

- Data banjir tahunan.
- Data cuaca, diagregasi dari bulanan ke tahunan.
- Data dampak bencana banjir.
- Data sampah tahunan.
- Referensi master wilayah.

## Situasi Nyata dan Keterbatasan Data

Dataset gabungan saat ini memiliki nilai `null` karena rentang tahun antar sumber tidak sama.

Ringkasan rentang tahun:

| Dataset | Rentang tahun |
|---|---:|
| Banjir Open Data Jabar | 2012–2025 |
| Cuaca Open-Meteo | 2012–2023 |
| Dampak BNPB/DIBI | 2008–2026 |
| Sampah Open Data Jabar | 2015–2023 |
| IRBI | 2015–2024 |

Dampaknya:

- Tahun 2008–2011 hanya banyak terisi oleh data dampak bencana.
- Tahun 2012–2014 belum memiliki data sampah.
- Tahun 2024–2026 tidak memiliki data cuaca dan sampah pada pipeline saat ini.
- Data dampak bencana tidak selalu tersedia untuk semua wilayah dan tahun.

Karena itu, `null` pada `master_merged.csv` adalah konsekuensi alami dari keterbatasan dan perbedaan cakupan sumber data, bukan semata-mata error pipeline.

## Rekomendasi Penggunaan Data

Untuk analisis lintas variabel yang paling konsisten, gunakan periode:

```text
2015–2023
```

Alasan:

- Data banjir tersedia.
- Data cuaca tersedia.
- Data sampah tersedia.
- Data dampak bencana tersedia sebagian besar.

Untuk analisis historis dampak bencana, gunakan `dampak_clean.csv` secara terpisah karena cakupannya lebih panjang, yaitu 2008–2026.

Untuk analisis utama kejadian banjir, gunakan `banjir_tahunan.csv` sebagai baseline karena data ini paling langsung merepresentasikan target analisis.

## Catatan Metodologi Missing Value

Nilai kosong pada `master_merged.csv` perlu diperlakukan sesuai konteks:

1. Jika kosong karena dataset memang tidak memiliki tahun tersebut, jangan langsung dianggap nol.
2. Jika kosong pada dampak bencana dan asumsi yang digunakan adalah “tidak ada catatan berarti tidak ada kejadian/dampak”, maka nilai dapat diisi nol.
3. Asumsi pengisian nol harus dijelaskan eksplisit dalam laporan atau dashboard.
4. Untuk visualisasi, disarankan menambahkan filter tahun 2015–2023 agar tampilan tidak didominasi nilai kosong.

## Pipeline yang Tersedia

### Ambil data cuaca Open-Meteo

Script:

```text
src/02_ingest_cuaca_openmeteo.py
```

Jalankan:

```bash
python src/02_ingest_cuaca_openmeteo.py
```

Output:

```text
data/raw/cuaca_raw/*.json
```

Catatan:

- Script bersifat idempotent. File JSON yang sudah ada akan di-skip.
- Jika ingin menarik ulang data dengan periode baru, hapus file lama di `data/raw/cuaca_raw/` terlebih dahulu.

### Bangun data clean

Script:

```text
src/05_build_clean_data.py
```

Jalankan:

```bash
python src/05_build_clean_data.py
```

Output:

```text
data/clean/banjir_tahunan.csv
data/clean/cuaca_bulanan.csv
data/clean/dampak_clean.csv
data/clean/sampah_tahunan.csv
data/clean/master_merged.csv
```

## Status Saat Ini

Sudah selesai:

- Master wilayah 27 kabupaten/kota.
- Data mentah banjir kabupaten/kota.
- Data mentah banjir desa/kelurahan.
- Data mentah cuaca Open-Meteo untuk 27 wilayah.
- Data mentah dampak bencana.
- Data mentah sampah.
- GeoJSON kabupaten/kota di folder referensi.
- Data clean utama.
- Dataset gabungan `master_merged.csv`.

Belum dilakukan:

- Export final ke Excel/Google Sheets.
- Integrasi IRBI ke `master_merged.csv`.
- Integrasi data potensi bahaya banjir ke `master_merged.csv`.
- Pembuatan dashboard Looker Studio.

## File Utama untuk Analisis

Gunakan file berikut sebagai input utama:

```text
data/clean/master_merged.csv
```

Untuk analisis yang lebih stabil dan minim missing value, filter tahun:

```text
2015 <= tahun <= 2023
```
