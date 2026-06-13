# Design: Clustering Kerentanan Banjir Berbasis Kapasitas Lingkungan

Tanggal: 2026-06-13

## Tujuan

Membuat segmentasi wilayah kerentanan banjir Jawa Barat menggunakan algoritma machine learning. Cluster tidak hanya melihat faktor cuaca, tetapi juga histori banjir, dampak banjir, dan kapasitas lingkungan yang direpresentasikan oleh timbulan sampah.

Hasil clustering akan digunakan sebagai dasar visualisasi dashboard, terutama choropleth map kabupaten/kota Jawa Barat dengan tiga kategori kerentanan: rendah, sedang, dan tinggi.

## Dataset dan Cakupan

Dataset input utama:

- `MASTER_MERGED_CLEANED_DASHBOARD.csv`

Unit data:

- Kabupaten/kota Jawa Barat per tahun
- Primary key: `kode_kemendagri` + `tahun`

Periode model utama:

- 2015–2023

Alasan periode:

- Kolom `jumlah_sampah_ton_per_tahun` lengkap untuk 27 wilayah pada 2015–2023.
- Periode ini menjaga analisis kapasitas lingkungan tetap berbasis data aktual tanpa imputasi tahun awal.

## Pendekatan Model

Model utama menggunakan KMeans dengan `n_clusters=3`.

Alasan pemilihan:

- Dataset kecil dan tabular.
- Output mudah dijelaskan di dashboard.
- Jumlah cluster sesuai kebutuhan narasi: rendah, sedang, tinggi.
- KMeans mudah direproduksi dan divalidasi dengan metrik seperti silhouette score.

Alternatif yang dipertimbangkan:

1. Hierarchical clustering: baik untuk melihat kemiripan antarwilayah, tetapi kurang praktis untuk pipeline dashboard tahunan.
2. Gaussian Mixture Model: dapat memberi probabilitas keanggotaan cluster, tetapi interpretasinya lebih berat untuk dashboard publik.

## Fitur Clustering

Fitur model menggabungkan tiga kelompok faktor.

### Faktor histori banjir

- `jumlah_banjir`
- `jumlah_kejadian_bnpb`
- `rasio_banjir_per_hujan`

### Faktor cuaca dan runoff

- `total_hujan_tahunan_mm`
- `rainy_days`
- `total_hari_hujan_ekstrem`
- `max_hujan_harian_mm`
- `rain_intensity_mm_per_hour_avg`
- `avg_kelembaban_tanah`
- `et0_fao_evapotranspiration_mm_avg`

### Faktor kapasitas lingkungan

- `jumlah_sampah_ton_per_tahun`

Catatan arah risiko:

- Nilai tinggi pada banjir, hujan ekstrem, intensitas hujan, kelembaban tanah, dan sampah diasumsikan meningkatkan kerentanan.
- Nilai tinggi pada `et0_fao_evapotranspiration_mm_avg` diasumsikan menunjukkan kapasitas pengeringan lebih baik, sehingga arahnya dibalik saat menghitung skor kerentanan komposit.

## Pra-pemrosesan

Langkah pra-pemrosesan:

1. Filter data ke tahun 2015–2023.
2. Pilih kolom identitas wilayah, koordinat, tahun, dan fitur model.
3. Pastikan `kode_kemendagri` disimpan sebagai teks 4 digit untuk kebutuhan join dashboard.
4. Tangani nilai hilang pada fitur model dengan aturan eksplisit:
   - Jika nilai hilang minor pada fitur cuaca atau dampak, gunakan median per fitur.
   - Jangan imputasi `jumlah_sampah_ton_per_tahun` di luar periode 2015–2023 karena model utama sudah difilter ke periode lengkap.
5. Skala semua fitur numerik dengan `StandardScaler`.
6. Jalankan KMeans 3 cluster dengan `random_state` tetap agar hasil reproduktif.

## Interpretasi Cluster

Nomor cluster mentah dari KMeans tidak dipakai langsung sebagai label dashboard.

Setiap cluster diberi skor kerentanan komposit berdasarkan rata-rata fitur yang sudah diskalakan, dengan arah risiko dibuat konsisten. Cluster dengan skor terendah diberi label `Rendah`, skor tengah `Sedang`, dan skor tertinggi `Tinggi`.

Label dashboard:

- `Rendah`
- `Sedang`
- `Tinggi`

Validasi interpretasi dilakukan dengan melihat profil rata-rata fitur per cluster. Cluster `Tinggi` harus menunjukkan kombinasi faktor risiko yang lebih berat dibanding cluster `Rendah`.

## Output Data

Pipeline menghasilkan tiga file utama.

### `data/processed/cluster_tahunan_2015_2023.csv`

Satu baris per wilayah per tahun.

Kolom utama:

