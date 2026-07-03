from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from clustering_core import (
    cluster_profile,
    first_text_column,
    inverse_centers,
    membership_for_point,
    membership_table,
    numeric_columns,
    prepare_matrix,
    run_fcm,
    sample_customer_data,
)


st.set_page_config(page_title="Fuzzy Clustering and Classification Lab", layout="wide")

PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToKeep": ["toImage"],
    "scrollZoom": False,
    "doubleClick": False,
    "showTips": False,
}
CLUSTER_COLORS = [
    "#e6194b",
    "#3cb44b",
    "#4363d8",
    "#f58231",
    "#911eb4",
    "#46f0f0",
    "#f032e6",
    "#808000",
]


def load_data() -> pd.DataFrame:
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded is None:
        return sample_customer_data()
    return pd.read_csv(uploaded)


def format_number_id(value: object) -> str:
    if pd.isna(value) or not isinstance(value, (int, float)):
        return ""
    if abs(value) >= 1000:
        if float(value).is_integer():
            return f"{int(value):,}".replace(",", ".")
        whole, decimal = f"{value:,.2f}".split(".")
        return f"{whole.replace(',', '.')},{decimal}"
    return f"{value:g}"


def display_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    formatters = {column: format_number_id for column in df.select_dtypes(include="number").columns}
    return df.style.format(formatters)


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


local_css()

st.title("Fuzzy Clustering and Classification Lab")
st.caption("Eksplorasi Fuzzy C-Means: data dapat menjadi anggota beberapa cluster sekaligus.")

df = load_data()
number_cols = numeric_columns(df)
if len(number_cols) < 2:
    st.error("Dataset perlu minimal 2 kolom numerik.")
    st.stop()

default_features = [
    col
    for col in ["belanja_bulanan", "frekuensi_transaksi", "nilai_keranjang", "kepuasan", "loyalitas"]
    if col in number_cols
]
if len(default_features) < 2:
    default_features = number_cols[: min(4, len(number_cols))]

with st.sidebar:
    st.header("Input")
    features = st.multiselect("Pilih fitur numerik", number_cols, default=default_features)
    if len(features) < 2:
        st.info("Pilih minimal 2 fitur untuk clustering.")
        st.stop()

    n_clusters = st.slider("Jumlah cluster", 2, min(8, len(df)), 4 if len(df) >= 4 else 2)
    fuzziness = st.slider("Parameter fuzziness (m)", 1.2, 3.0, 2.0, 0.1)
    max_iter = st.slider("Maksimum iterasi", 25, 300, 150, 25)
    seed = st.number_input("Seed", min_value=1, max_value=9999, value=41, step=1)

x_scaled, mean, std = prepare_matrix(df, features)
fcm = run_fcm(
    x_scaled,
    n_clusters=n_clusters,
    m=fuzziness,
    max_iter=max_iter,
    seed=int(seed),
)
centers = inverse_centers(fcm["centers_scaled"], mean, std, features)
name_col = first_text_column(df)
memberships = membership_table(df, fcm["membership"], fcm["labels"], name_col)
profiles = cluster_profile(df, features, fcm["labels"])

tab_input, tab_process, tab_result, tab_classification = st.tabs(
    ["Input Data", "Proses Fuzzy", "Hasil dan Visualisasi", "Klasifikasi"]
)

with tab_input:
    st.subheader("Dataset")
    st.caption("Dataset bawaan adalah contoh segmentasi pelanggan. Upload CSV dapat dipakai untuk kasus lain.")
    st.dataframe(display_table(df), use_container_width=True, hide_index=True)

    st.subheader("Fitur Terpilih")
    st.dataframe(display_table(df[features].describe().T.reset_index().rename(columns={"index": "fitur"})), use_container_width=True, hide_index=True)

