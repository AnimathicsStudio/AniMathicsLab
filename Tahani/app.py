from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from tahani_core import (
    FUZZY_TERMS,
    build_condition_frame,
    condition_token,
    default_sets,
    evaluate_query,
    first_text_column,
    fuzzify_dataframe,
    membership_value,
    normalize_query,
    numeric_columns,
    rank_results,
    sample_smartphones,
)


st.set_page_config(page_title="Fuzzy Tahani Explorer", layout="wide")

DEFAULT_DATA_PATH = Path(__file__).parent / "sample_data" / "smartphones_tahani.csv"
TERM_FROM_SLIDER = {0: "rendah", 1: "sedang", 2: "tinggi"}
TERM_COLORS = {"rendah": "#16a34a", "sedang": "#2563eb", "tinggi": "#dc2626"}
PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToKeep": ["toImage"],
    "scrollZoom": False,
    "doubleClick": False,
    "showTips": False,
}
DEFAULT_FEATURES = ["price_idr", "rating", "ram_gb", "battery_mah"]
FEATURE_HELP = {
    "price_idr": "rendah = lebih murah, tinggi = lebih mahal",
    "price": "rendah = lebih murah, tinggi = lebih mahal",
    "Harga": "rendah = lebih murah, tinggi = lebih mahal",
    "Harga Juta": "rendah = lebih murah, tinggi = lebih mahal",
    "rating": "rendah = rating kecil, tinggi = rating besar",
    "Rating": "rendah = rating kecil, tinggi = rating besar",
    "ram_gb": "rendah = RAM kecil, tinggi = RAM besar",
    "ram": "rendah = RAM kecil, tinggi = RAM besar",
    "storage_gb": "rendah = storage kecil, tinggi = storage besar",
    "RAM GB": "rendah = RAM kecil, tinggi = RAM besar",
    "Storage GB": "rendah = storage kecil, tinggi = storage besar",
    "battery_mah": "rendah = baterai kecil, tinggi = baterai besar",
    "battery": "rendah = baterai kecil, tinggi = baterai besar",
    "Baterai mAh": "rendah = baterai kecil, tinggi = baterai besar",
    "camera": "rendah = MP kecil, tinggi = MP besar",
    "rear_camera_max_mp": "rendah = MP kecil, tinggi = MP besar",
    "front_camera_mp": "rendah = MP kecil, tinggi = MP besar",
    "Kamera Utama MP": "rendah = MP kecil, tinggi = MP besar",
    "display": "rendah = layar kecil, tinggi = layar besar",
    "screen_size_in": "rendah = layar kecil, tinggi = layar besar",
    "clock_ghz": "rendah = clock rendah, tinggi = clock tinggi",
    "network_generation": "rendah = generasi lama, tinggi = generasi baru",
    "Layar Inci": "rendah = layar kecil, tinggi = layar besar",
    "Refresh Rate Hz": "rendah = refresh rate rendah, tinggi = refresh rate tinggi",
    "Berat Gram": "rendah = ringan, tinggi = berat",
    "os": "rendah = versi lama, tinggi = versi baru",
    "Android Versi": "rendah = versi lama, tinggi = versi baru",
}


def first_number(text: object) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", str(text).replace(",", ""))
    return float(match.group()) if match else None


def extract_with_pattern(text: object, pattern: str) -> float | None:
    match = re.search(pattern, str(text), flags=re.IGNORECASE)
    return float(match.group(1)) if match else None


