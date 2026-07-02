import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from mcdm_core import (
    CRITERIA,
    DEFAULT_TYPES,
    DEFAULT_WEIGHTS,
    best_reason,
    calculate_method,
    compare_methods,
    decision_matrix,
    normalize_weights,
    sample_beasiswa_data,
    sensitivity_analysis,
)


st.set_page_config(
    page_title="Fuzzy Decision and Recommendation Lab",
    page_icon="F",
    layout="wide",
)


st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-size: 14px;
    }
    .block-container {
        padding-top: 1.05rem;
        padding-bottom: 1rem;
        max-width: 1380px;
    }
    h1 {
        font-size: 1.75rem !important;
        margin-bottom: 0.15rem !important;
    }
    h2 {
        font-size: 1.25rem !important;
        margin-top: 0.55rem !important;
        margin-bottom: 0.35rem !important;
    }
    h3 {
        font-size: 1.02rem !important;
        margin-top: 0.45rem !important;
        margin-bottom: 0.25rem !important;
    }
    p, li, label, .stMarkdown, .stCaption {
        font-size: 0.93rem !important;
        line-height: 1.38 !important;
    }
    div[data-testid="stSidebar"] {
        min-width: 250px;
        max-width: 250px;
    }
    div[data-testid="stSidebar"] h2,
    div[data-testid="stSidebar"] h3 {
        font-size: 0.98rem !important;
    }
    div[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 0.82rem !important;
        line-height: 1.24 !important;
    }
    div[data-baseweb="tab-list"] {
        gap: 0.15rem;
    }
    button[data-baseweb="tab"] {
        height: 2rem;
        padding: 0 0.55rem;
        font-size: 0.82rem;
    }
    div[data-testid="stDataFrame"] {
        font-size: 0.86rem;
    }
    .stAlert {
        padding-top: 0.45rem;
        padding-bottom: 0.45rem;
    }
    .stAlert p {
        font-size: 0.9rem !important;
        line-height: 1.32 !important;
    }
    .small-note {
        border-left: 4px solid #0f766e;
        background: #f8fafc;
        padding: 0.55rem 0.7rem;
        border-radius: 6px;
        color: #334155;
        margin: 0.25rem 0 0.55rem 0;
        font-size: 0.9rem;
        line-height: 1.32;
    }
    .compact-note {
        color: #475569;
        font-size: 0.88rem;
        line-height: 1.25;
        margin: 0.15rem 0 0.45rem 0;
    }
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
        "zoom",
        "pan",
        "select",
        "lasso",
        "zoomIn",
        "zoomOut",
        "autoScale",
        "resetScale",
        "zoom2d",
        "pan2d",
        "select2d",
        "lasso2d",
        "zoomIn2d",
        "zoomOut2d",
        "autoScale2d",
        "resetScale2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
        "toggleSpikelines",
    ],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "fuzzy_decision_chart",
        "height": 720,
        "width": 1280,
        "scale": 2,
    },
}


def format_money(value):
    return f"Rp{value:,.0f}".replace(",", ".")


