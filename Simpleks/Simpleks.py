import streamlit as st
import numpy as np
import pandas as pd

# Konfigurasi layout
st.set_page_config(page_title="Animathics Lab - Penyelesai LP", layout="wide")

# Fungsi bantu
def pivot_operation(tableau, pivot_row, pivot_col):
    tableau[pivot_row, :] = tableau[pivot_row, :] / tableau[pivot_row, pivot_col]
    for r in range(tableau.shape[0]):
        if r != pivot_row:
            tableau[r, :] -= tableau[r, pivot_col] * tableau[pivot_row, :]
    return tableau

# Judul dan deskripsi
st.title("Penyelesai Linear Programming")
st.markdown("""
Selamat datang di **Laboratorium Linear Programming**.
Di sini, Anda dapat bereksperimen dengan **Metode Simpleks**, langkah demi langkah, dan mengamati bagaimana solusi berkembang pada setiap iterasi.
Alat ini ideal untuk mahasiswa, pendidik, dan peneliti.
""")

with st.sidebar:
    st.header("🔧 Panel Kendali")
    # st.markdown("""Tentukan masalah LP Anda di bawah ini. Gunakan angka yang dipisahkan koma seperti `3,5` atau `1,2,10`.""")
    obj_type = st.radio("**Tipe Tujuan**", ("Maksimalkan", "Minimalkan"))
    n_var = st.number_input("Banyaknya Variabel", min_value=2, max_value=15, value=2)
    n_con = st.number_input("Banyaknya Kendala", min_value=1, max_value=15, value=2)

    st.markdown("**🎯 Fungsi Tujuan**<br>(contoh: `3,5` untuk 3x + 5y)", unsafe_allow_html=True)
    obj_coeff = st.text_input("Koefisien Z:", value="3,5")

    st.markdown("**📏 Kendala** <br>(contoh: `2,1,10` berarti 2x + y ≤ 10)", unsafe_allow_html=True)
    constraints = []
    for i in range(int(n_con)):
        con = st.text_input(f"Kendala {i+1}", value=f"1,1,10")
        constraints.append(con)

    show_steps = st.checkbox("Tampilkan Langkah Iterasi", value=True)
    solve_btn = st.button("🚀 Selesaikan")

if solve_btn:
    try:
        c = np.array([float(x.strip()) for x in obj_coeff.split(",")])

        A = []
        b = []
        for con in constraints:
            parts = [float(x.strip()) for x in con.split(",")]
            A.append(parts[:-1])
            b.append(parts[-1])
        A = np.array(A)
        b = np.array(b)

        tableau = np.hstack([A, np.eye(len(A)), b.reshape(-1,1)])
        obj_row = np.hstack([-c if obj_type=="Maksimalkan" else c, np.zeros(len(A)+1)])
        tableau = np.vstack([tableau, obj_row])

        st.subheader("📋 Tabel Simpleks Awal")
        df = pd.DataFrame(tableau)
        st.dataframe(df)

        iteration = 0
        while True:
            iteration += 1
            obj_row = tableau[-1, :-1]
            if all(obj_row >= 0):
                st.success("✅ Solusi optimal ditemukan!")
                break

            pivot_col = np.argmin(obj_row)
            ratios = []
            for i in range(len(A)):
                if tableau[i, pivot_col] > 0:
                    ratios.append(tableau[i, -1] / tableau[i, pivot_col])
                else:
                    ratios.append(np.inf)
            pivot_row = np.argmin(ratios)

            if all(r == np.inf for r in ratios):
                st.error("❌ Masalah tidak terbatas!")
                break

            if show_steps:
                st.markdown(f"### 🔁 Iterasi {iteration}")
                st.write(f"Pivot di Baris {pivot_row+1}, Kolom {pivot_col+1}")

            tableau = pivot_operation(tableau, pivot_row, pivot_col)

            if show_steps:
                df = pd.DataFrame(tableau)
                st.dataframe(df)

        st.header("✅ Solusi Akhir")
        solution = np.zeros(len(c))
        for i in range(len(A)):
            col = tableau[i, :len(c)]
            if list(col).count(1) == 1 and list(col).count(0) == len(col)-1:
                var_idx = list(col).index(1)
                solution[var_idx] = tableau[i, -1]

        for idx, val in enumerate(solution):
            st.write(f"x{idx+1} = {val:.2f}")
        st.write(f"**Nilai Optimal Z = {tableau[-1, -1]:.2f}**")

        # Versi LaTeX dari ekspresi akhir
        expr = " + ".join([f"{c[i]}x_{{{i+1}}}" for i in range(len(c))])
        st.latex(f"Z = {expr}")

        # Tombol ekspor
        csv = pd.DataFrame(tableau).to_csv(index=False)
        st.download_button(
            label="⬇️ Unduh Tabel Akhir",
            data=csv,
            file_name='simplex_tableau.csv',
            mime='text/csv',
        )

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
