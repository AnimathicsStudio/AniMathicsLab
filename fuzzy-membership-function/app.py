from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from membership_core import (
    COLORS,
    PRESETS,
    SHAPE_POINT_COUNT,
    FuzzySet,
    alpha_cut_intervals,
    degree_table,
    display_table,
    plot_rows,
    validate_set,
)


st.set_page_config(page_title="Fuzzy Membership Function Lab", layout="wide")

PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToKeep": ["toImage"],
    "scrollZoom": False,
    "doubleClick": False,
    "showTips": False,
}


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
        .formula {
            font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.7rem 0.85rem;
            margin: 0.35rem 0 0.65rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_editor(default_sets: list[FuzzySet], domain: tuple[float, float]) -> list[FuzzySet]:
    rows = []
    for fuzzy_set in default_sets:
        points = list(fuzzy_set.points) + [None] * (4 - len(fuzzy_set.points))
        rows.append(
            {
                "Label": fuzzy_set.label,
                "Bentuk": fuzzy_set.shape,
                "Titik 1": points[0],
                "Titik 2": points[1],
                "Titik 3": points[2],
                "Titik 4": points[3],
                "Warna": fuzzy_set.color,
            }
        )

    edited = st.data_editor(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Label": st.column_config.TextColumn(required=True),
            "Bentuk": st.column_config.SelectboxColumn(options=list(SHAPE_POINT_COUNT.keys()), required=True),
            "Titik 1": st.column_config.NumberColumn(min_value=domain[0], max_value=domain[1], step=0.1),
            "Titik 2": st.column_config.NumberColumn(min_value=domain[0], max_value=domain[1], step=0.1),
            "Titik 3": st.column_config.NumberColumn(min_value=domain[0], max_value=domain[1], step=0.1),
            "Titik 4": st.column_config.NumberColumn(min_value=domain[0], max_value=domain[1], step=0.1),
            "Warna": st.column_config.TextColumn(help="Kode warna hex, misalnya #2563eb."),
        },
    )

    sets = []
    fallback_colors = list(COLORS.values())
    for idx, row in edited.iterrows():
        label = str(row["Label"]).strip()
        shape = str(row["Bentuk"]).strip()
        if not label or shape not in SHAPE_POINT_COUNT:
            continue
        point_columns = ["Titik 1", "Titik 2", "Titik 3", "Titik 4"][: SHAPE_POINT_COUNT[shape]]
        points = []
        for column in point_columns:
            if pd.isna(row[column]):
                points = []
                break
            points.append(float(row[column]))
        if not points:
            continue
        color = str(row.get("Warna") or fallback_colors[idx % len(fallback_colors)]).strip()
        sets.append(FuzzySet(label=label, shape=shape, points=tuple(points), color=color))
    return sets


def membership_figure(plot_df: pd.DataFrame, sets: list[FuzzySet], crisp: float, unit: str) -> go.Figure:
    fig = go.Figure()
    for fuzzy_set in sets:
        set_df = plot_df[plot_df["Himpunan"] == fuzzy_set.label]
        fig.add_trace(
            go.Scatter(
                x=set_df["Nilai"],
                y=set_df["Derajat"],
                mode="lines",
                name=fuzzy_set.label,
                line=dict(color=fuzzy_set.color, width=3),
            )
        )

    fig.add_vline(x=crisp, line_width=2, line_color="#111827", opacity=0.65)
    fig.add_annotation(
        x=crisp,
        y=1.04,
        text=f"nilai crisp = {crisp:g} {unit}",
        showarrow=False,
        font=dict(size=12, color="#111827"),
    )
    fig.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=40, b=20),
        legend_title_text="Himpunan",
        xaxis=dict(title=f"Nilai ({unit})" if unit else "Nilai", fixedrange=True),
        yaxis=dict(title="Derajat keanggotaan", range=[0, 1.08], fixedrange=True),
        hovermode="x unified",
    )
    return fig


