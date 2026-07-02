import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from control_core import (
    CASES,
    evaluate_control,
    mf_curve,
    narrative,
    surface_grid,
)


st.set_page_config(
    page_title="Fuzzy Control and Simulation Lab",
    page_icon="C",
    layout="wide",
)


st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-size: 14px; }
    .block-container {
        padding-top: 1.05rem;
        padding-bottom: 1rem;
        max-width: 1380px;
    }
    h1 { font-size: 1.75rem !important; margin-bottom: 0.15rem !important; }
    h2 { font-size: 1.25rem !important; margin-top: 0.55rem !important; margin-bottom: 0.35rem !important; }
    h3 { font-size: 1.02rem !important; margin-top: 0.45rem !important; margin-bottom: 0.25rem !important; }
    p, li, label, .stMarkdown, .stCaption {
        font-size: 0.93rem !important;
        line-height: 1.38 !important;
    }
    div[data-testid="stSidebar"] { min-width: 260px; max-width: 260px; }
    div[data-baseweb="tab-list"] { gap: 0.15rem; }
    button[data-baseweb="tab"] { height: 2rem; padding: 0 0.55rem; font-size: 0.82rem; }
    .stAlert { padding-top: 0.45rem; padding-bottom: 0.45rem; }
    .control-panel {
        border: 1px solid rgba(148,163,184,0.35);
        border-radius: 8px;
        padding: 0.8rem;
        background: rgba(15,23,42,0.18);
    }
    .gauge-label {
        font-size: 0.88rem;
        color: #94a3b8;
        margin-bottom: 0.2rem;
    }
    .value-big {
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.1;
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
        "filename": "fuzzy_control_chart",
        "height": 720,
        "width": 1280,
        "scale": 2,
    },
}


SET_COLORS = ["#16a34a", "#2563eb", "#dc2626"]
MARKER_LINE = "#f97316"


def table_height(df, max_height=520):
    row_count = len(df.index) if hasattr(df, "index") else 0
    return min(max_height, 42 + max(1, row_count) * 39)


def table_column_config(df):
    config = {}
    for column in df.columns:
        if column == "No":
            config[column] = st.column_config.Column(column, width=56)
        elif column == "Aktif":
            config[column] = st.column_config.Column(column, width=72)
        elif column in ["Alpha", "Alpha Mentah", "z Sugeno", "Alpha x z", "Derajat"]:
            config[column] = st.column_config.NumberColumn(column, width=110)
        elif column in ["Konsekuen", "Himpunan", "Aksi"]:
            config[column] = st.column_config.Column(column, width=120)
        elif column == "Kondisi":
            config[column] = st.column_config.Column(column, width=520)
        elif column == "Aturan":
            config[column] = st.column_config.Column(column, width=380)
        else:
            config[column] = st.column_config.Column(column, width=160)
    return config


def show_table(df, formatter=None):
    if formatter:
        st.dataframe(
            df.style.format(formatter),
            width="content",
            hide_index=True,
            height=table_height(df),
            column_config=table_column_config(df),
        )
    else:
        st.dataframe(
            df,
            width="content",
            hide_index=True,
            height=table_height(df),
            column_config=table_column_config(df),
        )


def plot_membership(case, input_name, value, degrees):
    spec = case["inputs"][input_name]
    x_min, x_max = spec["range"]
    x = pd.Series([x_min + (x_max - x_min) * i / 300 for i in range(301)])
    fig = go.Figure()
    for idx, (set_name, mf) in enumerate(spec["sets"].items()):
        y = mf_curve(x, mf)
        degree = degrees.get(set_name, 0.0)
        if degree > 0:
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=[min(float(y_value), degree) for y_value in y],
                    mode="lines",
                    fill="tozeroy",
                    name=f"area {set_name}",
                    line=dict(color=SET_COLORS[idx % len(SET_COLORS)], width=0),
                    fillcolor=SET_COLORS[idx % len(SET_COLORS)],
                    opacity=0.16,
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=set_name,
                line=dict(color=SET_COLORS[idx % len(SET_COLORS)], width=2.5),
            )
        )
        if degree > 0:
            fig.add_trace(
                go.Scatter(
                    x=[value],
                    y=[degree],
                    mode="markers",
                    name=f"μ {set_name}",
                    marker=dict(
                        color=SET_COLORS[idx % len(SET_COLORS)],
                        size=7,
                        line=dict(color="white", width=1),
                    ),
                    showlegend=False,
                )
            )
    fig.add_vline(
        x=value,
        line_color=MARKER_LINE,
        line_width=2,
        line_dash="dot",
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=34, b=10),
        title=f"{input_name}: {value:g}{spec['unit']}",
        xaxis_title=input_name,
        yaxis_title="Derajat",
        dragmode=False,
        legend=dict(orientation="h", y=-0.28),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(range=[0, 1.05], fixedrange=True)
    return fig


