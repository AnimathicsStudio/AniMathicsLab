import streamlit as st
from pyvis.network import Network
import networkx as nx
import tempfile
import streamlit.components.v1 as components

# --- Buat graf ---
st.title("Graf Interaktif: Drag Node Bebas (Pyvis)")

model = st.sidebar.selectbox("Model Graf", ["Erdős–Rényi", "Barabási–Albert"])
n = st.sidebar.slider("Jumlah simpul", 5, 50, 20)

if model == "Erdős–Rényi":
    p = st.sidebar.slider("Probabilitas sisi (p)", 0.0, 1.0, 0.2)
    G = nx.erdos_renyi_graph(n, p)
else:
    m = st.sidebar.slider("Sisi per simpul baru (m)", 1, min(n - 1, 5), 2)
    G = nx.barabasi_albert_graph(n, m)

# --- Buat visualisasi Pyvis ---
net = Network(height="600px", width="100%", notebook=False)
net.from_nx(G)
net.force_atlas_2based()  # agar gaya seperti karet

# --- Simpan sebagai HTML sementara ---
with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
    path = tmp_file.name
    net.show(path)
    HtmlFile = open(path, 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    components.html(source_code, height=620, width=800)
