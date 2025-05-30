import streamlit as st
import numpy as np
import pandas as pd
from fam_core import *

st.set_page_config(page_title="Aplikasi FAM Klasifikasi", layout="wide")

st.sidebar.title("Pengaturan FAM")

uploaded_file = st.sidebar.file_uploader("Unggah file Excel", type=["xlsx"])

if uploaded_file:
    sheet_names = ambil_nama_sheet(uploaded_file)
    sheet_selected = st.sidebar.selectbox("Pilih Sheet", sheet_names)

    if sheet_selected:
        df = muat_sheet(uploaded_file, sheet_selected)

        st.sidebar.markdown("### Pilih Kolom Fitur")
        fitur = st.sidebar.multiselect("Fitur (predictor)", df.columns.tolist())

        st.sidebar.markdown("### Pilih Kolom Label")
        label = st.sidebar.selectbox("Label (target)", df.columns.tolist())

        # Inisialisasi session_state tombol/flag
        for key in ["show_A", "show_B", "show_M", "show_HasilFAM", "show_plot_TFN"]:
            if key not in st.session_state:
                st.session_state[key] = False
        
        st.sidebar.title("Visualisasi Variabel")
        if st.sidebar.button("📈 Plot TFN", use_container_width=True):
            st.session_state.show_plot_TFN = True

        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            if st.button("$A$", use_container_width=True):
                st.session_state.show_A = True
        with col2:
            if st.button("$B$", use_container_width=True):
                st.session_state.show_B = True
        with col3:
            if st.button("$M$", use_container_width=True):
                st.session_state.show_M = True

        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚙️ Proses Analisis")
        metode = st.sidebar.selectbox("", ["SumProd", "MaxProd", "MaxMin", "Custom"])

        norma_t_choice = None
        norma_s_choice = None
        if metode == "Custom":
            norma_t_choice = st.sidebar.selectbox("Pilih T-norm (Operator AND)", [
                "Minimum", "Produk Algebra", "Lukasiewicz", "Einstein", "Hamacher"
            ])
            norma_s_choice = st.sidebar.selectbox("Pilih S-norm (Operator OR)", [
                "Maximum", "Probabilistic Sum", "Lukasiewicz", "Einstein", "Hamacher"
            ])
            
        if st.sidebar.button("🚀 Hitung Prediksi", use_container_width=True):
            st.session_state.show_HasilFAM = True

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Data dan Fitur",
            "Plot TFN",
            "Matriks $A$ & $B$",
            "Matriks $M$",
            "Hasil FAM"
        ])

        with tab1:
            st.header("Data Excel Lengkap")
            st.dataframe(df)

            if fitur and label:
                df_bersih = bersihkan_ubah_numerik(df, fitur)
                TFNVariabel = buat_TFN_variabel(df_bersih, fitur)

                st.header("Data Terpilih (Fitur + Label)")
                kolom_terpilih = fitur + [label] if label not in fitur else fitur
                st.dataframe(df[kolom_terpilih])

                A = buat_matriks_A(df_bersih, fitur, TFNVariabel, tampilkan=False)
                B, M = buat_matriks_B_M(A)
            else:
                st.warning("Silakan pilih fitur dan label terlebih dahulu.")
                A = B = M = None
                TFNVariabel = None
                df_bersih = None

        with tab2:
            if st.session_state.show_plot_TFN:
                st.header("Visualisasi Fungsi Keanggotaan TFN")
                if fitur and TFNVariabel and df_bersih is not None:
                    fig = plot_TFN(df_bersih, fitur, TFNVariabel)
                    st.pyplot(fig)
                else:
                    st.warning("Silakan pilih fitur terlebih dahulu untuk menampilkan plot TFN.")
            else:
                st.info("Tekan tombol 'Plot TFN' di sidebar untuk menampilkan plot TFN.")

        with tab3:
            if st.session_state.show_A and A is not None:
                st.subheader("Vektor $A_i$")
                for i, a in enumerate(A):
                    latex_str = LMtx_latex_str(np.array([a]), judul=f"A_{{{i+1}}}", koma=2)
                    st.latex(latex_str)
                latex_str = LMtx_latex_str(A, judul="A", koma=2)
                st.latex(latex_str)
            elif st.session_state.show_A:
                st.warning("Matriks A belum tersedia. Pastikan memilih fitur dan label.")

            if st.session_state.show_B and B is not None:
                st.subheader("Matriks $B$")
                latex_str = LMtx_latex_str(B, judul="B", koma=2)
                st.latex(latex_str)
            elif st.session_state.show_B:
                st.warning("Matriks B belum tersedia. Pastikan memilih fitur dan label.")

        with tab4:
            if st.session_state.show_M and M is not None:
                st.subheader("Matriks $M_i$")
                for i, m_i in enumerate(M):
                    latex_str = LMtx_latex_str(m_i, judul=f"M_{{{i+1}}}", koma=2)
                    st.latex(latex_str)

                st.subheader("Matriks $M = A^T$")
                M_transpose = A.T
                latex_str_transpose = LMtx_latex_str(M_transpose, judul="M", koma=2)
                st.latex(latex_str_transpose)
            elif st.session_state.show_M:
                st.warning("Matriks M belum tersedia. Pastikan memilih fitur dan label.")

        with tab5:
            if st.session_state.show_HasilFAM and fitur and label and A is not None and M is not None:
                st.header("Hasil Prediksi dan Akurasi")

                hasil_df, akurasi = hitung_FAM(
                    df_bersih, fitur, label, TFNVariabel, A,
                    metode=metode,
                    norma_t=norma_t_choice,
                    norma_s=norma_s_choice
                )
                st.dataframe(hasil_df)
                st.success(f"Akurasi keseluruhan: {akurasi:.2f}%")

                if st.checkbox("Tampilkan Aturan Fuzzy"):
                    final_rules = ekstrak_aturan(df_bersih, fitur, label, TFNVariabel)
                    st.text_area("Aturan Fuzzy", "\n".join(str(r) for r in final_rules), height=300)
            elif st.session_state.show_HasilFAM:
                st.warning("Data belum lengkap untuk menghitung prediksi. Pastikan memilih fitur dan label.")
            else:
                st.info("Tekan tombol 'Hitung Prediksi' di sidebar untuk mulai prediksi.")
