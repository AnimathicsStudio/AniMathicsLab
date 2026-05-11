import streamlit as st
import pandas as pd
import networkx as nx
import time
import numpy as np
import plotly.graph_objects as go
from aco_core import ACO

st.set_page_config(layout="wide")

st.title("Visualisasi Ant Colony Optimization (ACO)")
uploaded_file = st.file_uploader("Upload file Excel", type=["xlsx"])
if not uploaded_file:
    st.stop()

xls = pd.ExcelFile(uploaded_file)
sheet_names = xls.sheet_names
dist_sheet = st.selectbox("Pilih sheet untuk matriks jarak", sheet_names)
coord_sheet = st.selectbox("Pilih sheet untuk koordinat (opsional)", ["(Tidak digunakan)"] + sheet_names)

# Sidebar - parameter
st.sidebar.title("Parameter ACO")
alpha = st.sidebar.slider("α - Feromon", 0.1, 5.0, 1.0)
beta = st.sidebar.slider("β - Heuristik", 0.1, 5.0, 2.0)
rho = st.sidebar.slider("ρ - Evaporasi", 0.0, 1.0, 0.5)
Q = st.sidebar.slider("Q - Konstanta", 1.0, 10.0, 5.0)
n_ants = st.sidebar.slider("Jumlah Semut", 1, 20, 5)
n_iter = st.sidebar.slider("Jumlah Iterasi", 1, 50, 10)
frames_per_iter = st.sidebar.slider("Frame per Iterasi", 10, 300, 100)

# Baca data jarak dan koordinat
dist_df = pd.read_excel(xls, sheet_name=dist_sheet, index_col=0)
nodes = dist_df.columns.tolist()
distances = {(i, j): dist_df.loc[i, j] for i in nodes for j in nodes if i != j}

G = nx.Graph()
G.add_nodes_from(nodes)
for (i, j), d in distances.items():
    G.add_edge(i, j, weight=d)

if coord_sheet != "(Tidak digunakan)":
    coord_df = pd.read_excel(xls, sheet_name=coord_sheet, index_col=0)
    pos = {idx: (row[0], row[1]) for idx, row in coord_df.iterrows()}
else:
    pos = nx.spring_layout(G, seed=42)

aco = ACO(G, distances, alpha, beta, rho, Q)

# Fungsi untuk menggambar graf
def draw_plotly_graph(G, pos, pheromones, ant_positions=None):
    edge_x, edge_y = [], []

    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='gray'),
        hoverinfo='none', mode='lines'
    )

    node_x, node_y, node_text = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(node))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        marker=dict(size=30, color='skyblue'),
        text=node_text,
        textposition="top center"
    )

    traces = [edge_trace, node_trace]

    if ant_positions:
        for x, y in ant_positions:
            ant_trace = go.Scatter(
                x=[x], y=[y],
                mode='markers',
                marker=dict(size=12, color='red'),
                showlegend=False
            )
            traces.append(ant_trace)

    fig = go.Figure(data=traces)
    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
        height=600
    )
    return fig

# Visualisasi iteratif
placeholder = st.empty()

for it in range(n_iter):
    st.subheader(f"Iterasi {it + 1}")
    paths = aco.run_iteration(n_ants)

    # Buat semua perjalanan semut menjadi daftar koordinat (per frame)
    ants_trails = []
    for path in paths:
        trail = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            trail.append(((x0, y0), (x1, y1)))
        ants_trails.append(trail)

    total_hops = max(len(trail) for trail in ants_trails)

    for f in range(frames_per_iter):
        ant_positions = []
        progress = f / frames_per_iter
        for trail in ants_trails:
            if not trail:
                continue
            pos_idx = int(progress * len(trail))
            t = (progress * len(trail)) % 1
            if pos_idx >= len(trail):
                pos_idx = len(trail) - 1
                t = 1
            (x0, y0), (x1, y1) = trail[pos_idx]
            x = (1 - t) * x0 + t * x1
            y = (1 - t) * y0 + t * y1
            ant_positions.append((x, y))

        fig = draw_plotly_graph(G, pos, aco.get_pheromones(), ant_positions=ant_positions)
        placeholder.plotly_chart(fig, use_container_width=True, key=f"frame-{it}-{f}")
        time.sleep(0.05)

    fig = draw_plotly_graph(G, pos, aco.get_pheromones())
    placeholder.plotly_chart(fig, use_container_width=True, key=f"final-{it}")
    time.sleep(0.3)

st.success("Simulasi selesai!")