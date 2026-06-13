# Design: Streamlit Choropleth Dashboard MVP

Tanggal: 2026-06-13

## Tujuan

Membuat dashboard Streamlit sederhana untuk menampilkan choropleth kerentanan banjir kabupaten/kota Jawa Barat berdasarkan output clustering.

## Scope MVP

Dashboard hanya menampilkan summary periode 2015–2023, bukan filter tahunan.

Komponen:

1. Judul dan metodologi singkat.
2. Metric card jumlah wilayah per cluster.
3. Choropleth map Jawa Barat.
4. Tabel ranking wilayah berdasarkan `skor_kerentanan_rata2`.

## Data

Input:

- `data/processed/cluster_wilayah_summary.csv`
- `data/reference/Jabar_By_Kab.geojson`

Join key dashboard:

- `kode_kemendagri` sebagai string 4 digit.

Jika nama property kode pada GeoJSON berbeda, app akan mencari kandidat umum seperti `kode_kemendagri`, `KODE_KAB`, `kode`, `id`, dan `bps_kode`.

## Visual

Warna cluster:

- Rendah: `#FEE8C8`
- Sedang: `#FDBB84`
- Tinggi: `#E34A33`

Map menggunakan Plotly choropleth dengan tooltip nama wilayah, cluster, skor, rata-rata banjir, rata-rata hari hujan ekstrem, dan rata-rata sampah.

## Output

File utama:

- `app.py`

Cara menjalankan:

```bash
streamlit run app.py
```

## Kriteria Sukses

- Dashboard dapat dijalankan dengan Streamlit.
- Peta menampilkan 27 kabupaten/kota.
- Warna peta sesuai cluster rendah, sedang, tinggi.
- Ranking table tampil dan tersortir dari skor tertinggi.