def plot_output(case, result):
    output = case["output"]
    fig = go.Figure()
    for idx, (set_name, mf) in enumerate(output["sets"].items()):
        fig.add_trace(
            go.Scatter(
                x=result["x_output"],
                y=mf_curve(result["x_output"], mf),
                mode="lines",
                name=set_name,
                opacity=0.45,
                line=dict(color=SET_COLORS[idx % len(SET_COLORS)], width=2.5),
            )
        )
    fig.add_trace(
        go.Scatter(
            x=result["x_output"],
            y=result["aggregated"],
            mode="lines",
            fill="tozeroy",
            name="agregasi",
            line=dict(color="#f59e0b", width=3),
        )
    )
    fig.add_vline(
        x=result["value"],
        line_color=MARKER_LINE,
        line_width=2,
        line_dash="dot",
    )
    fig.update_layout(
        height=310,
        margin=dict(l=10, r=10, t=34, b=10),
        title=f"Output {output['name']}: {result['value']:.2f} {output['unit']}",
        xaxis_title=output["name"],
        yaxis_title="Derajat",
        dragmode=False,
        legend=dict(orientation="h", y=-0.25),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(range=[0, 1.05], fixedrange=True)
    return fig


def plot_rule_strength(result):
    df = pd.DataFrame(result["rules"])
    fig = go.Figure(
        go.Bar(
            x=[f"R{int(no)}" for no in df["No"]],
            y=df["Alpha"],
            text=[f"{value:.2f}" for value in df["Alpha"]],
            textposition="outside",
            marker_color="#14b8a6",
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis_title="Alpha",
        xaxis_title="Aturan",
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(range=[0, 1.05], fixedrange=True)
    return fig


def plot_surface(case, method, x_name, y_name, inputs, active_rules):
    xs, ys, z = surface_grid(case, method, x_name, y_name, inputs, active_rules, n=27)
    fig = go.Figure(
        data=[
            go.Surface(
                x=xs,
                y=ys,
                z=z,
                colorscale="Viridis",
                colorbar=dict(title=case["output"]["unit"]),
            )
        ]
    )
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=35, b=10),
        title=f"Hubungan {x_name}, {y_name}, dan {case['output']['name']}",
        scene=dict(
            xaxis_title=x_name,
            yaxis_title=y_name,
            zaxis_title=case["output"]["name"],
        ),
    )
    return fig


def actuator_view(case, result):
    output = case["output"]
    percent = (result["value"] - output["range"][0]) / (output["range"][1] - output["range"][0])
    percent = max(0, min(1, percent))
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="gauge-label">{output["name"]}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="value-big">{result["value"]:.2f} {output["unit"]}</div>',
        unsafe_allow_html=True,
    )
    st.progress(percent)
    st.caption(f"Kategori: {result['label']}")

    if case["name"] == "Kipas Otomatis":
        blades = "▰" * max(1, int(percent * 12))
        st.markdown(f"Kecepatan visual: `{blades}`")
    else:
        drops = "▮" * max(1, int(percent * 12))
        st.markdown(f"Durasi visual: `{drops}`")
    st.markdown("</div>", unsafe_allow_html=True)


