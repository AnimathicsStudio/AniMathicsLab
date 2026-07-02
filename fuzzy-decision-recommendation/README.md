# Fuzzy Decision and Recommendation Lab

Applet Streamlit untuk mempelajari rekomendasi dan ranking multikriteria berbasis fuzzy decision making.

Kasus bawaan:

- Prioritas penerima beasiswa
- Kriteria: IPK, penghasilan orang tua, jumlah tanggungan, prestasi, dan keaktifan organisasi
- Metode: SAW, TOPSIS, dan WP

Fitur utama:

- Dataset contoh yang langsung tampil di aplikasi
- Editor data interaktif
- Upload CSV opsional
- Pengaturan bobot dan tipe kriteria benefit/cost
- Tabel normalisasi dan nilai terbobot
- Ranking akhir dan rekomendasi utama
- Perbandingan SAW, TOPSIS, dan WP
- Analisis sensitivitas bobot

Jalankan lokal:

```bash
streamlit run app.py
```

Format CSV minimal:

```text
Alternatif,IPK,Penghasilan Orang Tua,Jumlah Tanggungan,Prestasi,Keaktifan Organisasi
```
