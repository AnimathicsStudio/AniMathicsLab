import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Konfigurasi layout
st.set_page_config(page_title="Animathics Lab - Penyelesai Grafik LP", layout="wide")

st.title("🌊 Animathics Lab: Penyelesai Grafik Linear Programming")

with st.sidebar:
    st.header("🔧 Pengaturan Masalah")
    st.markdown("Tentukan masalah LP Anda. Untuk saat ini dibatasi 2 variabel saja.")

    obj_type = st.radio("Tipe Tujuan", ("Maksimalkan", "Minimalkan"))

    st.markdown("**🎯 Fungsi Tujuan** (contoh: `3,5` untuk 3x + 5y)")
    obj_coeff = st.text_input("Koefisien Z:", value="3,5")

    st.markdown("**📏 Kendala** (contoh: `2,1,10` berarti 2x + y ≤ 10)")
    constraint1 = st.text_input("Kendala 1:", value="2,1,10")
    constraint2 = st.text_input("Kendala 2:", value="1,2,15")

    solve_btn = st.button("🚀 Selesaikan")

if solve_btn:
    try:
        c = np.array([float(x.strip()) for x in obj_coeff.split(",")])
        constraints = []
        for con in [constraint1, constraint2]:
            parts = [float(x.strip()) for x in con.split(",")]
            constraints.append(parts)

        A = np.array([con[:-1] for con in constraints])
        b = np.array([con[-1] for con in constraints])

        # Menambahkan batasan x >= 0, y >= 0
        A = np.vstack([A, [-1,0], [0,-1]])
        b = np.hstack([b, 0, 0])

        # Membuat plot dasar
        fig = go.Figure()
        x = np.linspace(0, max(b)*1.5, 400)
        y = np.linspace(0, max(b)*1.5, 400)
        X, Y = np.meshgrid(x, y)

        feasible = np.ones_like(X, dtype=bool)
        for i in range(len(b)):
            feasible &= (A[i,0]*X + A[i,1]*Y <= b[i])

        fig.add_trace(go.Contour(
            x=x, y=y, z=feasible.astype(int),
            showscale=False, colorscale=[[0, 'white'], [1, 'lightblue']],
            opacity=0.5
        ))

        # Garis kendala
        colors = ['red', 'green', 'purple', 'orange']
        for idx in range(len(constraints)):
            xi = np.linspace(0, max(b)*1.2, 100)
            if A[idx,1] != 0:
                yi = (b[idx] - A[idx,0]*xi) / A[idx,1]
                fig.add_trace(go.Scatter(x=xi, y=yi, mode='lines', name=f"Kendala {idx+1}", line=dict(color=colors[idx%4])))

        # Slider untuk menggeser garis fungsi tujuan
        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ Eksplorasi Garis Fungsi Tujuan")

        min_z = 0
        max_z = max(b)*1.5 if max(b) > 0 else 10
        z_slider = st.sidebar.slider("Geser Nilai Z", min_value=float(min_z), max_value=float(max_z), value=float(max_z/2), step=0.5)

        # Menggambar garis fungsi tujuan berdasarkan Z
        xi = np.linspace(0, max(b)*1.2, 100)
        if c[1] != 0:
            yi = (z_slider - c[0]*xi) / c[1]
            fig.add_trace(go.Scatter(x=xi, y=yi, mode='lines', name=f"Fungsi Tujuan Z={z_slider:.1f}", line=dict(color='blue', dash='dash')))

        fig.update_layout(title="Daerah Feasible dan Eksplorasi Fungsi Tujuan", xaxis_title="x₁", yaxis_title="x₂", width=800, height=600)
        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")