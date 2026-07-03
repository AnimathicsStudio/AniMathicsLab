from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from optimization_core import (
    Product,
    Resource,
    display_table,
    optimize_plan,
    product_table,
    resource_table,
    sample_products,
)


st.set_page_config(page_title="Fuzzy Optimization Planner", layout="wide")

PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToKeep": ["toImage"],
    "scrollZoom": False,
    "doubleClick": False,
    "showTips": False,
}

PLAN_COLORS = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#46f0f0"]


def local_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1180px; padding-top: 1.25rem; }
        div[data-testid="stMetricValue"] { font-size: 1.25rem; }
        .note-box {
            border: 1px solid rgba(128, 128, 128, 0.28);
            border-radius: 8px;
            padding: 0.75rem 0.9rem;
            margin: 0.35rem 0 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def editable_products(default_products: list[Product], resources: list[Resource]) -> list[Product]:
    edited = st.data_editor(
        product_table(default_products, resources),
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Produk": st.column_config.TextColumn(required=True),
            "Profit/unit": st.column_config.NumberColumn(min_value=0.0, step=1.0),
            "Target permintaan": st.column_config.NumberColumn(min_value=0.0, step=1.0),
            "Toleransi permintaan": st.column_config.NumberColumn(min_value=1.0, step=1.0),
        },
    )
    products = []
    for _, row in edited.iterrows():
        name = str(row["Produk"]).strip()
        if not name:
            continue
        products.append(
            Product(
                name=name,
                profit=float(row["Profit/unit"]),
                demand_target=float(row["Target permintaan"]),
                demand_tolerance=max(1.0, float(row["Toleransi permintaan"])),
                resources={resource.name: float(row.get(resource.name, 0.0)) for resource in resources},
            )
        )
    return products


def editable_resources(default_resources: list[Resource]) -> list[Resource]:
    edited = st.data_editor(
        resource_table(default_resources),
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Sumber daya": st.column_config.TextColumn(required=True),
            "Batas ideal": st.column_config.NumberColumn(min_value=0.0, step=1.0),
            "Toleransi fuzzy": st.column_config.NumberColumn(min_value=1.0, step=1.0),
        },
    )
    resources = []
    for _, row in edited.iterrows():
        name = str(row["Sumber daya"]).strip()
        if name:
            resources.append(
                Resource(
                    name=name,
                    limit=float(row["Batas ideal"]),
                    tolerance=max(1.0, float(row["Toleransi fuzzy"])),
                )
            )
    return resources


def plot_top_plans(result: pd.DataFrame, product_names: list[str]) -> go.Figure:
    top = result.head(10).copy()
    top["Label"] = [f"Rencana {idx + 1}" for idx in range(len(top))]
    fig = go.Figure()
    for color, product in zip(PLAN_COLORS, product_names):
        fig.add_bar(
            x=top["Label"],
            y=top[product],
            name=product,
            marker_color=color,
            hovertemplate="%{x}<br>" + product + ": %{y}<extra></extra>",
        )
    fig.update_layout(
        barmode="stack",
        height=420,
        margin=dict(l=10, r=10, t=20, b=20),
        legend_title_text="Produk",
        xaxis=dict(fixedrange=True),
        yaxis=dict(title="Jumlah unit", fixedrange=True),
    )
    return fig


def plot_membership(best_row: pd.Series, products: list[Product], resources: list[Resource]) -> go.Figure:
    rows = []
    for product in products:
        rows.append({"Komponen": f"Permintaan {product.name}", "Derajat": best_row[f"{product.name} mu permintaan"]})
    for resource in resources:
        rows.append({"Komponen": resource.name, "Derajat": best_row[f"{resource.name} mu"]})
    rows.append({"Komponen": "Target profit", "Derajat": best_row["mu target profit"]})
    df = pd.DataFrame(rows)
    fig = px.bar(df, x="Derajat", y="Komponen", orientation="h", color="Derajat", color_continuous_scale="Tealrose")
    fig.update_layout(
        height=max(340, 42 * len(df)),
        margin=dict(l=10, r=10, t=20, b=20),
        coloraxis_showscale=False,
        xaxis=dict(range=[0, 1], fixedrange=True),
        yaxis=dict(fixedrange=True, autorange="reversed"),
    )
    return fig


local_css()

st.title("Fuzzy Optimization Planner")
st.caption("Menyusun rencana terbaik ketika batas sumber daya dan target bisnis bersifat toleran/fuzzy.")

default_products, default_resources = sample_products()

with st.sidebar:
    st.header("Parameter")
    step = st.slider("Resolusi pencarian", 1, 5, 1, help="Angka kecil lebih teliti, angka besar lebih cepat.")
    min_profit_target = st.number_input("Target profit minimal", min_value=0.0, value=4800.0, step=100.0)
    profit_tolerance = st.number_input("Toleransi target profit", min_value=1.0, value=650.0, step=50.0)

tab_concept, tab_input, tab_process, tab_result = st.tabs(
    ["Konsep", "Input Data", "Proses Fuzzy", "Hasil dan Visualisasi"]
)

