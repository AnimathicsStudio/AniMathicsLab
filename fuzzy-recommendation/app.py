from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from recommendation_core import (
    FEATURES,
    PERSONAS,
    TERM_FROM_SLIDER,
    display_table,
    load_default_data,
    numeric_feature_columns,
    reason_for_item,
    recommend,
)


st.set_page_config(page_title="Fuzzy Recommendation Lab", layout="wide")

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
        .query-note {
            border: 1px solid rgba(128, 128, 128, 0.28);
            border-radius: 8px;
            padding: 0.75rem 0.9rem;
            margin: 0.35rem 0 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_data() -> pd.DataFrame:
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded is None:
        return load_default_data(Path(__file__).parent)
    return pd.read_csv(uploaded)


local_css()

st.title("Fuzzy Recommendation Lab")
st.caption("Rekomendasi personal berbasis kecocokan fuzzy terhadap preferensi pengguna.")

df = load_data()
available_features = numeric_feature_columns(df)
if not available_features:
    st.error("Dataset tidak memiliki kolom numerik yang dikenali untuk rekomendasi.")
    st.stop()

with st.sidebar:
    st.header("Preferensi")
    persona_name = st.selectbox("Preset persona", list(PERSONAS.keys()) + ["Kustom"])
    if persona_name != "Kustom":
        persona = PERSONAS[persona_name]
        default_features = [feature for feature in persona["terms"] if feature in available_features]
    else:
        default_features = [feature for feature in ["price_idr", "rating", "ram_gb", "battery_mah"] if feature in available_features]
    if not default_features:
        default_features = available_features[: min(4, len(available_features))]

    selected_features = st.multiselect(
        "Fitur rekomendasi",
        available_features,
        default=default_features,
    )
    if not selected_features:
        st.info("Pilih minimal satu fitur.")
        st.stop()

terms = {}
weights = {}
tab_input, tab_process, tab_result = st.tabs(["Input Data", "Proses Fuzzy", "Hasil Rekomendasi"])

with tab_input:
    st.subheader("Dataset")
    st.caption("Dataset bawaan memakai data smartphone bersih. Upload CSV dapat dipakai untuk dataset lain dengan kolom yang sesuai.")
    st.dataframe(display_table(df), use_container_width=True, hide_index=True)

with tab_result:
    st.subheader("Atur Preferensi")
    persona = PERSONAS.get(persona_name, {"terms": {}, "weights": {}})
    feature_cols = st.columns(min(4, max(2, len(selected_features))))
    for idx, feature in enumerate(selected_features):
        meta = FEATURES[feature]
        default_term = persona["terms"].get(feature, "sedang")
        default_value = {"rendah": 0, "sedang": 1, "tinggi": 2}[default_term]
        default_weight = int(persona["weights"].get(feature, 3))
        with feature_cols[idx % len(feature_cols)]:
            value = st.slider(
                meta["label"],
                min_value=0,
                max_value=2,
                value=default_value,
                step=1,
                key=f"term_{feature}",
                help="0 = rendah, 1 = sedang, 2 = tinggi",
            )
            terms[feature] = TERM_FROM_SLIDER[value]
            st.caption(f"Target: {terms[feature]}")
            weights[feature] = st.slider(
                f"Kepentingan {meta['label']}",
                min_value=1,
                max_value=5,
                value=default_weight,
                key=f"weight_{feature}",
            )

    result, details = recommend(df, selected_features, terms, weights)
    top_result = result.head(10).copy()
    best = top_result.iloc[0]

    query_text = ", ".join(f"{FEATURES[f]['label']} {terms[f]} (bobot {weights[f]})" for f in selected_features)
    st.markdown(
        f"""
        <div class="query-note">
        Preferensi aktif: <strong>{query_text}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Rekomendasi teratas", str(best["model"]) if "model" in best else "Item pertama")
    with metric_cols[1]:
        st.metric("Skor cocok", f"{best['Skor Cocok']:.4f}")
    with metric_cols[2]:
        st.metric("Fitur dipakai", str(len(selected_features)))
    with metric_cols[3]:
        st.metric("Data dinilai", str(len(result)))

    display_cols = ["Ranking"]
    if "model" in result.columns:
        display_cols.append("model")
    display_cols += selected_features + ["Skor Cocok"]

    left, right = st.columns([1.15, 0.85])
    with left:
        table = top_result[display_cols].copy()
        table["Alasan"] = [
            reason_for_item(row, selected_features, terms, details.loc[row["_source_index"]])
            for _, row in top_result.iterrows()
        ]
        st.dataframe(display_table(table), use_container_width=True, hide_index=True)

    with right:
        chart_df = top_result.reset_index(drop=True).copy()
        label_col = "model" if "model" in chart_df.columns else "Ranking"
        chart_df["Label Chart"] = chart_df.apply(lambda row: f"{int(row.name) + 1}. {row[label_col]}", axis=1)
        fig = px.bar(
            chart_df,
            x="Skor Cocok",
            y="Label Chart",
            orientation="h",
            range_x=[0, 1],
        )
        fig.update_traces(hovertemplate="%{y}<br>Skor cocok: %{x:.4f}<extra></extra>")
        fig.update_layout(
            height=430,
            margin=dict(l=10, r=20, t=20, b=10),
            xaxis_title="Skor cocok",
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

with tab_process:
    st.subheader("Proses Fuzzy")
    if not terms:
        st.info("Atur preferensi di tab Hasil Rekomendasi untuk melihat proses.")
    else:
        result, details = recommend(df, selected_features, terms, weights)
        st.write("Target preferensi dan bobot:")
        pref_df = pd.DataFrame(
            [
                {
                    "fitur": feature,
                    "label": FEATURES[feature]["label"],
                    "target": terms[feature],
                    "bobot": weights[feature],
                    "tipe": FEATURES[feature]["type"],
                }
                for feature in selected_features
            ]
        )
        st.dataframe(pref_df, use_container_width=True, hide_index=True)

        st.write("Skor kecocokan per fitur:")
        process_df = pd.DataFrame()
        if "model" in df.columns:
            process_df["model"] = df["model"]
        for feature in selected_features:
            process_df[f"{feature}_match"] = details[f"{feature}_match"]
        process_df["Skor Cocok"] = details["Skor Cocok"]
        st.dataframe(display_table(process_df), use_container_width=True, hide_index=True)
