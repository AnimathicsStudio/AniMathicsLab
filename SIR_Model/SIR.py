import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from plotly_config import plotly_bersih

# Judul Aplikasi
st.title("Model Penyebaran Penyakit - SIR (Susceptible, Infected, Recovered)")

# Input parameter model SIR
st.sidebar.header("Pengaturan Model SIR")
beta = st.sidebar.slider(r"Tingkat Infeksi ($\beta$)", 0.0, 1.0, 0.3)
gamma = st.sidebar.slider(r"Tingkat Pemulihan ($\gamma$)", 0.0, 1.0, 0.1)
population = st.sidebar.slider("Populasi (Jumlah Orang, $N$)", 100, 10000, 1000)
initial_infected = st.sidebar.slider(r"Jumlah Awal Terinfeksi ($I_{0}$)", 1, 100, 1)
initial_recovered = st.sidebar.slider(r"Jumlah Awal Sembuh ($R_{0}$)", 0, 100, 0)

# Parameter waktu simulasi
days = st.sidebar.slider("Jumlah Hari Simulasi", 1, 365, 160)

# Fungsi untuk menghitung model SIR
def sir_model(beta, gamma, population, initial_infected, initial_recovered, days):
    S = np.zeros(days)
    I = np.zeros(days)
    R = np.zeros(days)
    
    S[0] = population - initial_infected - initial_recovered
    I[0] = initial_infected
    R[0] = initial_recovered
    
    for t in range(1, days):
        dS = -beta * S[t-1] * I[t-1] / population
        dI = beta * S[t-1] * I[t-1] / population - gamma * I[t-1]
        dR = gamma * I[t-1]
        
        S[t] = S[t-1] + dS
        I[t] = I[t-1] + dI
        R[t] = R[t-1] + dR
    
    return S, I, R

# Menjalankan model SIR dengan parameter yang dipilih
S, I, R = sir_model(beta, gamma, population, initial_infected, initial_recovered, days)

# Membuat grafik menggunakan Plotly
fig = go.Figure()

# Menambahkan data ke grafik untuk Susceptible, Infected, dan Recovered
fig.add_trace(go.Scatter(
    x=np.arange(days),
    y=S,
    mode='lines',
    line=dict(color='blue'),
    name='Susceptible',
    hoverinfo='skip',
    hovertemplate=None
))

fig.add_trace(go.Scatter(
    x=np.arange(days),
    y=I,
    mode='lines',
    line=dict(color='red'),
    name='Infected',
    hoverinfo='skip',
    hovertemplate=None
))

fig.add_trace(go.Scatter(
    x=np.arange(days),
    y=R,
    mode='lines',
    line=dict(color='green'),
    name='Recovered',
    hoverinfo='skip',
    hovertemplate=None
))

# Mendapatkan konfigurasi Plotly dari file plotly_config.py
config = plotly_bersih()

fig.update_layout(
    # width=600,
    # height=600,
    showlegend=True,
    title="Simulasi Penyebaran Penyakit (Model SIR)",  # Set Title secara eksplisit
    # xaxis=dict(scaleanchor="y", visible=False),
    # yaxis=dict(visible=False),
    margin=dict(l=0, r=0, t=0, b=0),
    dragmode='pan',  # Set default mode to pan
)
# Menampilkan grafik di Streamlit dengan konfigurasi yang diatur
st.plotly_chart(fig, use_container_width=True, config=config)

# Menampilkan informasi terkait model
# st.write(f"**Tingkat Infeksi (Beta):** {beta}")
# st.write(f"**Tingkat Pemulihan (Gamma):** {gamma}")
# st.write(f"**Populasi Total:** {population}")
# st.write(f"**Jumlah Awal Terinfeksi:** {initial_infected}")
# st.write(f"**Jumlah Awal Sembuh:** {initial_recovered}")