with tab_process:
    st.subheader("Proses Fuzzy C-Means")
    st.markdown(
        f"""
        <div class="note-box">
        Jumlah cluster: <strong>{n_clusters}</strong><br>
        Parameter fuzziness m: <strong>{fuzziness:.1f}</strong><br>
        Iterasi sampai berhenti: <strong>{fcm["iterations"]}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Derajat Keanggotaan")
    st.dataframe(display_table(memberships), use_container_width=True, hide_index=True)

    st.subheader("Pusat Cluster")
    st.dataframe(display_table(centers), use_container_width=True, hide_index=True)

    st.subheader("Objektif per Iterasi")
    objective_df = pd.DataFrame(
        {"iterasi": range(1, len(fcm["objectives"]) + 1), "nilai_objektif": fcm["objectives"]}
    )
    fig = px.line(objective_df, x="iterasi", y="nilai_objektif", markers=True)
    fig.update_layout(
        height=360,
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
        dragmode=False,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

with tab_result:
    st.subheader("Hasil dan Visualisasi")
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Jumlah data", str(len(df)))
    with metric_cols[1]:
        st.metric("Fitur dipakai", str(len(features)))
    with metric_cols[2]:
        st.metric("Cluster", str(n_clusters))
    with metric_cols[3]:
        st.metric("Iterasi", str(fcm["iterations"]))

    st.subheader("Profil Cluster")
    st.dataframe(display_table(profiles), use_container_width=True, hide_index=True)

    st.subheader("Scatter Plot Cluster")
    x_axis = st.selectbox("Sumbu X", features, index=0)
    y_default = 1 if len(features) > 1 else 0
    y_axis = st.selectbox("Sumbu Y", features, index=y_default)
    plot_df = df.copy()
    plot_df["cluster"] = [f"Cluster {label + 1}" for label in fcm["labels"]]
    plot_df["derajat_dominan"] = fcm["membership"].max(axis=1)
    hover_cols = [name_col] if name_col else []
    fig = px.scatter(
        plot_df,
        x=x_axis,
        y=y_axis,
        color="cluster",
        color_discrete_sequence=CLUSTER_COLORS,
        size="derajat_dominan",
        hover_data=hover_cols + features,
    )
    fig.update_layout(
        height=520,
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
        dragmode=False,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

with tab_classification:
    st.subheader("Klasifikasi Sederhana")
    st.caption("Data baru diklasifikasikan ke cluster dengan pusat terdekat. Nilai similarity hanya indikator kedekatan.")

    input_cols = st.columns(min(4, max(2, len(features))))
    new_values = {}
    for idx, feature in enumerate(features):
        series = pd.to_numeric(df[feature], errors="coerce")
        min_value = float(series.min())
        max_value = float(series.max())
        default_value = float(series.median())
        with input_cols[idx % len(input_cols)]:
            new_values[feature] = st.number_input(
                feature,
                min_value=min_value,
                max_value=max_value,
                value=default_value,
            )

    new_row = pd.Series(new_values)
    new_membership = membership_for_point(
        new_row[features].to_numpy(dtype=float),
        fcm["centers_scaled"],
        mean,
        std,
        m=fuzziness,
    )
    best_idx = int(new_membership.argmax())
    predicted_cluster = f"Cluster {best_idx + 1}"
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Prediksi cluster", predicted_cluster)
    with col_b:
        st.metric("Derajat dominan", f"{new_membership[best_idx]:.4f}")

    st.subheader("Derajat Keanggotaan Data Baru")
    new_membership_df = pd.DataFrame(
        {
            "cluster": [f"Cluster {idx + 1}" for idx in range(len(new_membership))],
            "derajat_keanggotaan": new_membership.round(4),
        }
    )
    st.dataframe(new_membership_df, use_container_width=True, hide_index=True)

    st.subheader("Jarak ke Pusat Cluster")
    distances = []
    for _, center in centers.iterrows():
        distance = sum((float(new_row[f]) - float(center[f])) ** 2 for f in features) ** 0.5
        distances.append({"cluster": center["cluster"], "jarak": round(distance, 4)})
    st.dataframe(pd.DataFrame(distances), use_container_width=True, hide_index=True)