with tab_concept:
    st.subheader("Cara Kerja Metode")
    st.markdown(
        """
        <div class="note-box">
        Fuzzy Optimization Planner dipakai ketika keputusan harus memenuhi banyak batas dan target,
        tetapi batas tersebut tidak selalu kaku. Contohnya modal boleh sedikit melewati rencana,
        jam kerja masih bisa lembur terbatas, atau target profit punya toleransi.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1, 1], gap="large")
    with col_left:
        st.markdown(
            """
            **Alur perhitungan**

            1. Tentukan variabel keputusan, misalnya jumlah unit tiap produk.
            2. Tentukan batas sumber daya, seperti modal, jam kerja, dan bahan baku.
            3. Beri toleransi fuzzy pada setiap batas atau target.
            4. Sistem membangkitkan banyak kandidat rencana.
            5. Setiap kandidat dihitung derajat kepuasannya pada semua batas dan target.
            6. Skor akhir diambil dari derajat terkecil, sehingga rencana terbaik adalah rencana yang paling seimbang.
            """
        )
    with col_right:
        st.markdown(
            """
            **Jenis masalah yang cocok**

            <ol type="a">
                <li>Perencanaan produksi dengan modal, waktu, dan bahan terbatas.</li>
                <li>Penyusunan anggaran beberapa program.</li>
                <li>Pembagian kapasitas kerja tim.</li>
                <li>Penentuan stok barang dengan target permintaan.</li>
                <li>Pemilihan komposisi paket, menu, atau layanan.</li>
                <li>Alokasi sumber daya ketika batasnya masih bisa ditoleransi.</li>
            </ol>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Makna Derajat Fuzzy")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("1.000", "Sangat memenuhi")
        st.caption("Nilai kandidat berada pada area ideal.")
    with col_b:
        st.metric("0.500", "Masih ditoleransi")
        st.caption("Nilai kandidat mulai melewati target, tetapi belum gagal.")
    with col_c:
        st.metric("0.000", "Tidak memenuhi")
        st.caption("Nilai kandidat sudah melewati batas toleransi.")

    st.markdown(
        """
        <div class="note-box">
        Untuk batas maksimum seperti modal dan jam kerja, derajat tetap 1 selama pemakaian masih di bawah batas ideal,
        lalu turun sampai 0 ketika melewati batas ideal + toleransi. Untuk target minimal seperti profit,
        derajat naik menuju 1 ketika profit mendekati atau melewati target.
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab_input:
    col_a, col_b = st.columns([1, 1], gap="large")
    with col_a:
        st.subheader("Sumber Daya")
        resources = editable_resources(default_resources)
    with col_b:
        st.subheader("Produk dan Kebutuhan")
        products = editable_products(default_products, resources)

    st.markdown(
        """
        <div class="note-box">
        Batas ideal diberi toleransi fuzzy. Pemakaian di bawah batas mendapat derajat 1,
        lalu turun bertahap sampai 0 ketika melewati batas + toleransi.
        </div>
        """,
        unsafe_allow_html=True,
    )

if not products or not resources:
    st.error("Minimal perlu satu produk dan satu sumber daya.")
    st.stop()

result = optimize_plan(products, resources, min_profit_target, profit_tolerance, step=step)
best = result.iloc[0]

with tab_process:
    st.subheader("Derajat Kepuasan Kandidat")
    process_columns = (
        [product.name for product in products]
        + ["Profit", "mu target profit"]
        + [f"{resource.name} terpakai" for resource in resources]
        + [f"{resource.name} mu" for resource in resources]
        + [f"{product.name} mu permintaan" for product in products]
        + ["Skor fuzzy", "Skor rata-rata"]
    )
    st.dataframe(display_table(result[process_columns].head(60)), use_container_width=True, height=420)

    st.subheader("Rumus Evaluasi")
    st.markdown(
        """
        <div class="note-box">
        Skor fuzzy memakai operator minimum: nilai akhir sebuah rencana adalah derajat kepuasan terendah
        dari semua target permintaan, batas sumber daya, dan target profit.
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab_result:
    metric_cols = st.columns(4)
    metric_cols[0].metric("Skor fuzzy terbaik", f"{best['Skor fuzzy']:.3f}")
    metric_cols[1].metric("Profit", f"{best['Profit']:,.0f}".replace(",", "."))
    metric_cols[2].metric("Jumlah kandidat", f"{len(result):,.0f}".replace(",", "."))
    metric_cols[3].metric("Resolusi", step)

    st.subheader("Rencana Terbaik")
    st.dataframe(display_table(pd.DataFrame([best])), use_container_width=True, height=120)

    col_chart, col_membership = st.columns([1.15, 1], gap="large")
    with col_chart:
        st.plotly_chart(
            plot_top_plans(result, [product.name for product in products]),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )
    with col_membership:
        st.plotly_chart(plot_membership(best, products, resources), use_container_width=True, config=PLOTLY_CONFIG)

    st.subheader("10 Kandidat Teratas")
    st.dataframe(display_table(result.head(10)), use_container_width=True, height=360)
