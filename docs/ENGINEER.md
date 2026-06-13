# ENGINEER.md

Dokumen ini berisi spesifikasi teknis, arsitektur data pipeline, batasan sistem, serta kebutuhan fitur (requirements) yang akan diimplementasikan ke dalam dashboard analitik untuk memetakan risiko banjir di Jawa Barat.

---

## 1. Deskripsi Proyek & Pertanyaan Kunci

Proyek ini bertujuan untuk merancang sistem analitik data berbasis framework OSEMN guna mengidentifikasi korelasi antara volume sampah, intensitas curah hujan, dan kejadian banjir. Dashboard yang dibangun akan digunakan untuk memetakan wilayah risiko serta menentukan prioritas intervensi logistik yang preventif di Provinsi Jawa Barat.

### Kebutuhan Bisnis & Metrik Utama

Sistem ini dirancang untuk menjawab tantangan dan menyajikan metrik dampak bencana berikut:

* 
**Frekuensi Banjir**: Mendokumentasikan dan memantau lebih dari 150 kejadian banjir di Jawa Barat sepanjang tahun yang jalurnya relatif meningkat.


* 
**Dampak Kemanusiaan**: Memantau pergerakan wilayah rawan yang mengakibatkan lebih dari 25.000 jiwa terdampak langsung atau mengungsi di area Pantura dan Bandung Raya.


* 
**Dampak Ekonomi**: Menyediakan visualisasi berbasis risiko untuk memitigasi potensi kerugian ekonomi sebesar 1,69 Triliun pada sektor logistik dan pertanian akibat akses jalan yang tertutup.



---

## 2. Kebutuhan Data & Sumber (Data Requirements)

Data yang diambil untuk mendukung dashboard ini dibagi ke dalam 3 kategori utama:

### A. Data Historis Kebencanaan

* 
**Sumber Data**: OpenDataJabar dan DIBI - BNPB.


* 
**Karakteristik**: Dataset dari instansi pemerintah terverifikasi secara hukum. Open Data Jabar menyajikan data hingga tingkat granularity desa/kelurahan untuk mendukung analisis spasial mikro. Data DIBI-BNPB digunakan sebagai instrumen *cross-validation* guna memastikan keandalan data bencana regional.



### B. Data Meteorologi dan Curah Hujan

* 
**Sumber Data**: Open-Meteo API serta BMKG & BPS.


* 
**Karakteristik**: Open-Meteo API digunakan karena dapat diakses tanpa autentikasi token, mempermudah pipeline data otomatis. Dataset ini dibangun dengan model hidrologi H-TESSEL untuk merepresentasikan siklus air secara akurat. Data BMKG/BPS berperan sebagai pembanding untuk memverifikasi hasil presipitasi ERA5.



### C. Data Pengelolaan Lingkungan (Faktor Antropogenik)

* 
**Sumber Data**: OpenDataJabar.


* 
**Karakteristik**: Mengintegrasikan volume produksi dan penanganan sampah lokal sebagai variabel aktivitas manusia yang memengaruhi infrastruktur saluran air. Data ini digunakan sebagai indikator sumbatan drainase makro di perkotaan.



---

## 3. Batasan Teknis & Mitigasi Pipeline (Data Engineering Specs)

Sebagai Data Engineer, pengelolaan pipeline data harus mengantisipasi kendala teknis berikut demi menjaga stabilitas data supply dashboard:

| Kendala Teknis | Dampak Sistem | Strategi Mitigasi Terpilih |
| --- | --- | --- |
| <br>**Batasan Limit API** 

 | Open-Meteo membatasi kuota gratis maksimal 10.000 panggilan per hari per alamat IP.

 | Menggunakan database cache SQLite lokal melalui pustaka `requests-cache` dan dekorator python untuk mengeliminasi pemanggilan HTTP yang redundan.

 |
| <br>**Perubahan Nama Kolom** 

 | Perubahan nama kolom sepihak pada rilis tahunan Open Data Jabar memicu kegagalan fungsi baca data.

 | Membangun lapisan validasi dinamis menggunakan blok penanganan eksepsi (*exception handling*) serta pemetaan kamus (*dictionary mapping*) tanpa menghentikan jalannya sistem.

 |
| <br>**Pemekaran Wilayah Baru** 

 | Munculnya nama administratif baru yang belum tercatat berisiko memicu hilangnya data saat proses *join*.

 | Menggunakan sistem pencocokan bertingkat yang secara otomatis mengalihkan data wilayah baru ke wilayah induknya agar tidak terjadi kehilangan data.

 |

### Dimensi Lingkup Data (Scope of Work)

* 
**Dimensi Waktu**: Menggunakan data deret waktu (*time-series*) historis banjir dan iklim selama 12 tahun terakhir (periode 2012–2024).


* 
**Dimensi Spasial**: Pembatasan wilayah administrasi dilakukan pada level Kabupaten/Kota se-Provinsi Jawa Barat yang mencakup total 27 wilayah administratif.



---

## 4. Kebutuhan Fitur Dashboard (Dashboard Requirements)

Dashboard utama akan dibangun untuk menyajikan visualisasi indikator utama serta penyajian data analitik untuk target pengguna spesifik:

### A. Komponen Visualisasi Utama & Model Prediktif

* 
**Peta Klaster Risiko Wilayah**: Membantu menampilkan pemetaan wilayah kerentanan banjir hasil pemrosesan algoritma *machine learning* yang menggabungkan faktor cuaca dan kapasitas lingkungan (volume sampah).


* 
**Analisis Tren & Korelasi**: Visualisasi grafik interaktif untuk memetakan hubungan langsung antara efisiensi pengelolaan sampah lokal dengan frekuensi terjadinya genangan air luapan di 27 kabupaten/kota.


* 
**Grafik Puncak Bahaya**: Menampilkan tren puncak bahaya banjir bulanan berdasarkan data historis.



### B. Modul Berdasarkan Target Audience

* 
**Fitur BPBD Jawa Barat**: Modul khusus untuk pembagian bantuan logistik, perumusan kebijakan mitigasi, dan penyusunan strategi evakuasi darurat berbasis wilayah prioritas tinggi.


* 
**Fitur Pemerintah Daerah (Bappeda / Dinas SDA)**: Modul analisis spasial untuk membantu perencanaan tata ruang daerah ramah air, pemeliharaan DAS Citarum, serta penentuan titik pembangunan tanggul penahan banjir baru.


* 
**Fitur Relawan & Publik**: Tampilan ringkas dan informatif guna meningkatkan kesadaran masyarakat (*community resilience*) untuk melakukan evakuasi mandiri yang preventif.



---

## 5. Alokasi Peran Anggota Tim

* 
**Data Engineer (Mochamad Ikhbar Adiwinangun)**: Bertanggung jawab mengambil data, menyusun arsitektur pipeline, mengolah data mentah, dan memastikan data dapat diproses ulang (*re-processability*).


* 
**Data Preprocessing Lead (Mudzaki K Hakim)**: Bertanggung jawab membersihkan data, melakukan standarisasi, integrasi dataset, dan melakukan *feature engineering*.


* 
**Data Analyst (Raka Adhitya Nugraha)**: Bertanggung jawab melakukan analisis eksploratif dan menyusun interpretasi hasil teknis.


* 
**Dashboard Developer (Joan Melkior Silaen)**: Bertanggung jawab membangun visualisasi indikator utama dan penyajian akhir dashboard.


* 
**Documentation and Insight Lead (Alghan Pridanusuta)**: Bertanggung jawab menyusun laporan akhir dan slide presentasi proyek.
