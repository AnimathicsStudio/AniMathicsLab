import streamlit as st
import pandas as pd
from tahani_core import hitung_rekomendasi

def ambil_nama_sheet(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    return xls.sheet_names

def muat_sheet(uploaded_file, sheet_name):
    return pd.read_excel(uploaded_file, sheet_name=sheet_name)

st.set_page_config(page_title="Sistem Rekomendasi Produk, Fuzzy Tahani", layout="wide")
st.title('Sistem Rekomendasi, Fuzzy Tahani')

pilihan_user = {}  # Inisialisasi global

with st.sidebar:
    FileData = st.file_uploader("Pilih file Excel", type=["xlsx"])

    if FileData:
        nama_sheet = ambil_nama_sheet(FileData)
        sheet_terpilih = st.selectbox("Pilih Sheet", nama_sheet)

        if sheet_terpilih:
            df = muat_sheet(FileData, sheet_terpilih)

            st.sidebar.markdown("### Pilih Kolom Fitur")
            fitur = st.sidebar.multiselect("Pilih Fitur (predictor)", df.columns.tolist())
            if fitur:
                st.sidebar.markdown("### Tentukan Preferensi Anda:")
                pilihan_user['df'] = df
                for fitur_column in fitur:
                    pilihan_user[fitur_column] = st.sidebar.slider(
                        f"Preferensi untuk {fitur_column}",
                        min_value=0.0,
                        max_value=1.0,
                        step=0.01,
                        value=0.5,  # default = sedang
                        help="0 = Rendah, 0.5 = Sedang, 1 = Tinggi"
                    )
    else:
        st.warning("Silakan unggah file Excel terlebih dahulu.")

if FileData and 'df' in pilihan_user:
    tab1, tab2 = st.tabs(["Pemaparan Data", "Hasil Rekomendasi"])

    with tab1:
        st.subheader(f"Data dari Sheet '{sheet_terpilih}':")
        st.dataframe(pilihan_user['df'])

    with tab2:
        skor_df = hitung_rekomendasi(pilihan_user, df)
        if skor_df is not None:
            st.subheader("Rekomendasi Berdasarkan Preferensi Anda")
            st.write(skor_df)
        else:
            st.write("Tidak ada data yang dapat ditampilkan.")