def formula_notes(method, case):
    if method == "Mamdani":
        return [
            "Setiap aturan menghasilkan daerah output yang dipotong oleh nilai alpha.",
            "Semua daerah output digabung dengan operator maksimum.",
            f"Nilai akhir {case['output']['name'].lower()} diperoleh dari titik pusat daerah agregasi.",
        ], r"z^*=\frac{\int z\,\mu(z)\,dz}{\int \mu(z)\,dz}"
    return [
        "Setiap aturan menghasilkan nilai tegas z.",
        "Nilai z dikalikan alpha aturan.",
        "Nilai akhir diperoleh dari rata-rata berbobot seluruh aturan aktif.",
    ], r"z^*=\frac{\sum \alpha_i z_i}{\sum \alpha_i}"


def locked_choice(label, options, default_index=0):
    if hasattr(st, "segmented_control") and len(options) <= 4:
        return st.segmented_control(
            label,
            options,
            default=options[default_index],
        )
    return st.radio(label, options, index=default_index, horizontal=True)


def default_rule_editor(case):
    rows = []
    for idx, rule in enumerate(case["rules"]):
        rows.append(
            {
                "No": idx + 1,
                "Aktif": True,
                "Kondisi": " AND ".join(
                    f"{name} = {set_name}" for name, set_name in rule["if"].items()
                ),
                "Aksi": rule["then"],
            }
        )
    return pd.DataFrame(rows)


def make_rule_label(condition, action):
    readable = condition.replace(" = ", " ").replace(" AND ", " dan ")
    return f"Jika {readable.lower()}, maka {action}."


def apply_rule_editor(case, edited_rules):
    edited_case = dict(case)
    edited_case["rules"] = []
    active_rules = {}

    for _, row in edited_rules.iterrows():
        idx = int(row["No"]) - 1
        base_rule = case["rules"][idx]
        action = str(row["Aksi"])
        active_rules[idx] = bool(row["Aktif"])
        edited_case["rules"].append(
            {
                **base_rule,
                "then": action,
                "label": make_rule_label(row["Kondisi"], action),
            }
        )

    return edited_case, active_rules


st.title("Fuzzy Control and Simulation Lab")
st.caption("Simulasi sistem kontrol fuzzy: input sensor, aturan aktif, output kontrol, dan respons sistem.")

with st.sidebar:
    st.header("Panel Simulasi")
    case_options = {
        "Kipas Auto": "Kipas Otomatis",
        "Siram Auto": "Penyiraman Tanaman Otomatis",
    }
    case_label = locked_choice("Mode kasus", list(case_options.keys()), 0)
    case_name = case_options[case_label]
    case = CASES[case_name]()

    method = locked_choice("Metode kontrol", ["Mamdani", "Sugeno"], 0)

    st.divider()
    st.subheader("Input Sensor")
    inputs = {}
    for input_name, spec in case["inputs"].items():
        low, high = spec["range"]
        inputs[input_name] = st.slider(
            f"{input_name} ({spec['unit']})",
            min_value=float(low),
            max_value=float(high),
            value=float(spec["default"]),
            step=float(spec["step"]),
        )

tabs = st.tabs(
    [
        "Simulasi",
        "Fungsi Keanggotaan",
        "Aturan",
        "Perhitungan",
        "Grafik Input-Output",
    ]
)


with tabs[2]:
    st.subheader("Basis Aturan")
    st.caption("Kolom Aktif dan Aksi dapat diedit. Kondisi dikunci agar struktur aturan tetap terbaca.")
    default_rules_df = default_rule_editor(case)
    rule_editor = st.data_editor(
        default_rules_df,
        width="content",
        hide_index=True,
        height=table_height(default_rules_df),
        disabled=["No", "Kondisi"],
        column_config={
            "No": st.column_config.NumberColumn("No", width=56),
            "Aktif": st.column_config.CheckboxColumn("Aktif", width=72),
            "Kondisi": st.column_config.TextColumn("Kondisi", width=520),
            "Aksi": st.column_config.SelectboxColumn(
                "Aksi",
                options=list(case["output"]["sets"].keys()),
                required=True,
                width=120,
            ),
        },
        key=f"rule_editor_{case_name}",
    )


case, active_rules = apply_rule_editor(case, rule_editor)
result = evaluate_control(case, inputs, method=method, active_rules=active_rules)


