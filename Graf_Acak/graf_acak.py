import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import sys
import os

# Import konfigurasi visual plotly bersih
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from plotly_config import plotly_bersih

# --------------------------
# Fungsi: Ambil layout graf
# --------------------------
def get_layout(G, method):
    if method == "spring":
        return nx.spring_layout(G, seed=42)
    elif method == "circular":
        return nx.circular_layout(G)
    elif method == "kamada_kawai":
        return nx.kamada_kawai_layout(G)
    elif method == "shell":
        return nx.shell_layout(G)
    elif method == "random":
        return nx.random_layout(G)
    else:
        return nx.spring_layout(G, seed=42)

# --------------------------
# Konfigurasi halaman
# --------------------------
st.set_page_config(page_title="Graf Acak Interaktif", layout="centered")

# --------------------------
# Sidebar: Input + Tombol
# --------------------------
with st.sidebar:
    st.header("Pengaturan Model Graf")
    model = st.selectbox("Pilih Model Graf", ["Erdős–Rényi", "Barabási–Albert"])
    n = st.slider("Orde ($n$)", 5, 50, 20)

    if model == "Erdős–Rényi":
        p = st.slider("Probabilitas Sisi ($p$)", 0.0, 1.0, 0.2, step=0.01)
    else:
        m = st.slider("Banyaknya sisi tiap titik baru ($m$)", 1, min(n - 1, 10), 2)

    layout_method = st.selectbox(
        "Pilih Layout Graf",
        ["spring", "circular", "kamada_kawai", "shell", "random"]
    )

    generate = st.button("🔁 Generate Graf")

# --------------------------
# Session: tampilkan graf saat pertama kali
# --------------------------
if "generate_graf" not in st.session_state:
    st.session_state.generate_graf = True

if generate:
    st.session_state.generate_graf = True

# --------------------------
# Jika tombol ditekan, tampilkan graf
# --------------------------
if st.session_state.generate_graf:

    if model == "Erdős–Rényi":
        G = nx.erdos_renyi_graph(n, p)
    else:
        G = nx.barabasi_albert_graph(n, m)

    deg = [d for _, d in G.degree()]

    # Sidebar: Statistik Graf
    statistik_html = f"""
    <hr>
    <h4>📊 Statistik Graf</h4>
    <ol style='padding-left: 1.2em; margin-top: 0em;'>
      <li>Orde: <b>{G.number_of_nodes()}</b></li>
      <li>Ukuran: <b>{G.number_of_edges()}</b></li>
      <li>Rata-rata derajat: <b>{sum(deg)/len(deg):.2f}</b></li>
      <li>Komponen terhubung: <b>{1 if nx.is_connected(G) else nx.number_connected_components(G)}</b></li>
    </ol>
    """

    st.sidebar.markdown(statistik_html, unsafe_allow_html=True)


    # --------------------------
    # Layout & Visualisasi Plotly
    # --------------------------
    pos = get_layout(G, layout_method)

    edge_x = []
    edge_y = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    node_text = []
    node_color = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        degree = G.degree[node]
        node_text.append(f"Node {node}<br>Derajat: {degree}")
        node_color.append(degree)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            colorscale='YlGnBu',
            color=node_color,
            size=20,
            line_width=2
        ),
        text=[str(n) for n in G.nodes()],
        textposition="top center"
    )

    fig = go.Figure(data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
    )

    fig.update_layout(
    margin=dict(l=0, r=0, t=30, b=0),
    dragmode='pan'
    )
    fig.update_yaxes(scaleanchor='x', scaleratio=1)
    config = plotly_bersih()
    st.plotly_chart(fig, use_container_width=True, config=config)