def prepare_smartphone_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    if "price" in cleaned.columns:
        cleaned["price"] = cleaned["price"].apply(first_number)
    if "rating" in cleaned.columns:
        cleaned["rating"] = pd.to_numeric(cleaned["rating"], errors="coerce")
    if "ram" in cleaned.columns:
        cleaned["ram"] = cleaned["ram"].apply(lambda value: extract_with_pattern(value, r"(\d+(?:\.\d+)?)\s*\S*GB\s+RAM"))
    if "battery" in cleaned.columns:
        cleaned["battery"] = cleaned["battery"].apply(lambda value: extract_with_pattern(value, r"(\d+(?:\.\d+)?)\s*\S*mAh"))
    if "display" in cleaned.columns:
        cleaned["display"] = cleaned["display"].apply(lambda value: extract_with_pattern(value, r"(\d+(?:\.\d+)?)\s+inches"))
    if "camera" in cleaned.columns:
        cleaned["camera"] = cleaned["camera"].apply(lambda value: extract_with_pattern(value, r"(\d+(?:\.\d+)?)\s*\S*MP"))
    if "os" in cleaned.columns:
        cleaned["os"] = cleaned["os"].apply(lambda value: extract_with_pattern(value, r"Android\s+v?(\d+(?:\.\d+)?)"))
    for column in cleaned.columns:
        if cleaned[column].dtype == object:
            numeric = pd.to_numeric(cleaned[column], errors="coerce")
            if numeric.notna().mean() >= 0.9:
                cleaned[column] = numeric
    return cleaned


def load_data() -> pd.DataFrame:
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded is None:
        if DEFAULT_DATA_PATH.exists():
            return prepare_smartphone_data(pd.read_csv(DEFAULT_DATA_PATH))
        return sample_smartphones()
    return prepare_smartphone_data(pd.read_csv(uploaded))