def show_table(df, formatter=None):
    if formatter:
        st.dataframe(df.style.format(formatter), use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def build_bar_chart(ranking, score_column="Skor"):
    fig = px.bar(
        ranking.sort_values(score_column),
        x=score_column,
        y="Alternatif",
        orientation="h",
        color=score_column,
        color_continuous_scale=["#94a3b8", "#14b8a6", "#f59e0b"],
        text=score_column,
        height=330,
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.update_layout(
        xaxis_title="Skor akhir",
        yaxis_title="Alternatif",
        coloraxis_showscale=False,
        dragmode=False,
        margin=dict(l=10, r=30, t=40, b=10),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def build_comparison_chart(comparison):
    score_cols = ["Skor SAW", "Skor TOPSIS", "Skor WP"]
    melted = comparison.melt(
        id_vars="Alternatif",
        value_vars=score_cols,
        var_name="Metode",
        value_name="Skor",
    )
    melted["Metode"] = melted["Metode"].str.replace("Skor ", "", regex=False)
    fig = px.bar(
        melted,
        x="Alternatif",
        y="Skor",
        color="Metode",
        barmode="group",
        color_discrete_sequence=["#0f766e", "#2563eb", "#d97706"],
        height=330,
    )
    fig.update_layout(
        yaxis_title="Skor",
        xaxis_title="",
        dragmode=False,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def build_weight_chart(weights):
    weight_series = normalize_weights(weights)
    fig = px.bar(
        weight_series.reset_index().rename(columns={"index": "Kriteria", 0: "Bobot"}),
        x="Kriteria",
        y="Bobot",
        color="Kriteria",
        color_discrete_sequence=["#0f766e", "#2563eb", "#d97706", "#7c3aed", "#be123c"],
        height=255,
    )
    fig.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Bobot normalisasi",
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def build_sensitivity_chart(sensitivity_df):
    fig = px.line(
        sensitivity_df,
        x="Bobot Fokus",
        y="Peringkat",
        color="Alternatif",
        markers=True,
        height=335,
    )
    fig.update_yaxes(autorange="reversed", dtick=1)
    fig.update_layout(
        xaxis_title="Bobot kriteria yang diuji",
        yaxis_title="Peringkat",
        dragmode=False,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def build_score_explanation(method, weighted_table, ranking, criteria, criterion_types):
    if method == "SAW":
        detail = weighted_table.merge(
            ranking[["Alternatif", "Skor"]], on="Alternatif", how="left"
        )
        return (
            "Pada SAW, skor akhir adalah jumlah semua nilai terbobot.",
            detail[["Alternatif", *criteria, "Skor"]],
            r"V_i = \sum w_j r_{ij}",
        )

    if method == "TOPSIS":
        weighted_values = weighted_table[criteria].astype(float)
        ideal_best = {}
        ideal_worst = {}
        for criterion in criteria:
            if criterion_types[criterion] == "cost":
                ideal_best[criterion] = weighted_values[criterion].min()
                ideal_worst[criterion] = weighted_values[criterion].max()
            else:
                ideal_best[criterion] = weighted_values[criterion].max()
                ideal_worst[criterion] = weighted_values[criterion].min()

        ideal_table = pd.DataFrame(
            [
                {"Acuan": "Ideal Positif", **ideal_best},
                {"Acuan": "Ideal Negatif", **ideal_worst},
            ]
        )
        detail = ranking[
            [
                "Alternatif",
                "Jarak Ideal Positif",
                "Jarak Ideal Negatif",
                "Skor",
            ]
        ].copy()
        return (
            "Pada TOPSIS, skor akhir dihitung dari kedekatan terhadap ideal positif dan jarak dari ideal negatif.",
            detail,
            r"C_i = \frac{D_i^-}{D_i^+ + D_i^-}",
            ideal_table,
        )

    detail = weighted_table.merge(
        ranking[["Alternatif", "Vektor S", "Skor"]], on="Alternatif", how="left"
    )
    return (
        "Pada WP, setiap nilai dipangkatkan oleh bobot, lalu dikalikan menjadi Vektor S. Skor akhir adalah proporsi Vektor S terhadap total semua Vektor S.",
        detail[["Alternatif", *criteria, "Vektor S", "Skor"]],
        r"V_i = \frac{S_i}{\sum S_i},\quad S_i=\prod x_{ij}^{w_j}",
    )


def formula_notes(method):
    notes = {
        "SAW": {
            "meaning": (
                "SAW menghitung skor dengan menjumlahkan kontribusi setiap kriteria. "
                "Kontribusi satu kriteria diperoleh dari nilai normalisasi dikalikan bobot normalisasi."
            ),
            "flow": [
                "Ambil nilai asli dari tabel Data.",
                r"Ubah nilai asli menjadi nilai normalisasi. Benefit memakai $(x-\min)/(\max-\min)$, cost memakai $(\max-x)/(\max-\min)$.",
                "Kalikan nilai normalisasi dengan bobot normalisasi.",
                "Jumlahkan semua hasil perkalian untuk memperoleh skor akhir.",
            ],
            "symbols": [
                (r"V_i", "skor akhir alternatif ke-i", "diperoleh dari jumlah seluruh kontribusi kriteria"),
                (r"w_j", "bobot normalisasi kriteria ke-j", "berasal dari tabel Bobot, kolom Bobot Normalisasi"),
                (r"r_{ij}", "nilai normalisasi alternatif ke-i pada kriteria ke-j", "berasal dari Tabel Normalisasi"),
                (r"\sum", "penjumlahan", "menjumlahkan semua kriteria dari j = 1 sampai n"),
            ],
            "reading": r"Semakin besar $V_i$, semakin tinggi posisi alternatif pada ranking SAW.",
        },
        "TOPSIS": {
            "meaning": (
                "TOPSIS menghitung skor dari posisi alternatif terhadap dua titik acuan: "
                "ideal positif dan ideal negatif. Skor menjadi besar jika alternatif dekat "
                "ke ideal positif dan jauh dari ideal negatif."
            ),
            "flow": [
                r"Normalisasi data dengan membagi setiap nilai oleh akar jumlah kuadrat pada kriterianya: $x/\sqrt{\sum x^2}$.",
                "Kalikan hasil normalisasi dengan bobot normalisasi.",
                (
                    "Tentukan ideal positif dan ideal negatif dari tabel nilai terbobot. "
                    "Untuk kriteria benefit, ideal positif memakai nilai terbesar dan ideal negatif memakai nilai terkecil. "
                    "Untuk kriteria cost, ideal positif memakai nilai terkecil dan ideal negatif memakai nilai terbesar."
                ),
                r"Hitung jarak Euclidean setiap alternatif ke dua ideal tersebut.",
                "Ubah dua jarak itu menjadi skor kedekatan.",
            ],
            "symbols": [
                (r"C_i", "skor kedekatan alternatif ke-i", "dihitung dari perbandingan dua jarak"),
                (r"D_i^+", "jarak alternatif ke-i dari ideal positif", "dihitung dari tabel nilai terbobot terhadap baris Ideal Positif"),
                (r"D_i^-", "jarak alternatif ke-i dari ideal negatif", "dihitung dari tabel nilai terbobot terhadap baris Ideal Negatif"),
                (r"A^+", "ideal positif", "nilai terbaik tiap kriteria pada tabel nilai terbobot"),
                (r"A^-", "ideal negatif", "nilai terburuk tiap kriteria pada tabel nilai terbobot"),
            ],
            "reading": (
                r"Jika $D_i^+$ kecil dan $D_i^-$ besar, maka $C_i$ mendekati 1. "
                "Artinya alternatif itu dekat dengan kondisi terbaik dan jauh dari kondisi terburuk."
            ),
        },
        "WP": {
            "meaning": (
                "WP menghitung skor dengan perkalian. Setiap nilai kriteria diberi pangkat bobot, "
                "lalu semua hasilnya dikalikan menjadi Vektor S."
            ),
            "flow": [
                "Ambil nilai asli dari tabel Data.",
                "Ubah bobot input menjadi bobot normalisasi.",
                "Untuk kriteria benefit, gunakan pangkat positif; untuk cost, gunakan pangkat negatif.",
                r"Kalikan semua nilai berpangkat untuk memperoleh $S_i$.",
                r"Bagi $S_i$ tiap alternatif dengan total $S$ semua alternatif untuk memperoleh $V_i$.",
            ],
            "symbols": [
                (r"S_i", "Vektor S alternatif ke-i", "diperoleh dari perkalian semua nilai kriteria yang sudah dipangkatkan"),
                (r"V_i", "skor akhir alternatif ke-i", "diperoleh dari S_i dibagi total semua S"),
                (r"x_{ij}", "nilai alternatif ke-i pada kriteria ke-j", "berasal dari tabel Data"),
                (r"w_j", "bobot normalisasi kriteria ke-j", "berasal dari tabel Bobot, kolom Bobot Normalisasi"),
                (r"\prod", "perkalian berulang", "mengalikan semua kriteria dari j = 1 sampai n"),
            ],
            "reading": (
                r"Semakin besar $V_i$, semakin besar porsi $S_i$ alternatif tersebut dibandingkan total $S$ semua alternatif."
            ),
        },
    }
    return notes[method]


def show_formula_notes(method):
    note = formula_notes(method)
    st.markdown(note["meaning"])
    st.markdown("**Alur nilai yang dihitung:**")
    for index, item in enumerate(note["flow"], start=1):
        st.markdown(f"{index}. {item}")
    st.markdown("**Arti simbol dan asal nilainya:**")
    for symbol, meaning, source in note["symbols"]:
        col_symbol, col_text = st.columns([0.18, 0.82])
        with col_symbol:
            st.latex(symbol)
        with col_text:
            st.markdown(f"**{meaning}**  \n{source}")
    st.markdown(note["reading"])


def method_summary(method):
    summaries = {
        "SAW": {
            "name": "Simple Additive Weighting",
            "plain": "Setiap nilai dibuat sebanding, dikalikan bobot, lalu dijumlahkan.",
            "formula": r"V_i=\sum_{j=1}^{n} w_j r_{ij}",
        },
        "TOPSIS": {
            "name": "Technique for Order Preference by Similarity to Ideal Solution",
            "plain": "Skor makin besar jika alternatif makin dekat ke ideal positif dan makin jauh dari ideal negatif.",
            "formula": r"C_i=\frac{D_i^-}{D_i^+ + D_i^-}",
        },
        "WP": {
            "name": "Weighted Product",
            "plain": "Nilai kriteria dikalikan setelah diberi pangkat bobot.",
            "formula": r"V_i=\frac{\prod x_{ij}^{w_j}}{\sum_i \prod x_{ij}^{w_j}}",
        },
    }
    return summaries[method]


def beginner_glossary():
    return pd.DataFrame(
        [
            {
                "Istilah": "Alternatif",
                "Arti sederhana": "Pilihan yang akan diranking, misalnya Mahasiswa A, B, C.",
            },
            {
                "Istilah": "Kriteria",
                "Arti sederhana": "Aspek penilaian, misalnya IPK atau penghasilan orang tua.",
            },
            {
                "Istilah": "Benefit",
                "Arti sederhana": "Semakin besar nilainya, semakin baik.",
            },
            {
                "Istilah": "Cost",
                "Arti sederhana": "Semakin kecil nilainya, semakin baik.",
            },
            {
                "Istilah": "Bobot",
                "Arti sederhana": "Ukuran pentingnya sebuah kriteria.",
            },
            {
                "Istilah": "Normalisasi",
                "Arti sederhana": "Mengubah nilai berbeda satuan menjadi skala yang sebanding.",
            },
            {
                "Istilah": "Skor akhir",
                "Arti sederhana": "Nilai ringkasan yang dipakai untuk menyusun ranking.",
            },
        ]
    )


def explain_criterion_types(criterion_types):
    rows = []
    for criterion, ctype in criterion_types.items():
        if ctype == "benefit":
            meaning = "Nilai lebih besar dianggap lebih baik."
            example = "IPK 3.8 lebih baik daripada IPK 3.2."
        else:
            meaning = "Nilai lebih kecil dianggap lebih baik."
            example = "Penghasilan orang tua Rp1.400.000 lebih diprioritaskan daripada Rp3.800.000."
        rows.append({"Kriteria": criterion, "Tipe": ctype, "Cara membaca": meaning, "Contoh": example})
    return pd.DataFrame(rows)


st.title("Fuzzy Decision and Recommendation Lab")
st.caption(
    "Laboratorium Streamlit untuk memahami ranking, rekomendasi, bobot kriteria, dan sensitivitas keputusan."
)

with st.sidebar:
    st.header("Panel Keputusan")
    if hasattr(st, "segmented_control"):
        method = st.segmented_control(
            "Metode utama",
            ["SAW", "TOPSIS", "WP"],
            default="SAW",
        )
    else:
        method = st.radio(
            "Metode utama",
            ["SAW", "TOPSIS", "WP"],
            horizontal=True,
        )

    st.divider()
    st.subheader("Sensitivitas")
    focus_criterion = st.selectbox("Kriteria yang diuji", CRITERIA, index=1)


(
    tab_guide,
    tab_data,
    tab_weights,
    tab_process,
    tab_ranking,
    tab_compare,
    tab_sensitivity,
) = st.tabs(
    [
        "Panduan",
        "Data",
        "Bobot",
        "Perhitungan",
        "Ranking",
        "Perbandingan",
        "Sensitivitas Bobot",
    ]
)


with tab_guide:
    st.subheader("Alur Keputusan")
    st.markdown(
        """
        Aplikasi ini menjawab pertanyaan: **siapa yang paling layak direkomendasikan?**
        Prosesnya dibaca dari data, kriteria, bobot, perhitungan, lalu ranking.
        """
    )

    flow = pd.DataFrame(
        [
            {"Tahap": 1, "Nama": "Data", "Pertanyaan Panduan": "Siapa alternatifnya dan apa kriterianya?"},
            {"Tahap": 2, "Nama": "Benefit/Cost", "Pertanyaan Panduan": "Untuk tiap kriteria, angka besar itu baik atau buruk?"},
            {"Tahap": 3, "Nama": "Bobot", "Pertanyaan Panduan": "Kriteria mana yang paling penting?"},
            {"Tahap": 4, "Nama": "Normalisasi", "Pertanyaan Panduan": "Bagaimana menyamakan skala IPK, rupiah, dan skor?"},
            {"Tahap": 5, "Nama": "Skor metode", "Pertanyaan Panduan": "Bagaimana SAW/TOPSIS/WP mengolah nilai?"},
            {"Tahap": 6, "Nama": "Ranking", "Pertanyaan Panduan": "Siapa terbaik, dan mengapa?"},
        ]
    )
    show_table(flow)

    active_method = method_summary(method)
    col_method, col_terms = st.columns([1, 1])

    with col_method:
        st.markdown(f"### Metode yang Dipakai: {method}")
        st.markdown(f"**Nama lengkap:** {active_method['name']}")
        st.info(active_method["plain"])
        st.latex(active_method["formula"])
        with st.expander("Arti rumus", expanded=False):
            show_formula_notes(method)

    with col_terms:
        st.markdown("### Istilah Kunci")
        show_table(beginner_glossary())

    with st.expander("Urutan eksplorasi", expanded=False):
        st.markdown(
            """
            1. Buka **Data** dan periksa alternatif.
            2. Buka **Bobot**, jelaskan `benefit`, `cost`, dan bobot.
            3. Buka **Perhitungan**, tunjukkan normalisasi sebelum skor.
            4. Buka **Ranking** untuk melihat rekomendasi.
            5. Buka **Sensitivitas** untuk melihat dampak perubahan bobot.
            """
        )


with tab_data:
    st.subheader("Dataset Contoh: Prioritas Penerima Beasiswa")
    st.info(
        "Tahap 1. Data adalah bahan mentah keputusan. Baris adalah alternatif, kolom adalah kriteria penilaian."
    )
    st.markdown(
        """
        <div class="small-note">
        Data ini sengaja dibuat kecil agar proses normalisasi, pembobotan, dan ranking mudah ditelusuri.
        Kolom dapat diedit langsung tanpa upload file.
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_df = sample_beasiswa_data()
    edited_df = st.data_editor(
        default_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Alternatif": st.column_config.TextColumn("Alternatif", required=True),
            "IPK": st.column_config.NumberColumn("IPK", min_value=0.0, max_value=4.0, step=0.01),
            "Penghasilan Orang Tua": st.column_config.NumberColumn(
                "Penghasilan Orang Tua", min_value=0, step=100_000, format="Rp %d"
            ),
            "Jumlah Tanggungan": st.column_config.NumberColumn(
                "Jumlah Tanggungan", min_value=0, step=1
            ),
            "Prestasi": st.column_config.NumberColumn("Prestasi", min_value=0, max_value=100),
            "Keaktifan Organisasi": st.column_config.NumberColumn(
                "Keaktifan Organisasi", min_value=0, max_value=100
            ),
        },
    )

    uploaded_file = st.file_uploader(
        "Opsional: unggah CSV dengan kolom yang sama",
        type=["csv"],
    )

    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file)
            missing = [col for col in ["Alternatif", *CRITERIA] if col not in uploaded_df.columns]
            if missing:
                st.error("File belum valid. Kolom yang belum ada: " + ", ".join(missing))
                working_df = edited_df
            else:
                st.success("CSV berhasil dibaca. Dataset upload dipakai untuk perhitungan.")
                working_df = uploaded_df[["Alternatif", *CRITERIA]]
        except Exception as exc:
            st.error(f"CSV belum dapat dibaca: {exc}")
            working_df = edited_df
    else:
        working_df = edited_df

    clean_df = decision_matrix(working_df, CRITERIA)

    st.markdown("### Data yang Dipakai Sistem")
    show_table(
        clean_df,
        {
            "IPK": "{:.2f}",
            "Penghasilan Orang Tua": format_money,
            "Jumlah Tanggungan": "{:.0f}",
            "Prestasi": "{:.0f}",
            "Keaktifan Organisasi": "{:.0f}",
        },
    )

    with st.expander("Cara membaca dataset", expanded=False):
        st.markdown(
            """
            - **Alternatif** adalah calon penerima beasiswa.
            - **IPK, prestasi, organisasi**: makin besar biasanya makin baik.
            - **Penghasilan orang tua**: makin kecil biasanya makin diprioritaskan.
            - **Jumlah tanggungan**: makin besar biasanya makin diprioritaskan.
            """
        )


with tab_weights:
    st.subheader("Bobot dan Arah Kriteria")
    st.info(
        "Isi bobot dengan skala apa pun. Sistem otomatis mengubahnya menjadi bobot normalisasi."
    )
    col_a, col_b = st.columns([1.1, 1])

    default_weight_table = pd.DataFrame(
        {
            "Kriteria": CRITERIA,
            "Bobot Input": [DEFAULT_WEIGHTS[c] for c in CRITERIA],
            "Tipe": [DEFAULT_TYPES[c] for c in CRITERIA],
        }
    )

    with col_a:
        edited_weight_table = st.data_editor(
            default_weight_table,
            use_container_width=True,
            hide_index=True,
            disabled=["Kriteria"],
            column_config={
                "Kriteria": st.column_config.TextColumn("Kriteria"),
                "Bobot Input": st.column_config.NumberColumn(
                    "Bobot Input",
                    help="Boleh memakai skala apa pun. Contoh: 0.3, 3, 30, atau 100.",
                    step=0.01,
                    format="%.4f",
                ),
                "Tipe": st.column_config.SelectboxColumn(
                    "Tipe",
                    options=["benefit", "cost"],
                    required=True,
                ),
            },
            key="weight_type_editor",
        )

        edited_weight_table["Bobot Input"] = pd.to_numeric(
            edited_weight_table["Bobot Input"], errors="coerce"
        ).fillna(0)
        raw_weights = dict(zip(edited_weight_table["Kriteria"], edited_weight_table["Bobot Input"]))
        criterion_types = dict(zip(edited_weight_table["Kriteria"], edited_weight_table["Tipe"]))
        weights = normalize_weights(raw_weights).to_dict()

        weight_table = edited_weight_table.copy()
        weight_table["Bobot Normalisasi"] = weight_table["Kriteria"].map(weights)
        weight_table = weight_table[
            ["Kriteria", "Bobot Input", "Bobot Normalisasi", "Tipe"]
        ]
        st.caption("Hasil normalisasi")
        show_table(
            weight_table,
            {
                "Bobot Input": "{:.4f}",
                "Bobot Normalisasi": "{:.3f}",
            },
        )

    with col_b:
        st.plotly_chart(
            build_weight_chart(weights),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

    st.info(
        "Benefit berarti nilai lebih besar dianggap lebih baik. Cost berarti nilai lebih kecil dianggap lebih baik, misalnya penghasilan orang tua pada kasus beasiswa."
    )

    with st.expander("Benefit/cost dan normalisasi bobot", expanded=False):
        show_table(explain_criterion_types(criterion_types))
        st.markdown(
            f"Total bobot input **{sum(raw_weights.values()):.2f}** dinormalisasi menjadi **1.00**. "
            "Yang penting adalah perbandingan antar-bobot."
        )


clean_df = decision_matrix(locals().get("working_df", sample_beasiswa_data()), CRITERIA)
normalization, weighted_table, ranking = calculate_method(
    method, clean_df, CRITERIA, weights, criterion_types
)
comparison = compare_methods(clean_df, CRITERIA, weights, criterion_types)
best = ranking.iloc[0] if not ranking.empty else None


with tab_process:
    st.subheader(f"Perhitungan Metode {method}")
    st.info(
        "Tahap 4 dan 5. Urutannya: data mentah -> normalisasi -> pembobotan -> skor akhir."
    )

    if method == "SAW":
        st.markdown(
            "SAW menormalisasi setiap kriteria ke skala 0 sampai 1, lalu menjumlahkan nilai yang sudah dikalikan bobot."
        )
    elif method == "TOPSIS":
        st.markdown(
            "TOPSIS mencari alternatif yang paling dekat dengan kondisi ideal positif dan paling jauh dari kondisi ideal negatif."
        )
    else:
        st.markdown(
            "WP memakai perkalian nilai kriteria berpangkat bobot. Kriteria cost diberi pangkat negatif."
        )

    col_norm, col_weight = st.columns(2)

    with col_norm:
        st.markdown("### Tabel Normalisasi")
        st.caption(
            "Nilai sudah berada pada skala yang lebih sebanding. Untuk benefit, makin besar makin baik. Untuk cost, arah nilainya dibalik."
        )
        show_table(normalization, {criterion: "{:.4f}" for criterion in CRITERIA})

    with col_weight:
        st.markdown("### Tabel Nilai Terbobot")
        st.caption(
            "Nilai normalisasi sudah dikalikan bobot. Kriteria berbobot besar akan lebih terasa pengaruhnya."
        )
        show_table(weighted_table, {criterion: "{:.4f}" for criterion in CRITERIA})

    st.markdown("### Skor Akhir")
    show_table(
        ranking,
        {
            "Skor": "{:.4f}",
            "Jarak Ideal Positif": "{:.4f}",
            "Jarak Ideal Negatif": "{:.4f}",
            "Vektor S": "{:.4f}",
        },
    )

    st.markdown("### Rincian Skor Akhir")
    score_explanation = build_score_explanation(
        method, weighted_table, ranking, CRITERIA, criterion_types
    )
    st.caption(score_explanation[0])
    st.latex(score_explanation[2])

    if method == "TOPSIS":
        st.markdown("Acuan ideal")
        show_table(
            score_explanation[3],
            {criterion: "{:.4f}" for criterion in CRITERIA},
        )
        st.markdown("Perhitungan kedekatan")
        show_table(
            score_explanation[1],
            {
                "Jarak Ideal Positif": "{:.4f}",
                "Jarak Ideal Negatif": "{:.4f}",
                "Skor": "{:.4f}",
            },
        )
    else:
        formatter = {criterion: "{:.4f}" for criterion in CRITERIA}
        formatter.update({"Vektor S": "{:.4f}", "Skor": "{:.4f}"})
        show_table(score_explanation[1], formatter)


with tab_ranking:
    st.subheader("Ranking dan Rekomendasi")
    st.info(
        "Tahap 6. Ranking adalah hasil perhitungan berdasarkan data, bobot, tipe kriteria, dan metode yang dipilih."
    )

    st.plotly_chart(
        build_bar_chart(ranking),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )
    st.success(best_reason(clean_df, ranking, CRITERIA, weights, criterion_types))

    with st.expander("Cara membaca ranking", expanded=False):
        st.markdown(
            """
            - Peringkat 1 memiliki skor terbesar menurut metode yang dipilih.
            - Skor dipakai untuk membandingkan alternatif, bukan nilai mutlak.
            - Jika dua skor berdekatan, keputusan perlu dibahas lebih hati-hati.
            """
        )

    st.warning(
        "Ranking bukan kebenaran mutlak. Jika bobot, tipe kriteria, atau data berubah, rekomendasi juga dapat berubah."
    )


with tab_compare:
    st.subheader("Perbandingan SAW, TOPSIS, dan WP")
    st.info(
        "Bagian ini membandingkan hasil tiga metode pada data dan bobot yang sama. Gunakan setelah hasil metode utama sudah dipahami."
    )

    show_table(
        comparison,
        {
            "Skor SAW": "{:.4f}",
            "Skor TOPSIS": "{:.4f}",
            "Skor WP": "{:.4f}",
        },
    )
    st.plotly_chart(
        build_comparison_chart(comparison),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


with tab_sensitivity:
    st.subheader("Sensitivitas Bobot")
    st.markdown(
        f"Grafik ini menunjukkan perubahan peringkat ketika bobot **{focus_criterion}** dinaikkan atau diturunkan."
    )
    st.info(
        "Bagian ini menunjukkan bahwa hasil ranking dapat berubah ketika bobot kriteria berubah."
    )

    sensitivity_df = sensitivity_analysis(
        clean_df,
        CRITERIA,
        weights,
        criterion_types,
        focus_criterion,
        method,
    )

    st.plotly_chart(
        build_sensitivity_chart(sensitivity_df),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )

    score_view = sensitivity_df.pivot_table(
        index="Bobot Fokus",
        columns="Alternatif",
        values="Skor",
        aggfunc="first",
    ).reset_index()
    show_table(score_view, {col: "{:.4f}" for col in score_view.columns if col != "Bobot Fokus"})

    st.info(
        "Bagian ini berguna untuk diskusi PKL: keputusan multikriteria sering sensitif terhadap bobot. Karena itu, alasan pemilihan bobot perlu dijelaskan dalam laporan."
    )