with tabs[0]:
    st.subheader(case["name"])
    st.info(case["description"])

    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        st.markdown("### Respons Sistem")
        st.success(narrative(case, result))
        actuator_view(case, result)

    with col_right:
        st.markdown("### Aturan Terkuat")
        dominant = result["dominant_rule"]
        st.markdown(f"**R{dominant['No']}**")
        st.markdown(dominant["Aturan"])
        st.markdown(f"Alpha: **{dominant['Alpha']:.3f}**")
        if method == "Sugeno":
            st.markdown(f"Output aturan: **{dominant['z Sugeno']:.2f} {case['output']['unit']}**")

    st.markdown("### Kekuatan Aturan")
    st.plotly_chart(
        plot_rule_strength(result),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="simulasi_rule_strength",
    )


with tabs[1]:
    st.subheader("Fungsi Keanggotaan Input")
    cols = st.columns(2)
    for idx, (input_name, value) in enumerate(inputs.items()):
        with cols[idx % 2]:
            st.plotly_chart(
                plot_membership(case, input_name, value, result["degrees"][input_name]),
                use_container_width=True,
                config=PLOTLY_CONFIG,
                key=f"membership_{case_name}_{input_name}",
            )

    st.markdown("### Derajat Keanggotaan")
    degree_rows = []
    for input_name, sets in result["degrees"].items():
        for set_name, degree in sets.items():
            degree_rows.append(
                {"Input": input_name, "Himpunan": set_name, "Derajat": degree}
            )
    show_table(pd.DataFrame(degree_rows), {"Derajat": "{:.4f}"})

    st.markdown("### Agregasi Output")
    if method == "Mamdani":
        st.caption("Area berwarna menunjukkan gabungan output aturan yang aktif.")
        st.plotly_chart(
            plot_output(case, result),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="membership_output_aggregation",
        )
    else:
        st.caption("Pada Sugeno, agregasi berupa rata-rata berbobot dari output tegas tiap aturan.")
        rules_df = pd.DataFrame(result["rules"])
        show_table(
            rules_df[["No", "Aturan", "Konsekuen", "Alpha", "z Sugeno", "Alpha x z"]],
            {"Alpha": "{:.4f}", "z Sugeno": "{:.4f}", "Alpha x z": "{:.4f}"},
        )


with tabs[2]:
    st.markdown("### Hasil Evaluasi Aturan")
    rules_df = pd.DataFrame(result["rules"])
    show_table(
        rules_df,
        {
            "Alpha Mentah": "{:.4f}",
            "Alpha": "{:.4f}",
            "z Sugeno": "{:.4f}",
            "Alpha x z": "{:.4f}",
        },
    )


with tabs[3]:
    st.subheader(f"Perhitungan {method}")
    steps, formula = formula_notes(method, case)
    for idx, step in enumerate(steps, start=1):
        st.markdown(f"{idx}. {step}")
    st.latex(formula)

    if method == "Mamdani":
        st.markdown("### Agregasi Output")
        st.plotly_chart(
            plot_output(case, result),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="calculation_output_aggregation",
        )
    else:
        st.markdown("### Rata-Rata Berbobot")
        st.markdown(f"Pembilang: **{result['weighted_sum']:.4f}**")
        st.markdown(f"Penyebut: **{result['alpha_sum']:.4f}**")

    st.markdown("### Tabel Kontribusi Aturan")
    rules_df = pd.DataFrame(result["rules"])
    show_table(
        rules_df[["No", "Aturan", "Konsekuen", "Alpha", "z Sugeno", "Alpha x z"]],
        {"Alpha": "{:.4f}", "z Sugeno": "{:.4f}", "Alpha x z": "{:.4f}"},
    )


with tabs[4]:
    st.subheader("Grafik Input-Output")
    input_names = list(case["inputs"].keys())
    col_a, col_b = st.columns(2)
    with col_a:
        x_name = locked_choice("Sumbu X", input_names, 0)
    with col_b:
        y_default = 1 if len(input_names) > 1 else 0
        y_name = locked_choice("Sumbu Y", input_names, y_default)

    if x_name == y_name:
        st.warning("Pilih dua input yang berbeda.")
    else:
        st.plotly_chart(
            plot_surface(case, method, x_name, y_name, inputs, active_rules),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key=f"surface_{case_name}_{method}_{x_name}_{y_name}",
        )

    st.caption("Input lain yang tidak menjadi sumbu memakai nilai slider saat ini.")
