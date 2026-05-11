import math
import base64
from io import BytesIO
from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import streamlit as st


# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="L-System Explorer",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Layar utama dipadatkan agar canvas langsung tampak di resolusi kecil. */
    .block-container {
        padding-top: 0.18rem !important;
        padding-bottom: 0.35rem !important;
        padding-left: 0.55rem !important;
        padding-right: 0.55rem !important;
        max-width: 100% !important;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(80, 190, 120, .08), transparent 22rem),
            linear-gradient(135deg, #08111f 0%, #0b1020 48%, #07140b 100%);
        color: #f8fafc;
    }

    [data-testid="stSidebar"] {
        background: rgba(7, 12, 24, .96);
        border-right: 1px solid rgba(255,255,255,.08);
        min-width: 280px !important;
        max-width: 305px !important;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: .55rem !important;
        padding-left: .65rem !important;
        padding-right: .65rem !important;
        padding-bottom: .55rem !important;
    }

    .side-title {
        font-size: 1.08rem;
        font-weight: 850;
        letter-spacing: -.03em;
        margin: 0 0 .15rem 0;
        color: #f8fafc;
    }

    .side-subtitle {
        font-size: .72rem;
        line-height: 1.25;
        color: #a7f3d0;
        margin-bottom: .35rem;
    }

    .mini-stat {
        font-size: .72rem;
        line-height: 1.32;
        color: #cbd5e1;
        padding: .42rem .48rem;
        border-radius: .55rem;
        background: rgba(15, 23, 42, .72);
        border: 1px solid rgba(255,255,255,.10);
        margin-top: .35rem;
    }

    .mini-help {
        font-size: .72rem;
        line-height: 1.30;
        color: #d9f99d;
        padding: .42rem .48rem;
        border-radius: .55rem;
        background: rgba(63, 98, 18, .20);
        border: 1px solid rgba(132, 204, 22, .22);
    }

    label, .stSelectbox label, .stSlider label, .stNumberInput label,
    .stTextInput label, .stTextArea label, .stRadio label, .stCheckbox label {
        font-size: .72rem !important;
        line-height: 1.1 !important;
    }

    [data-testid="stWidgetLabel"] {
        min-height: 1rem !important;
    }

    div[data-baseweb="select"] > div {
        min-height: 1.95rem !important;
        font-size: .78rem !important;
    }

    input, textarea {
        font-size: .76rem !important;
    }

    textarea {
        min-height: 4.5rem !important;
    }

    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        min-height: 1.70rem !important;
        height: 1.70rem !important;
        padding: .05rem .25rem !important;
        border-radius: .55rem !important;
        border: 1px solid rgba(255,255,255,.18) !important;
        background: rgba(15, 23, 42, .82) !important;
        color: #f8fafc !important;
        font-size: .76rem !important;
        font-weight: 760 !important;
        line-height: 1 !important;
    }

    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        border-color: rgba(132, 204, 22, .72) !important;
        color: #bef264 !important;
    }

    div[data-testid="stSlider"] {
        padding-top: 0rem !important;
        padding-bottom: .10rem !important;
    }

    div[data-testid="stMarkdownContainer"] p {
        margin-bottom: .20rem !important;
    }

    hr {
        margin: .35rem 0 .45rem 0 !important;
    }

    .stExpander {
        border: 1px solid rgba(255,255,255,.10) !important;
        border-radius: .55rem !important;
        background: rgba(15,23,42,.35) !important;
    }

    .canvas-frame {
        border: 1px solid rgba(255,255,255,.10);
        border-radius: .75rem;
        overflow: hidden;
        background: rgba(0,0,0,.15);
        box-shadow: 0 18px 45px rgba(0,0,0,.18);
        margin: 0 !important;
        padding: 0 !important;
    }

    div[data-testid="stPyplot"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    div[data-testid="stPyplot"] img {
        display: block !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .word-panel {
        margin-top: .55rem;
        padding: .65rem .75rem .75rem .75rem;
        border-radius: .75rem;
        background: rgba(15,23,42,.64);
        border: 1px solid rgba(255,255,255,.10);
    }

    .word-title {
        font-size: .95rem;
        font-weight: 800;
        margin-bottom: .15rem;
        color: #f8fafc;
    }

    .word-caption {
        font-size: .74rem;
        color: #a7f3d0;
        margin-bottom: .35rem;
    }
    
    .mini-section {
        font-size: 1.08rem;
        font-weight: 800;
        color: #f6f7e8;
        margin-top: 0.9rem;
        margin-bottom: 0.35rem;
        padding: 0.38rem 0.55rem;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.07);
        border-left: 4px solid #d6c65a;
    }

    .download-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.5rem;
        margin-top: 0.5rem;
        margin-bottom: 0.8rem;
    }

    .download-chip {
        display: block;
        text-align: center;
        padding: 0.45rem 0.55rem;
        border-radius: 0.55rem;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.14);
        color: #f4f7df !important;
        text-decoration: none !important;
        font-size: 0.85rem;
        font-weight: 650;
    }

    .download-chip:hover {
        background: rgba(214,198,90,0.22);
        border-color: rgba(214,198,90,0.45);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def sidebar_label(text):
    st.sidebar.markdown(
        f'<div class="mini-section">{text}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# DATA PRESET
# ============================================================
PRESETS = {
    "Tanaman 1": {
        "description": "Tanaman bercabang padat dengan bentuk seperti perdu kecil.",
        "axiom": "X",
        "rules": "X -> F[+X][-X]FX\nF -> FF",
        "angle": 25.7,
        "start_angle": 90.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 7,
        "max_iteration": 7,
        "step": 1.0,
        "theme": "Botanical",
    },

    "Tanaman 2": {
        "description": "Tanaman menjalar ke atas dengan percabangan halus dan agak miring.",
        "axiom": "X",
        "rules": "X -> F[+X][-X]F[+X]FX\nF -> FF",
        "angle": 18.5,
        "start_angle": 90.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 7,
        "max_iteration": 7,
        "step": 1.0,
        "theme": "Wikipedia Night",
    },

    "Tanaman 3": {
        "description": "Tanaman simetris elegan dengan percabangan bertingkat. Visualnya bersih untuk pembelajaran.",
        "axiom": "X",
        "rules": "X -> F[+X][-X]F[+X][-X]\nF -> FF",
        "angle": 26.0,
        "start_angle": 90.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 6,
        "max_iteration": 7,
        "step": 1.0,
        "theme": "Wikipedia Night",
    },

    "Tanaman 4": {
        "description": "Tanaman spiral bercabang. Cocok untuk menunjukkan bahwa perubahan sudut kecil dapat memberi karakter besar.",
        "axiom": "X",
        "rules": "X -> F[+X]F[+X]-X\nF -> FF",
        "angle": 24.0,
        "start_angle": 90.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 8,
        "max_iteration": 8,
        "step": 1.0,
        "theme": "Wikipedia Night",
    },

    "Tanaman 5": {
        "description": "Pohon dengan percabangan melebar seperti mahkota. Bagus untuk variasi pohon rindang.",
        "axiom": "X",
        "rules": "X -> F[+X][-X]F[+X][-X]X\nF -> FF",
        "angle": 21.0,
        "start_angle": 90.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 5,
        "max_iteration": 7,
        "step": 1.0,
        "theme": "Wikipedia Night",
    },

    "Pohon Biner": {
        "description": "Pohon biner sederhana dengan percabangan simetris.",
        "axiom": "F",
        "rules": "F -> F[+F]F[-F]F",
        "angle": 25.7,
        "start_angle": 90.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 4,
        "max_iteration": 6,
        "step": 1.0,
        "theme": "Botanical",
    },
    "Koch Snowflake": {
        "description": "Setiap sisi segitiga diganti pola bergerigi berulang.",
        "axiom": "F--F--F",
        "rules": "F -> F+F--F+F",
        "angle": 60.0,
        "start_angle": 0.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 4,
        "max_iteration": 6,
        "step": 1.0,
        "theme": "Ice Paper",
    },
    "Kurva Koch": {
        "description": "Versi satu garis dari konstruksi Koch.",
        "axiom": "F",
        "rules": "F -> F+F--F+F",
        "angle": 60.0,
        "start_angle": 0.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 4,
        "max_iteration": 7,
        "step": 1.0,
        "theme": "Wikipedia Night",
    },
    "Segitiga Sierpinski": {
        "description": "Segitiga Sierpinski. Simbol F dan G sama-sama digambar.",
        "axiom": "F-G-G",
        "rules": "F -> F-G+F+G-F\nG -> GG",
        "angle": 120.0,
        "start_angle": 0.0,
        "draw_symbols": "FG",
        "move_symbols": "f",
        "default_iteration": 5,
        "max_iteration": 7,
        "step": 1.0,
        "theme": "Neon Math",
    },
    "Kurva Naga": {
        "description": "X dan Y menjadi variabel produksi, sedangkan F yang digambar.",
        "axiom": "FX",
        "rules": "X -> X+YF+\nY -> -FX-Y",
        "angle": 90.0,
        "start_angle": 0.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 10,
        "max_iteration": 16,
        "step": 1.0,
        "theme": "Wikipedia Night",
    },
    "Kurva Hilbert": {
        "description": "Kurva pengisi ruang. A dan B tidak digambar, F yang digambar.",
        "axiom": "A",
        "rules": "A -> -BF+AFA+FB-\nB -> +AF-BFB-FA+",
        "angle": 90.0,
        "start_angle": 0.0,
        "draw_symbols": "F",
        "move_symbols": "f",
        "default_iteration": 5,
        "max_iteration": 7,
        "step": 1.0,
        "theme": "Ink on Paper",
    },
}

THEMES = {
    "Wikipedia Night": {
        "background": "#0b1020",
        "line_start": "#37d67a",
        "line_end": "#f4d35e",
        "ghost": "#94a3b8",
    },
    "Botanical": {
        "background": "#07140b",
        "line_start": "#8b5a2b",
        "line_end": "#7ddc6f",
        "ghost": "#9ca3af",
    },
    "Ice Paper": {
        "background": "#f8fafc",
        "line_start": "#0f766e",
        "line_end": "#38bdf8",
        "ghost": "#94a3b8",
    },
    "Neon Math": {
        "background": "#09090b",
        "line_start": "#22d3ee",
        "line_end": "#a3e635",
        "ghost": "#71717a",
    },
    "Ink on Paper": {
        "background": "#fff7ed",
        "line_start": "#111827",
        "line_end": "#4b5563",
        "ghost": "#9ca3af",
    },
}

CANVAS_RATIOS = {
    "16:9 compact": (11.6, 6.52),
    "18:9 sangat lebar": (12.0, 6.0),
    "4:3": (9.4, 7.05),
    "1:1": (7.2, 7.2),
}


# ============================================================
# FUNGSI INTI
# ============================================================
@dataclass(frozen=True)
class Segment:
    x1: float
    y1: float
    x2: float
    y2: float
    depth: int
    index: int


def parse_rules(rules_text: str) -> dict[str, str]:
    rules: dict[str, str] = {}
    for raw_line in rules_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "->" in line:
            left, right = line.split("->", 1)
        elif "=" in line:
            left, right = line.split("=", 1)
        elif ":" in line:
            left, right = line.split(":", 1)
        else:
            raise ValueError(f"Aturan tidak terbaca: {raw_line}")

        left = left.strip()
        right = right.strip()

        if len(left) != 1:
            raise ValueError(f"Sisi kiri aturan harus satu simbol: {left}")

        rules[left] = right
    return rules


@st.cache_data(show_spinner=False)
def produce_lsystem_cached(
    axiom: str,
    rules_text: str,
    iteration: int,
    max_chars: int = 250_000,
) -> tuple[str, bool]:
    rules = parse_rules(rules_text)
    word = axiom
    truncated = False

    for _ in range(iteration):
        parts: list[str] = []
        new_length = 0
        for ch in word:
            replacement = rules.get(ch, ch)
            parts.append(replacement)
            new_length += len(replacement)
            if new_length > max_chars:
                truncated = True
                break
        word = "".join(parts)
        if truncated:
            break

    return word, truncated


@st.cache_data(show_spinner=False)
def turtle_segments_cached(
    word: str,
    angle_deg: float,
    start_angle_deg: float,
    step: float,
    draw_symbols: str,
    move_symbols: str,
) -> list[Segment]:
    x, y = 0.0, 0.0
    heading = math.radians(start_angle_deg)
    turn = math.radians(angle_deg)
    stack: list[tuple[float, float, float, int]] = []
    depth = 0
    segments: list[Segment] = []
    idx = 0

    for ch in word:
        if ch in draw_symbols or ch in move_symbols:
            nx = x + step * math.cos(heading)
            ny = y + step * math.sin(heading)
            if ch in draw_symbols:
                segments.append(Segment(x, y, nx, ny, depth, idx))
                idx += 1
            x, y = nx, ny
        elif ch == "+":
            heading += turn
        elif ch == "-":
            heading -= turn
        elif ch == "|":
            heading += math.pi
        elif ch == "[":
            stack.append((x, y, heading, depth))
            depth += 1
        elif ch == "]" and stack:
            x, y, heading, depth = stack.pop()

    return segments


def hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.strip().lstrip("#")
    return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255


def blend(c1: str, c2: str, t: float) -> tuple[float, float, float]:
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = hex_to_rgb01(c1)
    r2, g2, b2 = hex_to_rgb01(c2)
    return r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t


def raw_bounds(segments: list[Segment]) -> tuple[float, float, float, float]:
    if not segments:
        return -1.0, 1.0, -1.0, 1.0

    xs = [s.x1 for s in segments] + [s.x2 for s in segments]
    ys = [s.y1 for s in segments] + [s.y2 for s in segments]
    return min(xs), max(xs), min(ys), max(ys)


def plot_bounds_for_canvas(
    bounds: tuple[float, float, float, float],
    canvas_ratio: str,
    margin_fraction: float = 0.060,
) -> tuple[float, float, float, float]:
    """Membuat setiap iterasi memenuhi canvas dengan padding kecil."""
    xmin, xmax, ymin, ymax = bounds
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    width = max(xmax - xmin, 1e-9)
    height = max(ymax - ymin, 1e-9)

    width *= 1 + 2 * margin_fraction
    height *= 1 + 2 * margin_fraction

    fig_w, fig_h = CANVAS_RATIOS[canvas_ratio]
    target_ratio = fig_w / fig_h
    current_ratio = width / height

    if current_ratio < target_ratio:
        width = height * target_ratio
    else:
        height = width / target_ratio

    return cx - width / 2, cx + width / 2, cy - height / 2, cy + height / 2


def colored_line_collection(
    segments: list[Segment],
    start_color: str,
    end_color: str,
    color_mode: str,
    line_width: float,
    alpha: float = 1.0,
) -> LineCollection | None:
    if not segments:
        return None

    line_data = [[(s.x1, s.y1), (s.x2, s.y2)] for s in segments]
    max_depth = max(s.depth for s in segments) or 1
    max_index = max(s.index for s in segments) or 1

    colors = []
    for s in segments:
        if color_mode == "Kedalaman":
            t = s.depth / max_depth
        elif color_mode == "Urutan":
            t = s.index / max_index
        else:
            t = 0.65
        r, g, b = blend(start_color, end_color, t)
        colors.append((r, g, b, alpha))

    return LineCollection(
        line_data,
        colors=colors,
        linewidths=line_width,
        capstyle="round",
        joinstyle="round",
    )

def download_link(label, data, file_name, mime):
    if isinstance(data, str):
        data = data.encode("utf-8")

    b64 = base64.b64encode(data).decode("utf-8")

    return (
        f'<a class="download-chip" '
        f'href="data:{mime};base64,{b64}" '
        f'download="{file_name}">{label}</a>'
    )

def render_lsystem(
    segments: list[Segment],
    previous_segments: list[Segment] | None,
    theme_name: str,
    line_width: float,
    color_mode: str,
    show_start_end: bool,
    show_previous_ghost: bool,
    ghost_alpha: float,
    canvas_ratio: str,
):
    theme = THEMES[theme_name]
    bg = theme["background"]
    start = theme["line_start"]
    end = theme["line_end"]
    ghost = theme["ghost"]
    figsize = CANVAS_RATIOS[canvas_ratio]

    fig, ax = plt.subplots(figsize=figsize, dpi=145, facecolor=bg)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_facecolor(bg)
    ax.axis("off")
    ax.set_aspect("equal", adjustable="box")

    # Fit-to-current iteration: batas gambar dihitung dari iterasi yang sedang aktif.
    xmin, xmax, ymin, ymax = plot_bounds_for_canvas(raw_bounds(segments), canvas_ratio)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    if show_previous_ghost and previous_segments:
        ghost_collection = colored_line_collection(
            previous_segments,
            ghost,
            ghost,
            "Satu warna",
            max(0.35, line_width * 0.82),
            alpha=ghost_alpha,
        )
        if ghost_collection is not None:
            ax.add_collection(ghost_collection)

    if not segments:
        ax.text(
            0.5,
            0.5,
            "Belum ada segmen yang digambar.\nKlik Next atau periksa draw symbols.",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=10,
            color=end,
        )
        return fig

    main_collection = colored_line_collection(
        segments,
        start,
        end,
        color_mode,
        line_width,
        alpha=1.0,
    )
    if main_collection is not None:
        ax.add_collection(main_collection)

    if show_start_end:
        ax.scatter([segments[0].x1], [segments[0].y1], s=18, color=start, zorder=3)
        ax.scatter([segments[-1].x2], [segments[-1].y2], s=18, color=end, zorder=3)

    return fig


def compact_preview(text: str, limit: int = 1400) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n\n... dipotong untuk preview sidebar ...\n\n" + text[-half:]


# ============================================================
# SIDEBAR COMPACT
# ============================================================
st.sidebar.markdown(
    """
    <div class="side-title">L-System Explorer</div>
    <div class="side-subtitle">
        Bangun fraktal dari axiom dan aturan produksi. 
        Klik iterasi berikutnya untuk melihat pola tumbuh langkah demi langkah.
    </div>
    """,
    unsafe_allow_html=True,
)

sidebar_label("Preset")

preset_name = st.sidebar.selectbox(
    "Preset",
    list(PRESETS.keys()),
    label_visibility="collapsed",
)
preset = PRESETS[preset_name]

if st.session_state.get("_last_preset") != preset_name:
    st.session_state.iteration = int(preset["default_iteration"])
    st.session_state._last_preset = preset_name

if "iteration" not in st.session_state:
    st.session_state.iteration = int(preset["default_iteration"])

custom_mode = st.sidebar.toggle("Custom", value=False, help="Aktifkan untuk mengubah axiom, aturan, sudut, dan simbol.")

if custom_mode:
    with st.sidebar.expander("Aturan", expanded=True):
        axiom = st.text_input("Axiom", value=preset["axiom"])
        rules_text = st.text_area("Rules", value=preset["rules"], height=92)
        draw_symbols = st.text_input("Draw", value=preset["draw_symbols"])
        move_symbols = st.text_input("Move", value=preset["move_symbols"])

    with st.sidebar.expander("Geometri", expanded=True):
        angle = st.number_input("Sudut", min_value=0.0, max_value=180.0, value=float(preset["angle"]), step=0.5)
        start_angle = st.number_input("Arah awal", min_value=-360.0, max_value=360.0, value=float(preset["start_angle"]), step=5.0)
        step = st.number_input("Langkah", min_value=0.1, max_value=20.0, value=float(preset["step"]), step=0.1)
        max_iteration = st.slider("Maks iterasi", min_value=1, max_value=16, value=int(preset["max_iteration"]))
else:
    axiom = preset["axiom"]
    rules_text = preset["rules"]
    angle = float(preset["angle"])
    start_angle = float(preset["start_angle"])
    draw_symbols = preset["draw_symbols"]
    move_symbols = preset["move_symbols"]
    step = float(preset["step"])
    max_iteration = int(preset["max_iteration"])

st.session_state.iteration = max(0, min(int(st.session_state.iteration), int(max_iteration)))

st.sidebar.markdown("---")

if "iteration" not in st.session_state:
    st.session_state.iteration = 0

# Pastikan iterasi tidak melebihi max_iteration
st.session_state.iteration = min(st.session_state.iteration, max_iteration)

sidebar_label("Iterasi")

col1, col2, col3, col4 = st.sidebar.columns(4)

with col1:
    if st.button("‹‹", use_container_width=True):
        st.session_state.iteration = 1
        st.rerun()

with col2:
    if st.button("‹", use_container_width=True):
        st.session_state.iteration = max(1, st.session_state.iteration - 1)
        st.rerun()

with col3:
    if st.button("›", use_container_width=True):
        st.session_state.iteration = min(max_iteration, st.session_state.iteration + 1)
        st.rerun()

with col4:
    if st.button("››", use_container_width=True):
        st.session_state.iteration = max_iteration
        st.rerun()

st.sidebar.slider(
    "Iterasi",
    min_value=1,
    max_value=max_iteration,
    key="iteration",
    label_visibility="collapsed",
)


with st.sidebar.expander("Tampilan", expanded=False):
    theme_name = st.selectbox("Tema", list(THEMES.keys()), index=list(THEMES.keys()).index(preset["theme"]))
    color_mode = st.radio("Warna", ["Kedalaman", "Urutan", "Satu warna"], index=0, horizontal=True)
    line_width = st.slider("Tebal", min_value=0.25, max_value=3.0, value=1.15, step=0.05)
    canvas_ratio = st.selectbox("Kanvas", list(CANVAS_RATIOS.keys()), index=0)
    show_previous_ghost = st.checkbox(
        "Ghost iterasi sebelumnya",
        value=False,
        help="Iterasi i-1 digambar tipis. Ini membantu melihat perkembangan walaupun iterasi aktif selalu fit-to-canvas.",
    )
    ghost_alpha = st.slider("Transparansi ghost", min_value=0.05, max_value=0.60, value=0.20, step=0.05)
    show_start_end = st.checkbox("Titik awal/akhir", value=False)

with st.sidebar.expander("Performa", expanded=False):
    max_chars = st.select_slider(
        "Batas kata",
        options=[25_000, 50_000, 100_000, 250_000, 500_000, 900_000, 1_500_000],
        value=250_000,
        help="Batas ini mencegah browser terlalu berat ketika string L-System meledak.",
    )


# ============================================================
# GENERATE DAN RENDER
# ============================================================
error_message = None
previous_word = ""
previous_segments: list[Segment] = []
previous_truncated = False

try:
    # Validasi aturan lebih awal agar error tampil jelas.
    parse_rules(rules_text)

    word, truncated = produce_lsystem_cached(
        axiom=axiom,
        rules_text=rules_text,
        iteration=st.session_state.iteration,
        max_chars=int(max_chars),
    )
    segments = turtle_segments_cached(
        word=word,
        angle_deg=angle,
        start_angle_deg=start_angle,
        step=step,
        draw_symbols=draw_symbols,
        move_symbols=move_symbols,
    )

    if st.session_state.iteration > 0:
        previous_word, previous_truncated = produce_lsystem_cached(
            axiom=axiom,
            rules_text=rules_text,
            iteration=st.session_state.iteration - 1,
            max_chars=int(max_chars),
        )
        previous_segments = turtle_segments_cached(
            word=previous_word,
            angle_deg=angle,
            start_angle_deg=start_angle,
            step=step,
            draw_symbols=draw_symbols,
            move_symbols=move_symbols,
        )
    else:
        previous_segments = []

except Exception as exc:
    word = ""
    segments = []
    truncated = False
    previous_segments = []
    error_message = str(exc)

# Sidebar info diletakkan setelah generate, tetap tidak mengganggu canvas utama.
st.sidebar.markdown(
    f"""
    <div class="mini-stat">
    <b>{preset_name}</b><br>
    i = {st.session_state.iteration} &nbsp; | &nbsp; kata = {len(word):,} &nbsp; | &nbsp; segmen = {len(segments):,}<br>
    skala = fit iterasi aktif &nbsp; | &nbsp; ghost = {'on' if show_previous_ghost else 'off'}
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar.expander("Info", expanded=False):
    st.markdown(f"<div class='mini-help'>{preset['description']}</div>", unsafe_allow_html=True)
    st.code(
        f"Axiom: {axiom}\n\nRules:\n{rules_text}\n\nAngle: {angle}°\nStart: {start_angle}°\nDraw: {draw_symbols}",
        language="text",
    )

with st.sidebar.expander("Preview kata", expanded=False):
    st.code(compact_preview(word), language="text")

with st.sidebar.expander("Simbol", expanded=False):
    st.markdown(
        """
        `F/G`: gambar  
        `f`: maju tanpa gambar  
        `+`: belok kiri  
        `-`: belok kanan  
        `|`: putar balik  
        `[`: simpan posisi  
        `]`: kembali ke posisi
        """
    )

if error_message:
    st.error(error_message)
else:
    if truncated:
        st.sidebar.warning("Kata dipotong karena melewati batas. Turunkan iterasi atau naikkan batas kata.")
    if previous_truncated:
        st.sidebar.warning("Ghost iterasi sebelumnya terpotong oleh batas kata.")

    # ============================================================
    # AREA UTAMA: CANVAS DULU, TANPA JUDUL DI ATASNYA
    # ============================================================
    fig = render_lsystem(
        segments=segments,
        previous_segments=previous_segments,
        theme_name=theme_name,
        line_width=line_width,
        color_mode=color_mode,
        show_start_end=show_start_end,
        show_previous_ghost=show_previous_ghost,
        ghost_alpha=ghost_alpha,
        canvas_ratio=canvas_ratio,
    )
    st.pyplot(fig, use_container_width=True)

    safe_preset_name = "".join(
        ch.lower() if ch.isalnum() else "_"
        for ch in preset_name
    ).strip("_")

    base_file_name = f"lsystem_{safe_preset_name}_iter_{st.session_state.iteration}"

    svg_buffer = BytesIO()
    fig.savefig(
        svg_buffer,
        format="svg",
        bbox_inches="tight",
        pad_inches=0,
        transparent=False,
    )

    pdf_buffer = BytesIO()
    fig.savefig(
        pdf_buffer,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0,
        transparent=False,
    )

    png_buffer = BytesIO()
    fig.savefig(
        png_buffer,
        format="png",
        dpi=300,
        bbox_inches="tight",
        pad_inches=0,
        transparent=False,
    )

    plt.close(fig)

    with st.expander("Panduan membaca L-System", expanded=False):
        st.markdown(
            """
            L-System bekerja seperti proses pertumbuhan bertahap. Pada setiap iterasi,
            setiap simbol pada string diganti secara serentak menggunakan aturan produksi.

            **Makna simbol utama**

            | Simbol | Makna visual |
            |---|---|
            | `F` | Maju sambil menggambar garis |
            | `f` | Maju tanpa menggambar garis |
            | `+` | Berbelok ke kiri sebesar sudut yang dipilih |
            | `-` | Berbelok ke kanan sebesar sudut yang dipilih |
            | `[` | Menyimpan posisi dan arah saat ini |
            | `]` | Kembali ke posisi dan arah terakhir yang disimpan |

            **Cara membaca pertumbuhan**

            - **Axiom** adalah bentuk awal.
            - **Rule** adalah aturan penggantian simbol.
            - Iterasi ke-1 mengganti axiom satu kali.
            - Iterasi ke-2 mengganti hasil iterasi ke-1.
            - Semakin tinggi iterasi, string makin panjang dan bentuk makin kompleks.
            """
        )
    

    if "show_downloads" not in st.session_state:
        st.session_state.show_downloads = False

    if st.button("Siapkan file unduhan", use_container_width=True):
        st.session_state.show_downloads = True

    if st.session_state.show_downloads:
        links = [
            download_link("TXT", word, f"{base_file_name}.txt", "text/plain"),
            download_link("SVG", svg_buffer.getvalue(), f"{base_file_name}.svg", "image/svg+xml"),
            download_link("PDF", pdf_buffer.getvalue(), f"{base_file_name}.pdf", "application/octet-stream"),
            download_link("PNG", png_buffer.getvalue(), f"{base_file_name}.png", "image/png"),
        ]

        st.markdown(
            '<div class="download-row">' + "".join(links) + "</div>",
            unsafe_allow_html=True,
        )

    
    st.markdown(
        f"""
        <div class="word-panel">
            <div class="word-title">DNA Fraktal: String L-System</div>
            <div class="word-caption">
                Pada iterasi {st.session_state.iteration}, axiom dan rule telah menghasilkan
                {len(word):,} simbol. Dari simbol-simbol ini, turtle menggambar {len(segments):,}
                segmen pada canvas. Jadi, gambar fraktal di atas bukan digambar langsung,
                tetapi muncul dari pembacaan string berikut sebagai rangkaian instruksi.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.text_area(
        "String hasil iterasi",
        value=word,
        height=230,
        label_visibility="collapsed",
        help="Klik di dalam kotak, lalu Ctrl+A dan Ctrl+C untuk menyalin string.",
    )