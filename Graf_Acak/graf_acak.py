import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os

# --------------------------
# Konfigurasi halaman
# --------------------------
st.set_page_config(page_title="Graf Acak Interaktif", layout="centered")
st.title("🎲 Graf Interaktif: Drag Node Bebas")

# --------------------------
# Sidebar: Pengaturan Graf
# --------------------------
st.sidebar.header("Pengaturan Model Graf")

model = st.sidebar.selectbox("Pilih Model Graf", ["Erdős–Rényi", "Barabási–Albert"])
n = st.sidebar.slider("Jumlah Simpul (n)", 5, 50, 20)

if model == "Erdős–Rényi":
    p = st.sidebar.slider("Probabilitas Sisi (p)", 0.0, 1.0, 0.2, step=0.01)
    G = nx.erdos_renyi_graph(n, p)
else:
    m = st.sidebar.slider("Jumlah Sisi per Simpul Baru (m)", 1, min(n - 1, 10), 2)
    G = nx.barabasi_albert_graph(n, m)

# --------------------------
# Statistik Sederhana
# --------------------------
st.subheader("📊 Statistik Graf")
st.markdown(f"- Jumlah simpul: **{G.number_of_nodes()}**")
st.markdown(f"- Jumlah sisi: **{G.number_of_edges()}**")

derajat = [d for _, d in G.degree()]
st.markdown(f"- Derajat rata-rata: **{sum(derajat)/len(derajat):.2f}**")

if nx.is_connected(G):
    st.markdown("- Komponen terhubung: **1 (Graf Terhubung)**")
else:
    st.markdown(f"- Komponen terhubung: **{nx.number_connected_components(G)}**")

# --------------------------
# Visualisasi Interaktif
# --------------------------
st.subheader("📌 Visualisasi Interaktif")

# Buat graf Pyvis dari NetworkX
net = Network(height="600px", width="100%", notebook=False, directed=False)
net.from_nx(G)
net.force_atlas_2based()

# Pastikan direktori /tmp ada
os.makedirs("/tmp", exist_ok=True)

# Simpan HTML ke path aman
html_path = "/tmp/graph.html"
net.write_html(html_path)

# Tampilkan HTML di Streamlit
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()
components.html(html_content, height=620, width=800)