- `kode_kemendagri`
- `nama_clean`
- `tahun`
- `lat`
- `lon`
- fitur model terpilih
- `cluster_id_raw`
- `cluster_label`
- `skor_kerentanan`

Kegunaan:

- Tren cluster tahunan.
- Filter dashboard berdasarkan tahun.
- Analisis perubahan kerentanan tiap wilayah.

### `data/processed/cluster_wilayah_summary.csv`

Satu baris per wilayah, hasil agregasi periode 2015–2023.

Kolom utama:

- `kode_kemendagri`
- `nama_clean`
- `lat`
- `lon`
- `cluster_dominan`
- `cluster_label`
- `skor_kerentanan_rata2`
- `avg_jumlah_banjir`
- `avg_total_hari_hujan_ekstrem`
- `avg_jumlah_sampah_ton_per_tahun`

Kegunaan:

- Sumber utama choropleth map dashboard.
- Ranking wilayah paling rentan.

### `data/processed/cluster_profile.csv`

Satu baris per cluster label.

Kolom utama:

- `cluster_label`
- jumlah observasi
- rata-rata fitur utama
- ringkasan interpretasi cluster

Kegunaan:

- Panel profil cluster di dashboard.
- Narasi mengapa cluster disebut rendah, sedang, atau tinggi.

## Desain Dashboard

Dashboard menampilkan empat komponen utama.

### 1. Choropleth map kerentanan wilayah

Sumber data:

- `cluster_wilayah_summary.csv`
- GeoJSON kabupaten/kota Jawa Barat

Join key:

- `kode_kemendagri` sebagai teks 4 digit

Skema warna sequential orange-red:

- `Rendah`: `#FEE8C8`
- `Sedang`: `#FDBB84`
- `Tinggi`: `#E34A33`

Tooltip:

- `nama_clean`
- `cluster_label`
- `skor_kerentanan_rata2`
- `cluster_dominan`
- `avg_jumlah_banjir`
- `avg_total_hari_hujan_ekstrem`
- `avg_jumlah_sampah_ton_per_tahun`

Default peta:

- Summary wilayah periode 2015–2023 agar peta stabil dan mudah dibaca.

### 2. Tren cluster tahunan

Sumber data:

- `cluster_tahunan_2015_2023.csv`

Visual:

- Stacked bar jumlah wilayah per cluster per tahun, atau line chart jumlah wilayah berdasarkan label cluster.

Pertanyaan yang dijawab:

- Apakah jumlah wilayah rentan tinggi meningkat atau menurun dari waktu ke waktu?

### 3. Ranking wilayah paling rentan

Sumber data:

- `cluster_wilayah_summary.csv`

Visual:

- Bar chart top 10 berdasarkan `skor_kerentanan_rata2`.

Metric pendukung:

- rata-rata jumlah banjir
- rata-rata hari hujan ekstrem
- rata-rata sampah tahunan

### 4. Profil cluster

Sumber data:

- `cluster_profile.csv`

Visual:

- Tabel atau grouped bar chart rata-rata fitur utama per cluster.

Pertanyaan yang dijawab:

- Apa karakteristik cluster rendah, sedang, dan tinggi?

## Validasi Model

Validasi yang wajib dilakukan:

1. Hitung `silhouette_score` untuk memeriksa separasi cluster.
2. Buat ringkasan rata-rata fitur per cluster.
3. Pastikan urutan label rendah-sedang-tinggi sesuai skor kerentanan komposit.
4. Periksa jumlah wilayah per cluster agar tidak ada cluster kosong atau terlalu timpang tanpa alasan data.
5. Cek peta secara visual: wilayah cluster tinggi harus masuk akal berdasarkan histori banjir, hujan ekstrem, dan faktor sampah.

## Batasan

- Cluster bukan prediksi kejadian banjir masa depan. Cluster adalah segmentasi historis berdasarkan data 2015–2023.
- Karena pengguna memilih memasukkan histori banjir ke fitur model, cluster merepresentasikan gabungan kerentanan lingkungan dan rekam kejadian banjir, bukan kapasitas lingkungan murni.
- Timbulan sampah dipakai sebagai proksi kapasitas lingkungan. Interpretasi perlu hati-hati karena sampah bukan satu-satunya faktor drainase atau daya dukung wilayah.
- Model bekerja pada level kabupaten/kota, sehingga variasi kerentanan di level kecamatan atau desa tidak tertangkap.

## Kriteria Sukses

Desain dianggap berhasil jika:

- File output cluster tahunan, summary wilayah, dan profil cluster terbentuk.
- Setiap wilayah memiliki label cluster untuk peta choropleth.
- Label rendah, sedang, tinggi dapat dijelaskan dari profil fitur.
- Dashboard dapat menampilkan peta choropleth dengan warna sequential orange-red.
- Join ke GeoJSON berjalan memakai `kode_kemendagri` tanpa kehilangan wilayah.
