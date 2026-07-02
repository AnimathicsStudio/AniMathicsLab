import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from forecasting_core import (
    clean_timeseries,
    evaluate_forecast,
    forecast_series,
    make_intervals,
    midpoint_for_state,
    sample_sales_data,
)


st.set_page_config(
    page_title="Fuzzy Forecasting Lab",
    page_icon="F",
    layout="wide",
)


st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-size: 14px; }
    .block-container { padding-top: 1.05rem; padding-bottom: 1rem; max-width: 1380px; }
    h1 { font-size: 1.75rem !important; margin-bottom: 0.15rem !important; }
    h2 { font-size: 1.25rem !important; margin-top: 0.55rem !important; margin-bottom: 0.35rem !important; }
    h3 { font-size: 1.02rem !important; margin-top: 0.45rem !important; margin-bottom: 0.25rem !important; }
    p, li, label, .stMarkdown, .stCaption { font-size: 0.93rem !important; line-height: 1.38 !important; }
    div[data-testid="stSidebar"] { min-width: 260px; max-width: 260px; }
    div[data-baseweb="tab-list"] { gap: 0.15rem; }
    button[data-baseweb="tab"] { height: 2rem; padding: 0 0.55rem; font-size: 0.82rem; }
    .stAlert { padding-top: 0.45rem; padding-bottom: 0.45rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": False,
    "doubleClick": False,
    "showTips": False,
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "zoom", "pan", "select", "lasso", "zoomIn", "zoomOut", "autoScale",
        "resetScale", "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d",
        "zoomOut2d", "autoScale2d", "resetScale2d", "hoverClosestCartesian",
        "hoverCompareCartesian", "toggleSpikelines",
    ],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "fuzzy_forecasting_chart",
        "height": 720,
        "width": 1280,
        "scale": 2,
    },
}


def table_height(df, max_height=520):
    return min(max_height, 42 + max(1, len(df.index)) * 38)


def table_config(df):
    config = {}
    for col in df.columns:
        if col in ["Tanggal"]:
            config[col] = st.column_config.Column(col, width=130)
        elif col in ["Relasi", "Tujuan", "Tujuan Unik", "Keterangan", "Langkah", "Hasil"]:
            config[col] = st.column_config.Column(col, width=240)
        elif col in ["No", "State", "Dari", "Ke"]:
            config[col] = st.column_config.Column(col, width=80)
        else:
            config[col] = st.column_config.Column(col, width=120)
    return config


def show_table(df, formatter=None, column_config=None):
    config = column_config if column_config is not None else table_config(df)
    if formatter:
        st.dataframe(
            df.style.format(formatter),
            width="content",
            hide_index=True,
            height=table_height(df),
            column_config=config,
        )
    else:
        st.dataframe(
            df,
            width="content",
            hide_index=True,
            height=table_height(df),
            column_config=config,
        )


def locked_choice(label, options, default_index=0):
    if hasattr(st, "segmented_control") and len(options) <= 4:
        return st.segmented_control(label, options, default=options[default_index])
    return st.radio(label, options, index=default_index, horizontal=True)


def plot_actual(data):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["Tanggal"],
            y=data["Nilai"],
            mode="lines+markers",
            name="Aktual",
            line=dict(color="#2563eb", width=3),
        )
    )
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Tanggal",
        yaxis_title="Nilai",
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def plot_intervals(data, intervals):
    fig = plot_actual(data)
    colors = ["rgba(22,163,74,0.08)", "rgba(37,99,235,0.08)", "rgba(220,38,38,0.08)"]
    for idx, row in intervals.iterrows():
        fig.add_hrect(
            y0=row["Batas Bawah"],
            y1=row["Batas Atas"],
            fillcolor=colors[idx % len(colors)],
            line_width=0,
            annotation_text=row["State"],
            annotation_position="right",
        )
    fig.update_layout(title="Data Aktual dan Interval Fuzzy")
    return fig