def bar_figure(degrees: pd.DataFrame, sets: list[FuzzySet]) -> go.Figure:
    color_map = {fuzzy_set.label: fuzzy_set.color for fuzzy_set in sets}
    fig = px.bar(
        degrees,
        x="Derajat keanggotaan",
        y="Himpunan fuzzy",
        orientation="h",
        color="Himpunan fuzzy",
        color_discrete_map=color_map,
        text="Derajat keanggotaan",
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.update_layout(
        height=max(280, 58 * len(degrees)),
        showlegend=False,
        margin=dict(l=10, r=35, t=20, b=20),
        xaxis=dict(range=[0, 1.08], fixedrange=True),
        yaxis=dict(fixedrange=True, autorange="reversed"),
    )
    return fig


local_css()

st.title("Fuzzy Membership Function Lab")
st.caption("Membangun, menggeser, dan membaca derajat keanggotaan dari fungsi fuzzy.")

with st.sidebar:
    st.header("Variabel")
    preset_name = st.selectbox("Preset", list(PRESETS.keys()))
    preset = PRESETS[preset_name]
    variable_name = preset.name
    unit = preset.unit
    st.caption(f"Variabel: {variable_name} | Satuan: {unit}")
    domain_min, domain_max = st.slider(
        "Domain",
        min_value=float(preset.domain[0]),
        max_value=float(preset.domain[1]),
        value=(float(preset.domain[0]), float(preset.domain[1])),
        step=(preset.domain[1] - preset.domain[0]) / 100,
    )
    if domain_max <= domain_min:
        st.error("Domain maksimum harus lebih besar dari domain minimum.")
        st.stop()
    crisp = st.slider(
        "Nilai crisp",
        min_value=float(domain_min),
        max_value=float(domain_max),
        value=float(min(max(preset.crisp, domain_min), domain_max)),
        step=(domain_max - domain_min) / 200,
    )

domain = (float(domain_min), float(domain_max))

tab_concept, tab_input, tab_process, tab_visual = st.tabs(["Konsep", "Input Data", "Proses Fuzzy", "Visualisasi"])

with tab_concept:
    st.subheader("Apa yang Dipelajari")
    st.markdown(
        """
        <div class="note-box">
        Fungsi keanggotaan mengubah nilai tegas menjadi derajat fuzzy antara 0 dan 1.
        Dengan cara ini, sebuah nilai tidak harus langsung masuk satu kelas saja.
        Misalnya suhu 28 C bisa cukup normal sekaligus mulai panas.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1, 1], gap="large")
    with col_left:
        st.markdown(
            """
            **Bentuk yang tersedia**

            - Bahu kiri: cocok untuk kategori rendah, murah, dingin, dekat.
            - Segitiga: cocok untuk kategori tengah yang punya satu puncak.
            - Trapesium: cocok untuk kategori ideal yang punya rentang puncak.
            - Bahu kanan: cocok untuk kategori tinggi, mahal, panas, jauh.
            """
        )
    with col_right:
        st.markdown(
            """
            **Kegunaan praktis**

            - Menentukan label fuzzy dari nilai sensor.
            - Membuat input untuk FIS Mamdani, Sugeno, atau Tsukamoto.
            - Menjelaskan batas rendah, sedang, tinggi secara visual.
            - Mengecek apakah titik parameter sudah masuk akal.
            """
        )

    st.subheader("Rumus Umum")
    st.markdown(
        """
        <div class="formula">
        mu(x) = 0 berarti tidak menjadi anggota.<br>
        mu(x) = 1 berarti anggota penuh.<br>
        0 &lt; mu(x) &lt; 1 berarti anggota sebagian.
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab_input:
    st.subheader("Parameter Himpunan Fuzzy")
    fuzzy_sets = set_editor(preset.sets, domain)
    errors = [error for fuzzy_set in fuzzy_sets if (error := validate_set(fuzzy_set, domain))]
    if errors:
        for error in errors:
            st.error(error)
        st.stop()
    if not fuzzy_sets:
        st.error("Minimal perlu satu himpunan fuzzy yang valid.")
        st.stop()

    st.markdown(
        """
        <div class="note-box">
        Titik harus berurutan dari kecil ke besar. Untuk bahu kiri/kanan gunakan 2 titik,
        segitiga 3 titik, dan trapesium 4 titik.
        </div>
        """,
        unsafe_allow_html=True,
    )

plot_df = plot_rows(domain, fuzzy_sets)
degrees = degree_table(float(crisp), fuzzy_sets)
dominant = degrees.iloc[0]

with tab_process:
    metric_cols = st.columns(4)
    metric_cols[0].metric("Variabel", variable_name)
    metric_cols[1].metric("Nilai crisp", f"{crisp:g} {unit}")
    metric_cols[2].metric("Dominan", str(dominant["Himpunan fuzzy"]))
    metric_cols[3].metric("Derajat dominan", f"{dominant['Derajat keanggotaan']:.3f}")

    st.subheader("Derajat Keanggotaan")
    st.dataframe(display_table(degrees), use_container_width=True, hide_index=True)

    st.subheader("Alpha-cut")
    alpha = st.slider("Nilai alpha", 0.0, 1.0, 0.5, 0.05)
    alpha_df = alpha_cut_intervals(fuzzy_sets, alpha, domain)
    st.dataframe(alpha_df, use_container_width=True, hide_index=True)

    st.subheader("Sampel Kurva")
    st.dataframe(display_table(plot_df.head(120)), use_container_width=True, hide_index=True, height=320)

with tab_visual:
    col_chart, col_bar = st.columns([1.25, 1], gap="large")
    with col_chart:
        st.plotly_chart(membership_figure(plot_df, fuzzy_sets, float(crisp), unit), use_container_width=True, config=PLOTLY_CONFIG)
    with col_bar:
        st.plotly_chart(bar_figure(degrees, fuzzy_sets), use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown(
        f"""
        <div class="note-box">
        Pada nilai crisp <b>{crisp:g} {unit}</b>, himpunan paling kuat adalah
        <b>{dominant["Himpunan fuzzy"]}</b> dengan derajat <b>{dominant["Derajat keanggotaan"]:.3f}</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )
