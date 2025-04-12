import streamlit as st
import networkx as nx
import plotly.graph_objects as go

# --------------------------
# Konfigurasi halaman
# --------------------------
st.set_page_config(page_title="Graf Acak Interaktif", layout="centered")
st.title("🎲 Graf Acak Interaktif dengan Plotly")

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
# Statistik Graf
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
# Layout & Visualisasi Plotly
# --------------------------
st.subheader("📌 Visualisasi Graf (Plotly)")

pos = nx.spring_layout(G, seed=42)

# Buat edge trace
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

# Buat node trace
node_x = []
node_y = []
node_text = []
node_color = []

for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    deg = G.degree[node]
    node_text.append(f"Node {node}<br>Derajat: {deg}")
    node_color.append(deg)

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    hoverinfo='text',
    marker=dict(
        showscale=True,
        colorscale='YlGnBu',
        color=node_color,
        size=20,
        colorbar=dict(title="Derajat"),
        line_width=2
    ),
    text=[str(n) for n in G.nodes()],
    textposition="top center"
)

fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title="Visualisasi Graf Acak",
                    title_x=0.5,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=False, zeroline=False)
                ))

st.plotly_chart(fig, use_container_width=True)