def plot_forecast(forecast, next_forecast):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=forecast["Tanggal"],
            y=forecast["Nilai"],
            mode="lines+markers",
            name="Aktual",
            line=dict(color="#2563eb", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["Tanggal"],
            y=forecast["Prediksi"],
            mode="lines+markers",
            name="Prediksi",
            line=dict(color="#dc2626", width=2, dash="dot"),
        )
    )
    next_date = forecast["Tanggal"].iloc[-1] + (forecast["Tanggal"].iloc[-1] - forecast["Tanggal"].iloc[-2])
    fig.add_trace(
        go.Scatter(
            x=[next_date],
            y=[next_forecast],
            mode="markers+text",
            name="Prediksi Berikutnya",
            marker=dict(color="#f97316", size=10),
            text=[f"{next_forecast:.2f}"],
            textposition="top center",
        )
    )
    fig.update_layout(
        height=390,
        margin=dict(l=10, r=10, t=35, b=10),
        title="Aktual vs Prediksi",
        xaxis_title="Tanggal",
        yaxis_title="Nilai",
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def method_notes(method):
    if method == "Fuzzy Time Series":
        return [
            "Setiap data diubah menjadi state fuzzy berdasarkan interval.",
            "Relasi dibaca sebagai state hari ini menuju state periode berikutnya.",
            "Prediksi diperoleh dari rata-rata titik tengah state tujuan pada relasi yang sama.",
        ]
    return [
        "Setiap data diubah menjadi state fuzzy berdasarkan interval.",
        "Transisi antar-state dihitung sebagai frekuensi dan probabilitas.",
        "Prediksi diperoleh dari rata-rata berbobot titik tengah state tujuan.",
    ]


def formula_table(method):
    if method == "Fuzzy Time Series":
        return pd.DataFrame(
            [
                {
                    "Bagian": "Interval",
                    "Formula": r"U_i=[b_i,b_{i+1}]",
                    "Makna": "Semesta data dibagi menjadi beberapa rentang. Setiap rentang menjadi state fuzzy.",
                },
                {
                    "Bagian": "Titik tengah",
                    "Formula": r"m_i=\frac{b_i+b_{i+1}}{2}",
                    "Makna": "Titik tengah interval dipakai sebagai wakil numerik state.",
                },
                {
                    "Bagian": "Relasi",
                    "Formula": r"A_t \rightarrow A_{t+1}",
                    "Makna": "State pada periode sekarang dihubungkan ke state periode berikutnya.",
                },
                {
                    "Bagian": "Prediksi Chen",
                    "Formula": r"\hat{x}_{t+1}=\frac{m_{j_1}+m_{j_2}+\cdots+m_{j_k}}{k}",
                    "Makna": "Prediksi adalah rata-rata titik tengah semua state tujuan dari relasi yang sama.",
                },
            ]
        )
    return pd.DataFrame(
        [
            {
                "Bagian": "Interval",
                "Formula": r"U_i=[b_i,b_{i+1}]",
                "Makna": "Semesta data dibagi menjadi beberapa state fuzzy.",
            },
            {
                "Bagian": "Transisi",
                "Formula": r"P_{ij}=\frac{n_{ij}}{\sum_j n_{ij}}",
                "Makna": "Probabilitas pindah dari state i ke state j dihitung dari frekuensi transisi.",
            },
            {
                "Bagian": "Prediksi Markov",
                "Formula": r"\hat{x}_{t+1}=\sum_j P_{ij}m_j",
                "Makna": "Prediksi adalah jumlah titik tengah state tujuan yang dibobot oleh probabilitas transisi.",
            },
        ]
    )


def show_formula_block(method):
    st.markdown("### Formula Utama")
    rows = formula_table(method)
    for _, row in rows.iterrows():
        st.markdown(f"**{row['Bagian']}**")
        st.latex(row["Formula"])
        st.caption(row["Makna"])


def interval_process_table(data, intervals):
    min_value = data["Nilai"].min()
    max_value = data["Nilai"].max()
    lower = intervals["Batas Bawah"].iloc[0]
    upper = intervals["Batas Atas"].iloc[-1]
    width = intervals["Batas Atas"].iloc[0] - intervals["Batas Bawah"].iloc[0]
    return pd.DataFrame(
        [
            {"Langkah": "Nilai minimum data", "Hasil": f"{min_value:.2f}"},
            {"Langkah": "Nilai maksimum data", "Hasil": f"{max_value:.2f}"},
            {"Langkah": "Batas bawah semesta", "Hasil": f"{lower:.2f}"},
            {"Langkah": "Batas atas semesta", "Hasil": f"{upper:.2f}"},
            {"Langkah": "Jumlah interval", "Hasil": f"{len(intervals)}"},
            {"Langkah": "Lebar interval", "Hasil": f"{width:.2f}"},
        ]
    )


def selected_forecast_detail(forecast_df, flr, intervals, row_number):
    if row_number <= 1:
        return pd.DataFrame(
            [{"Langkah": "Prediksi awal", "Hasil": "Periode pertama tidak memiliki periode sebelumnya."}]
        )
    previous = forecast_df.iloc[row_number - 2]
    current = forecast_df.iloc[row_number - 1]
    previous_state = previous["State"]
    historical_flr = flr.iloc[: row_number - 2]
    related = historical_flr[historical_flr["Dari"] == previous_state]
    destinations = related["Ke"].tolist()
    midpoints = [midpoint_for_state(intervals, state) for state in destinations]
    midpoint_text = " + ".join(f"{value:.2f}" for value in midpoints)
    formula = (
        f"({midpoint_text}) / {len(midpoints)} = {current['Prediksi']:.2f}"
        if midpoints
        else f"Tidak ada riwayat; memakai titik tengah {previous_state}."
    )
    return pd.DataFrame(
        [
            {"Langkah": "Periode yang diprediksi", "Hasil": str(current["Tanggal"].date())},
            {"Langkah": "State periode sebelumnya", "Hasil": previous_state},
            {"Langkah": "Relasi yang dicari", "Hasil": f"{previous_state} -> ?"},
            {"Langkah": "Riwayat tujuan state", "Hasil": ", ".join(destinations) if destinations else previous_state},
            {
                "Langkah": "Titik tengah tujuan",
                "Hasil": ", ".join(f"{state}={midpoint:.2f}" for state, midpoint in zip(destinations, midpoints))
                if destinations
                else f"{previous_state}={midpoint_for_state(intervals, previous_state):.2f}",
            },
            {"Langkah": "Rumus prediksi", "Hasil": formula},
            {"Langkah": "Prediksi", "Hasil": f"{current['Prediksi']:.2f}"},
            {"Langkah": "Aktual", "Hasil": f"{current['Nilai']:.2f}"},
            {"Langkah": "Error", "Hasil": f"{current['Error']:.2f}"},
        ]
    )


st.title("Fuzzy Forecasting Lab")
st.caption("Peramalan runtun waktu dengan interval fuzzy, relasi fuzzy, prediksi, dan evaluasi.")

with st.sidebar:
    st.header("Panel Forecasting")
    method_label = locked_choice(
        "Metode",
        ["F. Time Series", "F. Markov Chain"],
        0,
    )
    method = {
        "F. Time Series": "Fuzzy Time Series",
        "F. Markov Chain": "Fuzzy Markov Chain",
    }[method_label]
    n_intervals = st.slider("Jumlah interval fuzzy", 4, 12, 7, 1)


tabs = st.tabs(["Konsep", "Data", "Interval Fuzzy", "Relasi Fuzzy", "Proses", "Prediksi", "Evaluasi"])


with tabs[0]:
    st.subheader("Konsep Fuzzy Forecasting")
    st.markdown(
        """
        Fuzzy forecasting dipakai untuk membaca pola data runtun waktu dengan cara mengubah angka menjadi
        **state fuzzy**. Data terlebih dahulu dimasukkan ke beberapa interval seperti `A1`, `A2`, `A3`, dan seterusnya.

        Intinya:

        1. Data aktual dibagi ke beberapa interval.
        2. Setiap nilai aktual masuk ke satu state fuzzy.
        3. Perubahan state dari waktu ke waktu dibaca sebagai relasi.
        4. Relasi itu dipakai untuk memprediksi periode berikutnya.
        """
    )

    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown("### Fuzzy Time Series")
        st.markdown(
            """
            Fuzzy Time Series melihat pola perpindahan state. Jika state terakhir adalah `A5`,
            sistem mencari riwayat relasi yang pernah berawal dari `A5`. State tujuan dari relasi
            tersebut diubah kembali menjadi angka melalui titik tengah interval.
            """
        )
    with col_right:
        st.markdown("### Fuzzy Markov Chain")
        st.markdown(
            """
            Fuzzy Markov Chain juga melihat perpindahan state, tetapi memperhitungkan frekuensi.
            Jika `A5` lebih sering berpindah ke `A6` daripada ke `A4`, maka titik tengah `A6`
            mendapat bobot lebih besar dalam prediksi.
            """
        )

    show_formula_block(method)


with tabs[1]:
    st.subheader("Dataset Contoh: Penjualan UMKM")
    default_df = sample_sales_data()
    edited_df = st.data_editor(
        default_df,
        width="content",
        hide_index=True,
        height=table_height(default_df),
        num_rows="dynamic",
        column_config={
            "Tanggal": st.column_config.DateColumn("Tanggal", width=130),
            "Penjualan": st.column_config.NumberColumn("Penjualan", width=120, min_value=0),
        },
        key="sales_data_editor",
    )

    uploaded_file = st.file_uploader("Opsional: unggah CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            raw_upload = pd.read_csv(uploaded_file)
            date_col = st.selectbox("Kolom tanggal", raw_upload.columns)
            value_col = st.selectbox("Kolom nilai", raw_upload.columns)
            data = clean_timeseries(raw_upload, date_col, value_col)
            st.success("CSV berhasil dipakai.")
        except Exception as exc:
            st.error(f"CSV belum dapat dibaca: {exc}")
            data = clean_timeseries(edited_df, "Tanggal", "Penjualan")
    else:
        data = clean_timeseries(edited_df, "Tanggal", "Penjualan")

    st.markdown("### Data yang Dipakai")
    show_table(data, {"Nilai": "{:.2f}"})
    st.plotly_chart(plot_actual(data), use_container_width=True, config=PLOTLY_CONFIG, key="actual_plot")


data = locals().get(
    "data",
    clean_timeseries(locals().get("edited_df", sample_sales_data()), "Tanggal", "Penjualan"),
)
intervals = make_intervals(data["Nilai"], n_intervals)
forecast_result = forecast_series(data, intervals, method)
forecast_df = forecast_result["forecast"]
metrics = evaluate_forecast(forecast_df)


with tabs[2]:
    st.subheader("Interval Fuzzy")
    st.info("Interval membagi rentang data menjadi beberapa state fuzzy. Setiap nilai aktual masuk ke salah satu state.")
    show_table(
        intervals,
        {"Batas Bawah": "{:.2f}", "Batas Atas": "{:.2f}", "Titik Tengah": "{:.2f}"},
    )
    st.markdown("### Cara Interval Dibentuk")
    show_table(interval_process_table(data, intervals))
    st.plotly_chart(
        plot_intervals(data, intervals),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="interval_plot",
    )

    st.markdown("### Hasil Fuzzifikasi")
    show_table(
        forecast_result["fuzzy"],
        {"Nilai": "{:.2f}", "Titik Tengah State": "{:.2f}"},
    )


with tabs[3]:
    st.subheader("Relasi Fuzzy")
    st.info("Relasi dibaca dari state periode sekarang menuju state periode berikutnya.")
    show_table(forecast_result["flr"])

    st.markdown("### Kelompok Relasi")
    show_table(forecast_result["flrg"])

    if method == "Fuzzy Markov Chain":
        st.markdown("### Transisi untuk Prediksi Berikutnya")
        if forecast_result["next_detail"].empty:
            st.warning("State terakhir belum memiliki riwayat transisi.")
        else:
            show_table(
                forecast_result["next_detail"],
                {
                    "Probabilitas": "{:.4f}",
                    "Titik Tengah": "{:.2f}",
                    "Kontribusi": "{:.2f}",
                },
            )


with tabs[4]:
    st.subheader("Proses Prediksi")
    st.info("Bagian ini memperlihatkan dari mana satu nilai prediksi diperoleh.")

    selected_row = st.slider(
        "Periode yang dibedah proses prediksinya",
        min_value=2,
        max_value=len(forecast_df),
        value=len(forecast_df),
        step=1,
    )
    selected_period = forecast_df.iloc[selected_row - 1]
    st.caption(
        f"Baris ke-{selected_row}: prediksi untuk {selected_period['Tanggal'].date()} "
        f"dihitung dari state periode sebelumnya."
    )
    show_table(selected_forecast_detail(forecast_df, forecast_result["flr"], intervals, selected_row))

    st.markdown("### Prediksi Periode Berikutnya")
    st.markdown(f"State terakhir: **{forecast_result['last_state']}**")
    if method == "Fuzzy Time Series":
        st.markdown(
            "Bagian ini memakai state terakhir untuk menebak periode setelah data terakhir.  \n"
            "Caranya: cari semua riwayat relasi yang pernah berangkat dari state terakhir, "
            "ambil titik tengah state tujuannya, lalu hitung rata-ratanya."
        )
        show_table(
            forecast_result["next_detail"],
            {"Titik Tengah": "{:.2f}", "Kontribusi Rata-rata": "{:.2f}"},
        )
    else:
        st.markdown(
            "Bagian ini memakai state terakhir untuk menebak periode setelah data terakhir. "
            "Caranya: cari peluang perpindahan dari state terakhir ke setiap state tujuan, "
            "lalu kalikan peluang tersebut dengan titik tengah state tujuan."
        )
        if forecast_result["next_detail"].empty:
            st.warning("State terakhir belum memiliki riwayat transisi.")
        else:
            show_table(
                forecast_result["next_detail"],
                {
                    "Probabilitas": "{:.4f}",
                    "Titik Tengah": "{:.2f}",
                    "Kontribusi": "{:.2f}",
                },
            )
    st.success(f"Prediksi periode berikutnya: **{forecast_result['next_forecast']:.2f}**")


with tabs[5]:
    st.subheader("Prediksi")
    for idx, note in enumerate(method_notes(method), start=1):
        st.markdown(f"{idx}. {note}")

    st.success(
        f"State terakhir adalah **{forecast_result['last_state']}**. "
        f"Prediksi periode berikutnya: **{forecast_result['next_forecast']:.2f}**."
    )
    st.plotly_chart(
        plot_forecast(forecast_df, forecast_result["next_forecast"]),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="forecast_plot",
    )

    st.markdown("### Tabel Aktual dan Prediksi")
    show_table(
        forecast_df,
        {
            "Nilai": "{:.2f}",
            "Titik Tengah State": "{:.2f}",
            "Prediksi": "{:.2f}",
            "Error": "{:.2f}",
            "Abs Error": "{:.2f}",
            "APE": "{:.2f}",
        },
    )


with tabs[6]:
    st.subheader("Evaluasi")
    st.info("Evaluasi hanya dipakai sebagai alat baca. Hasil prediksi fuzzy dapat berubah ketika jumlah interval diubah.")
    eval_df = pd.DataFrame(
        [
            {"Metrik": "MAE", "Nilai": metrics["MAE"], "Makna": "rata-rata besar kesalahan absolut"},
            {"Metrik": "MAPE", "Nilai": metrics["MAPE"], "Makna": "rata-rata persentase kesalahan"},
            {"Metrik": "RMSE", "Nilai": metrics["RMSE"], "Makna": "kesalahan kuadrat rata-rata yang diakarkan"},
        ]
    )
    show_table(
        eval_df,
        {"Nilai": "{:.4f}"},
        {
            "Metrik": st.column_config.Column("Metrik", width=80),
            "Nilai": st.column_config.NumberColumn("Nilai", width=95),
            "Makna": st.column_config.Column("Makna", width=300),
        },
    )

    st.markdown("### Ringkasan")
    st.markdown(
        f"""
        - Metode: **{method}**
        - Jumlah interval: **{n_intervals}**
        - Prediksi berikutnya: **{forecast_result['next_forecast']:.2f}**
        - MAE: **{metrics['MAE']:.2f}**
        - MAPE: **{metrics['MAPE']:.2f}%**
        - RMSE: **{metrics['RMSE']:.2f}**
        """
    )
