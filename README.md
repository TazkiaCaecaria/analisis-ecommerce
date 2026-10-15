# Proyek Analisis Data: E-Commerce Public Dataset (Olist, Brasil)

Analisis data e-commerce periode **Januari 2017 - Agustus 2018** (pesanan berstatus *delivered*) beserta dashboard interaktif Streamlit.

## Pertanyaan Bisnis
1. Kategori produk apa yang menjadi 10 besar penyumbang revenue, berapa kontribusinya, dan bagaimana rata-rata review score-nya?
2. State mana yang memiliki lama pengiriman dan persentase keterlambatan tertinggi, dan seberapa besar keterlambatan menurunkan review score?

Analisis lanjutan: RFM, geospatial, dan binning lama pengiriman.

## Struktur Direktori
```
submission
├───dashboard
| ├───main_data.csv      # data gabungan hasil cleaning (level item pesanan)
| ├───state_geo.csv      # koordinat rata-rata tiap state
| └───dashboard.py
├───data                 # dataset mentah (CSV)
├───notebook.ipynb
├───README.md
├───requirements.txt
└───url.txt
```

## Setup Environment
```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

## Menjalankan Dashboard
Jalankan dari folder `submission`:
```
streamlit run dashboard/dashboard.py
```
Dashboard terbuka di `http://localhost:8501`.

## Menjalankan Ulang Notebook
Jalankan `notebook.ipynb` dari folder `submission` (membaca folder `data/`). Sel terakhir menghasilkan ulang `dashboard/main_data.csv` dan `dashboard/state_geo.csv`.