def local_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1180px; padding-top: 1.25rem; }
        div[data-testid="stMetricValue"] { font-size: 1.25rem; }
        .result-note {
            border: 1px solid rgba(128, 128, 128, 0.28);
            border-radius: 8px;
            padding: 0.75rem 0.9rem;
            margin: 0.35rem 0 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def slider_term(feature: str, default: int) -> str:
    value = st.slider(
        feature,
        min_value=0,
        max_value=2,
        value=default,
        step=1,
        help=FEATURE_HELP.get(feature, "0 = rendah, 1 = sedang, 2 = tinggi"),
        key=f"slider_{feature}",
    )
    term = TERM_FROM_SLIDER[value]
    st.caption(f"Target: {term}")
    return term


def make_sets(df: pd.DataFrame, features: list[str]) -> dict:
    return {feature: default_sets(df[feature]) for feature in features}


def make_query(features: list[str], terms: dict[str, str], operator_text: str) -> str:
    parts = [f"{feature} {terms[feature]}" for feature in features]
    return f" {operator_text} ".join(parts)


def membership_plot_data(df: pd.DataFrame, feature: str, fuzzy_sets: dict) -> pd.DataFrame:
    values = pd.to_numeric(df[feature], errors="coerce").dropna()
    x_min = float(values.min())
    x_max = float(values.max())
    grid = {x_min + (x_max - x_min) * i / 240 for i in range(241)}
    for fuzzy_set in fuzzy_sets[feature].values():
        grid.update(fuzzy_set.points)
    rows = []
    for value in sorted(grid):
        for term in FUZZY_TERMS:
            rows.append(
                {
                    "Nilai": value,
                    "Derajat": membership_value(value, fuzzy_sets[feature][term]),
                    "Label": term,
                }
            )
    return pd.DataFrame(rows)


def format_number_id(value: object) -> object:
    if pd.isna(value) or not isinstance(value, (int, float)):
        return value
    if abs(value) >= 1000:
        if float(value).is_integer():
            return f"{int(value):,}".replace(",", ".")
        whole, decimal = f"{value:,.2f}".split(".")
        return f"{whole.replace(',', '.')},{decimal}"
    return value


def display_table(df: pd.DataFrame) -> pd.DataFrame:
    view = df.copy()
    for column in view.select_dtypes(include="number").columns:
        view[column] = view[column].map(format_number_id)
    return view


def membership_figure(df: pd.DataFrame, feature: str, fuzzy_sets: dict) -> go.Figure:
    plot_df = membership_plot_data(df, feature, fuzzy_sets)
    fig = go.Figure()
    for term in FUZZY_TERMS:
        term_df = plot_df[plot_df["Label"] == term]
        fig.add_trace(
            go.Scatter(
                x=term_df["Nilai"],
                y=term_df["Derajat"],
                mode="lines",
                name=term,
                line=dict(color=TERM_COLORS[term], width=3),
            )
        )

    fig.update_layout(
        height=310,
        margin=dict(l=10, r=10, t=34, b=10),
        title=feature,
        xaxis_title="Nilai",
        yaxis_title="Derajat",
        xaxis=dict(fixedrange=True),
        yaxis=dict(range=[0, 1.05], fixedrange=True),
        legend_title_text="",
        dragmode=False,
    )
    return fig


local_css()

st.title("Fuzzy Tahani Explorer")
st.caption("Pilih fitur numerik, geser rendah-sedang-tinggi, lalu lihat ranking kecocokan fuzzy.")

df = load_data()
number_cols = numeric_columns(df)
if not number_cols:
    st.error("Dataset perlu minimal 1 kolom numerik.")
    st.stop()

default_features = [feature for feature in DEFAULT_FEATURES if feature in number_cols]
if len(default_features) < 3:
    default_features = number_cols[:3]

with st.sidebar:
    st.header("Input")
    selected_features = st.multiselect(
        "Pilih fitur numerik",
        number_cols,
        default=default_features[:3],
    )
    if not selected_features:
        st.info("Pilih minimal 1 fitur agar slider dan output muncul.")
        st.stop()

    operator_text = st.radio(
        "Cara gabung",
        ["AND", "OR"],
        index=0,
        horizontal=True,
        help="AND = ambil nilai minimum. OR = ambil nilai maksimum.",
    )
fuzzy_sets = make_sets(df, selected_features)

default_slider = {
    "price_idr": 0,
    "price": 0,
    "Harga": 0,
    "Harga Juta": 0,
    "rating": 2,
    "Rating": 2,
    "ram_gb": 2,
    "ram": 2,
    "RAM GB": 2,
    "storage_gb": 2,
    "battery_mah": 2,
    "battery": 2,
    "Baterai mAh": 2,
    "Storage GB": 2,
    "camera": 2,
    "rear_camera_max_mp": 2,
    "front_camera_mp": 2,
    "Kamera Utama MP": 2,
    "display": 2,
    "screen_size_in": 2,
    "clock_ghz": 2,
    "network_generation": 2,
    "volte": 2,
    "nfc": 2,
    "ir_blaster": 2,
    "cpu_core_count": 2,
    "resolution_width_px": 2,
    "rear_camera_count": 2,
    "Refresh Rate Hz": 2,
    "Berat Gram": 0,
    "os": 2,
    "Android Versi": 2,
}
name_col = first_text_column(df)

tab_input, tab_process, tab_result = st.tabs(
    ["Input Data", "Proses Fuzzy", "Hasil dan Visualisasi"]
)

with tab_input:
    st.subheader("Dataset")
    st.caption("Dataset bawaan hanya contoh praktikum. Upload CSV dapat dipakai untuk data lain.")
    st.dataframe(display_table(df), use_container_width=True, hide_index=True)

terms = {
    feature: TERM_FROM_SLIDER[st.session_state.get(f"slider_{feature}", default_slider.get(feature, 1))]
    for feature in selected_features
}
query_text = make_query(selected_features, terms, operator_text)

token_lookup = {
    f"{feature} {term}": condition_token(feature, term)
    for feature in selected_features
    for term in FUZZY_TERMS
}
expression = normalize_query(query_text, token_lookup)
condition_df = build_condition_frame(df, selected_features, fuzzy_sets)
scores = evaluate_query(condition_df, expression)
ranked = rank_results(df, scores)
filtered = ranked.copy()
fuzzy_table = fuzzify_dataframe(df, selected_features, fuzzy_sets)

with tab_process:
    st.subheader("Proses Hitung Tahani")
    st.write("Query dari slider:")
    st.code(query_text, language="text")
    st.write("Ekspresi internal yang dihitung:")
    st.code(expression, language="text")

    st.markdown(
        f"""
        Operator yang dipakai: **{operator_text}**.
        Pada Model Tahani, **AND** dihitung dengan minimum, sedangkan **OR** dihitung dengan maksimum.
        """
    )

    st.subheader("Derajat Keanggotaan")
    st.dataframe(display_table(fuzzy_table), use_container_width=True, hide_index=True)

    st.subheader("Grafik Fungsi Keanggotaan")
    st.caption("Rendah = hijau, sedang = biru, tinggi = merah.")
    grid_cols = st.columns(2)
    for index, feature in enumerate(selected_features):
        with grid_cols[index % 2]:
            fig = membership_figure(df, feature, fuzzy_sets)
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    st.subheader("Derajat Kondisi dan Skor Akhir")
    condition_view = condition_df.copy()
    if name_col:
        condition_view.insert(0, name_col, df[name_col])
    condition_view["Derajat Cocok"] = scores
    st.dataframe(display_table(condition_view), use_container_width=True)

with tab_result:
    st.subheader("Pilih Preferensi")
    slider_column_count = min(4, max(2, len(selected_features)))
    slider_cols = st.columns(slider_column_count)
    terms = {}
    for index, feature in enumerate(selected_features):
        with slider_cols[index % slider_column_count]:
            terms[feature] = slider_term(feature, default_slider.get(feature, 1))

    query_text = make_query(selected_features, terms, operator_text)
    expression = normalize_query(query_text, token_lookup)
    scores = evaluate_query(condition_df, expression)
    ranked = rank_results(df, scores)
    filtered = ranked.copy()
    chart_results = filtered.head(15).copy()

    st.markdown(
        f"""
        <div class="result-note">
        Query aktif: <strong>{query_text}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Ranking Hasil")
    best = filtered.iloc[0]
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Item teratas", str(best[name_col]) if name_col else "Baris pertama")
    with metric_cols[1]:
        st.metric("Derajat cocok", f"{best['Derajat Cocok']:.3f}")
    with metric_cols[2]:
        st.metric("Fitur dipakai", str(len(selected_features)))
    with metric_cols[3]:
        st.metric("Data tabel", str(len(filtered)))

    display_cols = ["Ranking"]
    if name_col:
        display_cols.append(name_col)
    display_cols += selected_features + ["Derajat Cocok"]

    left, right = st.columns([1.15, 0.85])
    with left:
        st.dataframe(display_table(filtered[display_cols]), use_container_width=True, hide_index=True)

    with right:
        chart_label = name_col if name_col else "Ranking"
        chart_df = chart_results.reset_index(drop=True).copy()
        chart_df["Urutan Chart"] = chart_df.index + 1
        chart_df["Label Chart"] = chart_df.apply(
            lambda row: f"{int(row['Urutan Chart'])}. {row[chart_label]}",
            axis=1,
        )
        fig = px.bar(
            chart_df,
            x="Derajat Cocok",
            y="Label Chart",
            orientation="h",
            range_x=[0, 1],
        )
        fig.update_traces(
            hovertemplate="%{y}<br>Derajat cocok: %{x:.4f}<extra></extra>",
        )
        fig.update_layout(
            height=max(430, 30 * len(chart_df) + 90),
            margin=dict(l=10, r=20, t=20, b=10),
            xaxis_title="Derajat cocok",
            yaxis_title="",
            showlegend=False,
            dragmode=False,
            xaxis=dict(fixedrange=True, range=[0, 1]),
            yaxis=dict(
                fixedrange=True,
                categoryorder="array",
                categoryarray=chart_df["Label Chart"].tolist(),
                autorange="reversed",
            ),
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
