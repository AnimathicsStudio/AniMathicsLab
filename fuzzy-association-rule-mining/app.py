from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from association_core import (
    categorical_columns,
    categorical_items,
    fuzzify_numeric_items,
    mine_rules,
    numeric_columns,
    sample_transaction_data,
)


st.set_page_config(page_title="Fuzzy Association Rule Mining Lab", layout="wide")

PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToKeep": ["toImage"],
    "scrollZoom": False,
    "doubleClick": False,
    "showTips": False,
}


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


def load_data() -> pd.DataFrame:
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded is None:
        return sample_transaction_data()
    return pd.read_csv(uploaded)


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

st.title("Fuzzy Association Rule Mining Lab")
st.caption("Temukan pola hubungan dari data transaksi setelah atribut numerik difuzzifikasi.")

df = load_data()
num_cols = numeric_columns(df)
cat_cols = [column for column in categorical_columns(df) if column.lower() not in {"id", "id_transaksi"}]
if not num_cols and not cat_cols:
    st.error("Dataset perlu minimal satu kolom numerik atau kategorik.")
    st.stop()

default_numeric = [col for col in ["frekuensi_belanja", "nilai_belanja", "jumlah_item", "respons_promo"] if col in num_cols]
if not default_numeric:
    default_numeric = num_cols[: min(4, len(num_cols))]

with st.sidebar:
    st.header("Input")
    selected_numeric = st.multiselect("Atribut numerik untuk fuzzifikasi", num_cols, default=default_numeric)
    selected_categorical = st.multiselect("Atribut kategorik", cat_cols, default=cat_cols[:1])
    min_support = st.slider("Minimum support", 0.01, 0.60, 0.08, 0.01)
    min_confidence = st.slider("Minimum confidence", 0.05, 1.00, 0.45, 0.05)
    max_antecedent = st.slider("Maksimum panjang antecedent", 1, 3, 2)

numeric_item_df = fuzzify_numeric_items(df, selected_numeric) if selected_numeric else pd.DataFrame(index=df.index)
categorical_item_df = categorical_items(df, selected_categorical) if selected_categorical else pd.DataFrame(index=df.index)
item_df = pd.concat([numeric_item_df, categorical_item_df], axis=1)

if item_df.empty:
    st.error("Pilih minimal satu atribut untuk membentuk item fuzzy.")
    st.stop()

rules = mine_rules(
    item_df,
    min_support=min_support,
    min_confidence=min_confidence,
    max_antecedent=max_antecedent,
)

tab_input, tab_process, tab_result = st.tabs(["Input Data", "Proses Fuzzy", "Hasil Aturan"])

with tab_input:
    st.subheader("Dataset")
    st.caption("Dataset bawaan adalah transaksi pelanggan sintetis untuk praktikum. Upload CSV dapat dipakai untuk kasus lain.")
    st.dataframe(display_table(df), use_container_width=True, hide_index=True)

with tab_process:
    st.subheader("Item Fuzzy")
    st.markdown(
        f"""
        <div class="note-box">
        Item numerik fuzzy: <strong>{len(numeric_item_df.columns)}</strong><br>
        Item kategorik: <strong>{len(categorical_item_df.columns)}</strong><br>
        Total item: <strong>{len(item_df.columns)}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(display_table(item_df.round(4)), use_container_width=True)

    st.subheader("Support Item Tunggal")
    support_df = pd.DataFrame(
        {
            "item": item_df.columns,
            "support": [round(float(item_df[column].mean()), 4) for column in item_df.columns],
        }
    ).sort_values("support", ascending=False)
    st.dataframe(support_df, use_container_width=True, hide_index=True)

    fig = px.bar(support_df.head(20), x="support", y="item", orientation="h", range_x=[0, 1])
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=20, t=20, b=10),
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True, autorange="reversed"),
        dragmode=False,
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

with tab_result:
    st.subheader("Aturan Asosiasi")
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Jumlah data", str(len(df)))
    with metric_cols[1]:
        st.metric("Jumlah item", str(len(item_df.columns)))
    with metric_cols[2]:
        st.metric("Aturan lolos", str(len(rules)))
    with metric_cols[3]:
        st.metric("Min support", f"{min_support:.2f}")

    if rules.empty:
        st.warning("Belum ada aturan yang lolos. Turunkan minimum support atau confidence.")
    else:
        st.dataframe(display_table(rules), use_container_width=True, hide_index=True)

        st.subheader("Aturan Terbaik")
        best = rules.iloc[0]
        st.markdown(
            f"""
            <div class="note-box">
            <strong>{best['antecedent']}</strong> → <strong>{best['consequent']}</strong><br>
            Support: <strong>{best['support']:.4f}</strong>,
            Confidence: <strong>{best['confidence']:.4f}</strong>,
            Lift: <strong>{best['lift']:.4f}</strong><br>
            {best['interpretasi']}
            </div>
            """,
            unsafe_allow_html=True,
        )

        chart_df = rules.head(20).reset_index(drop=True).copy()
        chart_df["aturan"] = chart_df.apply(lambda row: f"{row.name + 1}. {row['antecedent']} -> {row['consequent']}", axis=1)
        fig = px.bar(chart_df, x="lift", y="aturan", orientation="h")
        fig.update_layout(
            height=600,
            margin=dict(l=10, r=20, t=20, b=10),
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True, autorange="reversed"),
            dragmode=False,
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
