import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import rcParams
import random

# Gaya visual elegan
rcParams['font.family'] = 'serif'
rcParams['mathtext.fontset'] = 'cm'
rcParams['font.size'] = 12

# Buat graf tetap atau acak
def build_fixed_graph():
    G = nx.Graph()
    edges = [
        (1, 2), (1, 3), (2, 4), (2, 5),
        (3, 6), (4, 7), (5, 8), (6, 9),
        (7, 10), (8, 9), (9, 10)
    ]
    G.add_edges_from(edges)
    return G

def build_random_graph(n):
    G = nx.erdos_renyi_graph(n, 0.3, seed=random.randint(0, 10000))
    while not nx.is_connected(G):
        G = nx.erdos_renyi_graph(n, 0.3, seed=random.randint(0, 10000))
    return G

# BFS dengan pelacakan parent dan urutan
from collections import deque

def bfs_spanning_tree(G, start):
    visited = set()
    queue = deque([start])
    parent = {}
    tree_edges = []
    visited_order = []

    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            visited_order.append(node)
            for neighbor in sorted(G.neighbors(node)):
                if neighbor not in visited and neighbor not in queue:
                    parent[neighbor] = node
                    queue.append(neighbor)
                    tree_edges.append((node, neighbor))
    return tree_edges, visited_order

# DFS dengan pelacakan parent dan urutan
def dfs_spanning_tree(G, start):
    visited = set()
    stack = [start]
    parent = {}
    tree_edges = []
    visited_order = []

    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            visited_order.append(node)
            if node in parent:
                tree_edges.append((parent[node], node))
            for neighbor in sorted(G.neighbors(node), reverse=True):
                if neighbor not in visited:
                    parent[neighbor] = node
                    stack.append(neighbor)
    return tree_edges, visited_order

# Sidebar kontrol
st.sidebar.title("🎛️ Panel Kontrol")

if "use_random" not in st.session_state:
    st.session_state.use_random = False
if "G" not in st.session_state:
    st.session_state.G = build_fixed_graph()

n = st.sidebar.number_input("Jumlah simpul (graf acak)", 5, 20, 10)
if st.sidebar.button("🎲 Acak Graf Baru"):
    st.session_state.use_random = True
    st.session_state.G = build_random_graph(n)
elif st.sidebar.button("🔒 Gunakan Graf Tetap"):
    st.session_state.use_random = False
    st.session_state.G = build_fixed_graph()

G = st.session_state.G
nodes = list(G.nodes)
start_node = st.sidebar.selectbox("🟢 Pilih Simpul Awal", nodes)
method = st.sidebar.radio("🔁 Metode", ["BFS", "DFS"])

# Hasil spanning tree dan urutan kunjungan
if method == "BFS":
    tree_edges, visited_order = bfs_spanning_tree(G, start_node)
else:
    tree_edges, visited_order = dfs_spanning_tree(G, start_node)

# Inisialisasi langkah
if "step" not in st.session_state:
    st.session_state.step = 0

# Tombol navigasi minimalis
col1, col2, col3, col4 = st.sidebar.columns(4)
with col1:
    if st.button("↺", help="Reset"):
        st.session_state.step = 0
with col2:
    if st.button("◀", help="Mundur"):
        st.session_state.step = max(0, st.session_state.step - 1)
with col3:
    if st.button("▶", help="Lanjut"):
        st.session_state.step = min(len(tree_edges), st.session_state.step + 1)
with col4:
    if st.button("⋙", help="Langsung ke akhir"):
        st.session_state.step = len(tree_edges)

# Posisi layout
pos = nx.spring_layout(G, seed=42)

# Tentukan warna simpul
node_colors = []
for node in G.nodes:
    if node == start_node:
        color = 'orange'
    elif node in visited_order[:st.session_state.step + 1]:
        color = 'black'
    else:
        color = '#dddddd'
    node_colors.append(color)

# Gambar graf
fig, ax = plt.subplots(figsize=(6, 6))
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=200)
nx.draw_networkx_labels(G, pos, ax=ax, font_size=9, font_color='white', font_family='serif')
nx.draw_networkx_edges(G, pos, ax=ax, edgelist=G.edges, width=1, edge_color='lightgray')
nx.draw_networkx_edges(G, pos, ax=ax, edgelist=tree_edges[:st.session_state.step], width=3, edge_color='red')

ax.set_title(f"{method}, Langkah ke-{st.session_state.step} dari {len(tree_edges)}", fontsize=9)
ax.set_aspect('equal')
ax.axis('off')
col = st.columns([1, 12, 1])[1]
with col:
    st.pyplot(fig)
