
import math
from io import BytesIO
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon


# ============================================================
# Fractal Geometry Lab
# Fraktal parametrik tanpa L-System.
#
# Ide utama:
# Objek dasar geometri sederhana disalin, diperkecil, diputar,
# digeser, lalu prosesnya diulang beberapa kali.
#
# Parameter penting:
# - sudut
# - iterasi
# - skala
# - jumlah cabang
# - jarak antarsalinan
# - objek dasar
# ============================================================

st.set_page_config(
    page_title="Fractal Geometry Lab",
    page_icon="✦",
    layout="wide",
)


# ------------------------------------------------------------
# Utilitas transformasi affine 2D
# ------------------------------------------------------------
def T(tx, ty):
    return np.array([
        [1.0, 0.0, tx],
        [0.0, 1.0, ty],
        [0.0, 0.0, 1.0],
    ])


def R(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([
        [c, -s, 0.0],
        [s,  c, 0.0],
        [0.0, 0.0, 1.0],
    ])


def S(scale):
    return np.array([
        [scale, 0.0, 0.0],
        [0.0, scale, 0.0],
        [0.0, 0.0, 1.0],
    ])


def apply(M, points):
    pts = np.array([[x, y, 1.0] for x, y in points], dtype=float).T
    out = (M @ pts).T
    return [(float(x), float(y)) for x, y, _ in out]


def centroid(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return sum(xs) / len(xs), sum(ys) / len(ys)


# ------------------------------------------------------------
# Objek dasar
# ------------------------------------------------------------
def regular_polygon(n=6, radius=1.0, rotation=-90):
    pts = []
    for i in range(n):
        a = math.radians(rotation + 360 * i / n)
        pts.append((radius * math.cos(a), radius * math.sin(a)))
    return pts


def star(n=5, r_outer=1.0, r_inner=0.43, rotation=-90):
    pts = []
    for i in range(2 * n):
        r = r_outer if i % 2 == 0 else r_inner
        a = math.radians(rotation + 180 * i / n)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def ellipse_poly(rx=1.0, ry=0.45, n=80):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        pts.append((rx * math.cos(a), ry * math.sin(a)))
    return pts


def petal_poly(n=80):
    # Bentuk daun/kelopak sederhana dari elips yang agak runcing.
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        r = 0.55 + 0.45 * math.cos(t)
        x = 1.2 * r * math.cos(t)
        y = 0.55 * math.sin(t)
        pts.append((x - 0.35, y))
    return pts


def diamond():
    return [(0, -1), (1, 0), (0, 1), (-1, 0)]


BASE_OBJECTS = {
    "Lingkaran": ellipse_poly(1, 1, 72),
    "Elips": ellipse_poly(1.25, 0.55, 72),
    "Kelopak/Daun": petal_poly(90),
    "Segitiga": regular_polygon(3, 1, -90),
    "Persegi": regular_polygon(4, 1, -45),
    "Belah Ketupat": diamond(),
    "Pentagon": regular_polygon(5, 1, -90),
    "Heksagon": regular_polygon(6, 1, -90),
    "Bintang 5": star(5, 1.0, 0.42, -90),
    "Bintang 8": star(8, 1.0, 0.45, -90),
}


# ------------------------------------------------------------
# Warna
# ------------------------------------------------------------
PALETTES = {
    "Sogan": {
        "bg": "#F4E3BF",
        "stroke": "#2B1608",
        "fill1": "#C58A3A",
        "fill2": "#8B4A1E",
        "fill3": "#E7C98C",
    },
    "Keraton Gelap": {
        "bg": "#15100A",
        "stroke": "#F2D27D",
        "fill1": "#B77A2B",
        "fill2": "#FFF0B7",
        "fill3": "#3A2A16",
    },
    "Indigo": {
        "bg": "#101724",
        "stroke": "#D7E7FF",
        "fill1": "#3F6EA8",
        "fill2": "#8FB7E8",
        "fill3": "#1E314D",
    },
    "Mega Mendung": {
        "bg": "#DDEAF2",
        "stroke": "#102A43",
        "fill1": "#2F6F9F",
        "fill2": "#66A6C9",
        "fill3": "#B7D7E8",
    },
    "Monokrom": {
        "bg": "#F2EFE8",
        "stroke": "#111111",
        "fill1": "#555555",
        "fill2": "#999999",
        "fill3": "#D9D4C8",
    },
}


def color_by_depth(depth, max_depth, palette):
    if max_depth <= 0:
        return palette["fill1"]
    t = depth / max_depth
    if t < 0.34:
        return palette["fill1"]
    if t < 0.67:
        return palette["fill2"]
    return palette["fill3"]


# ------------------------------------------------------------
# Scene
# ------------------------------------------------------------
def add_polygon(scene, points, fill, stroke, sw=1.0, opacity=1.0):
    scene.append({
        "points": points,
        "fill": fill,
        "stroke": stroke,
        "sw": sw,
        "opacity": opacity,
    })


def add_base_object(scene, M, base_points, size, fill, stroke, sw, opacity):
    pts = apply(M @ S(size), base_points)
    add_polygon(scene, pts, fill, stroke, sw, opacity)


def estimate_count(family, branches, iterations):
    if family in ["Bercabang Simetris", "Roset Rekursif", "Coral Geometris"]:
        if branches <= 1:
            return iterations + 1
        return (branches ** (iterations + 1) - 1) // (branches - 1)
    if family == "Spiral Tunggal":
        return iterations + 1
    if family == "Vertex Polygon Fractal":
        return (branches ** (iterations + 1) - 1) // (branches - 1)
    return 0


# ------------------------------------------------------------
# Generator fraktal
# ------------------------------------------------------------
def generate_branching(
    scene, M, depth, max_depth, base_points,
    size, angle, scale, branches, step,
    palette, stroke_width, opacity_decay, spread_mode,
    max_shapes_state
):
    if max_shapes_state["count"] >= max_shapes_state["limit"]:
        return

    fill = color_by_depth(max_depth - depth, max_depth, palette)
    opacity = max(0.06, opacity_decay ** (max_depth - depth))
    add_base_object(scene, M, base_points, size, fill, palette["stroke"], stroke_width, opacity)
    max_shapes_state["count"] += 1

    if depth <= 0:
        return

    if branches == 1:
        angles = [angle]
    else:
        if spread_mode == "Kipas":
            start = -angle * (branches - 1) / 2
            angles = [start + i * angle for i in range(branches)]
        elif spread_mode == "Melingkar":
            angles = [angle + 360 * i / branches for i in range(branches)]
        else:
            # Bergantian kanan-kiri.
            raw = []
            for i in range(branches):
                k = i // 2 + 1
                raw.append(k * angle if i % 2 == 0 else -k * angle)
            angles = raw

    for a in angles:
        child = M @ R(a) @ T(0, -step) @ S(scale)
        generate_branching(
            scene, child, depth - 1, max_depth, base_points,
            size, angle, scale, branches, step,
            palette, stroke_width * 0.95, opacity_decay, spread_mode,
            max_shapes_state
        )


def generate_spiral(
    scene, M, iterations, base_points, size, angle, scale, step,
    palette, stroke_width, opacity_decay, max_shapes_state
):
    current = M.copy()
    current_size = size

    for i in range(iterations + 1):
        if max_shapes_state["count"] >= max_shapes_state["limit"]:
            break

        fill = color_by_depth(i, iterations, palette)
        opacity = max(0.06, opacity_decay ** i)
        add_base_object(scene, current, base_points, current_size, fill, palette["stroke"], stroke_width, opacity)
        max_shapes_state["count"] += 1

        current = current @ R(angle) @ T(step, 0) @ S(scale)
        current_size *= 1.0


def generate_vertex_polygon(
    scene, M, depth, max_depth, base_points, size, angle, scale, branches, step,
    palette, stroke_width, opacity_decay, max_shapes_state
):
    if max_shapes_state["count"] >= max_shapes_state["limit"]:
        return

    fill = color_by_depth(max_depth - depth, max_depth, palette)
    opacity = max(0.06, opacity_decay ** (max_depth - depth))
    add_base_object(scene, M, base_points, size, fill, palette["stroke"], stroke_width, opacity)
    max_shapes_state["count"] += 1

    if depth <= 0:
        return

    # Anak-anak diletakkan pada titik sudut poligon imajiner.
    verts = regular_polygon(branches, radius=step, rotation=-90 + angle)
    for vx, vy in verts:
        child = M @ T(vx, vy) @ R(angle) @ S(scale)
        generate_vertex_polygon(
            scene, child, depth - 1, max_depth, base_points,
            size, angle, scale, branches, step,
            palette, stroke_width * 0.95, opacity_decay, max_shapes_state
        )


def generate_fractal(
    family, width, height, base_points, iterations, angle, scale, branches,
    step, size, palette, stroke_width, opacity_decay, max_shapes
):
    scene = []
    start = T(width / 2, height / 2)

    state = {"count": 0, "limit": max_shapes}

    if family == "Bercabang Simetris":
        # Cabang seperti pohon/karang, tetapi objeknya murni geometri.
        start = T(width / 2, height * 0.76)
        generate_branching(
            scene, start, iterations, iterations, base_points,
            size, angle, scale, branches, step,
            palette, stroke_width, opacity_decay, "Kipas", state
        )

    elif family == "Roset Rekursif":
        # Anak-anak menyebar melingkar. Cocok untuk bunga/mandala.
        start = T(width / 2, height / 2)
        generate_branching(
            scene, start, iterations, iterations, base_points,
            size, angle, scale, branches, step,
            palette, stroke_width, opacity_decay, "Melingkar", state
        )

    elif family == "Coral Geometris":
        # Cabang bergantian kanan-kiri. Sering menghasilkan bentuk koral/naga/ornamen.
        start = T(width / 2, height * 0.72)
        generate_branching(
            scene, start, iterations, iterations, base_points,
            size, angle, scale, branches, step,
            palette, stroke_width, opacity_decay, "Alternating", state
        )

    elif family == "Spiral Tunggal":
        # Satu salinan berubah terus. Cocok untuk spiral, pusaran, atau cangkang.
        start = T(width / 2, height / 2)
        generate_spiral(
            scene, start, iterations * max(1, branches), base_points,
            size, angle, scale, step, palette, stroke_width, opacity_decay, state
        )

    elif family == "Vertex Polygon Fractal":
        # Salinan diletakkan di sudut poligon. Cocok untuk bentuk snowflake/geometri.
        start = T(width / 2, height / 2)
        generate_vertex_polygon(
            scene, start, iterations, iterations, base_points,
            size, angle, scale, branches, step,
            palette, stroke_width, opacity_decay, state
        )

    return scene, state["count"]


# ------------------------------------------------------------
# SVG dan PNG
# ------------------------------------------------------------
def points_to_svg(points):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def scene_to_svg(scene, width, height, bg):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{bg}"/>',
    ]

    for s in scene:
        pts = points_to_svg(s["points"])
        parts.append(
            f'<polygon points="{pts}" '
            f'fill="{s["fill"]}" stroke="{s["stroke"]}" '
            f'stroke-width="{s["sw"]:.2f}" opacity="{s["opacity"]:.3f}" '
            f'stroke-linejoin="round"/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def scene_to_png(scene, width, height, bg, dpi=170):
    fig_w = width / dpi
    fig_h = height / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.set_aspect("equal")
    ax.axis("off")

    for s in scene:
        patch = MplPolygon(
            s["points"],
            closed=True,
            facecolor=s["fill"],
            edgecolor=s["stroke"],
            linewidth=s["sw"],
            alpha=s["opacity"],
            joinstyle="round",
        )
        ax.add_patch(patch)

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def preview_html(svg, height):
    return f"""
    <div style="
        width:100%;
        height:{height}px;
        overflow:auto;
        border:1px solid rgba(120,120,120,0.25);
        border-radius:18px;
        padding:10px;
        background:#fafafa;
        box-sizing:border-box;">
        {svg}
    </div>
    """


# ------------------------------------------------------------
# Preset eksplorasi
# ------------------------------------------------------------
PRESETS = {
    "Bunga Rekursif": {
        "family": "Roset Rekursif",
        "object": "Kelopak/Daun",
        "iterations": 4,
        "angle": 18,
        "scale": 0.52,
        "branches": 7,
        "step": 96,
        "size": 42,
    },
    "Koral Geometris": {
        "family": "Coral Geometris",
        "object": "Elips",
        "iterations": 5,
        "angle": 32,
        "scale": 0.66,
        "branches": 3,
        "step": 104,
        "size": 32,
    },
    "Snowflake Poligon": {
        "family": "Vertex Polygon Fractal",
        "object": "Heksagon",
        "iterations": 4,
        "angle": 0,
        "scale": 0.43,
        "branches": 6,
        "step": 128,
        "size": 44,
    },
    "Cangkang Spiral": {
        "family": "Spiral Tunggal",
        "object": "Elips",
        "iterations": 8,
        "angle": 31,
        "scale": 0.91,
        "branches": 5,
        "step": 45,
        "size": 46,
    },
    "Ornamen Naga Abstrak": {
        "family": "Coral Geometris",
        "object": "Belah Ketupat",
        "iterations": 7,
        "angle": 45,
        "scale": 0.72,
        "branches": 2,
        "step": 82,
        "size": 26,
    },
}


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("Fractal Geometry Lab")
st.caption("Fraktal parametrik dari objek geometri sederhana. Ubah sudut, skala, cabang, dan iterasi untuk memunculkan bentuk yang berbeda.")

with st.sidebar:
    st.header("Preset")
    preset_name = st.selectbox("Pilih preset awal", list(PRESETS.keys()), index=0)
    preset = PRESETS[preset_name]

    st.header("Kanvas")
    width = st.slider("Lebar", 500, 1800, 1100, 50)
    height = st.slider("Tinggi", 400, 1600, 800, 50)

    st.header("Mesin Fraktal")
    family_options = ["Bercabang Simetris", "Roset Rekursif", "Coral Geometris", "Spiral Tunggal", "Vertex Polygon Fractal"]
    family = st.selectbox("Keluarga bentuk", family_options, index=family_options.index(preset["family"]))

    object_options = list(BASE_OBJECTS.keys())
    base_object = st.selectbox("Objek dasar", object_options, index=object_options.index(preset["object"]))

    iterations = st.slider("Iterasi", 0, 8, preset["iterations"], 1)
    angle = st.slider("Sudut rotasi", -180, 180, preset["angle"], 1)
    scale = st.slider("Skala anak", 0.20, 0.95, float(preset["scale"]), 0.01)
    branches = st.slider("Jumlah cabang/salinan", 1, 8, preset["branches"], 1)
    step = st.slider("Jarak antarsalinan", 10, 220, preset["step"], 2)
    size = st.slider("Ukuran objek dasar", 4, 120, preset["size"], 2)

    st.header("Visual")
    palette_name = st.selectbox("Palet", list(PALETTES.keys()), index=0)
    stroke_width = st.slider("Ketebalan garis", 0.2, 5.0, 1.2, 0.1)
    opacity_decay = st.slider("Pelemahan opacity per level", 0.55, 1.00, 0.88, 0.01)
    max_shapes = st.slider("Batas maksimal objek", 100, 12000, 5000, 100)

    custom_color = st.toggle("Warna manual", value=False)
    palette = PALETTES[palette_name].copy()

    if custom_color:
        palette["bg"] = st.color_picker("Background", palette["bg"])
        palette["stroke"] = st.color_picker("Garis", palette["stroke"])
        palette["fill1"] = st.color_picker("Isi level awal", palette["fill1"])
        palette["fill2"] = st.color_picker("Isi level tengah", palette["fill2"])
        palette["fill3"] = st.color_picker("Isi level akhir", palette["fill3"])


base_points = BASE_OBJECTS[base_object]

scene, count = generate_fractal(
    family=family,
    width=width,
    height=height,
    base_points=base_points,
    iterations=iterations,
    angle=angle,
    scale=scale,
    branches=branches,
    step=step,
    size=size,
    palette=palette,
    stroke_width=stroke_width,
    opacity_decay=opacity_decay,
    max_shapes=max_shapes,
)

svg = scene_to_svg(scene, width, height, palette["bg"])
png = scene_to_png(scene, width, height, palette["bg"])

left, right = st.columns([1.2, 0.8])

with left:
    st.subheader("Preview")
    ph = min(760, max(430, int(height * 0.72)))
    components.html(preview_html(svg, ph), height=ph + 28, scrolling=False)

with right:
    st.subheader("Makna Parameter")

    st.markdown(
        f"""
        **Bentuk aktif**

        - Keluarga: `{family}`
        - Objek dasar: `{base_object}`
        - Iterasi: `{iterations}`
        - Sudut: `{angle}°`
        - Skala anak: `{scale}`
        - Cabang/salinan: `{branches}`
        - Jumlah objek tergambar: `{count}`
        """
    )

    st.info(
        """
        Prinsipnya: objek dasar disalin, diperkecil, diputar, digeser, lalu aturan itu diulang.
        Karena itu perubahan kecil pada sudut atau skala dapat membuat objek akhir berubah menjadi bunga,
        koral, spiral, snowflake, ornamen naga abstrak, atau struktur geometris lain.
        """
    )

    with st.expander("Contoh eksplorasi sudut", expanded=True):
        st.markdown(
            """
            Coba kombinasi berikut:

            - Sudut `18°`, roset, cabang `7`: cenderung menjadi bunga.
            - Sudut `30°–36°`, spiral: cenderung menjadi cangkang/pusaran.
            - Sudut `45°`, cabang `2`: sering menjadi ornamen patah seperti naga abstrak.
            - Sudut `60°`, vertex polygon, cabang `6`: cenderung menjadi snowflake/geometri heksagonal.
            - Sudut `90°`, objek persegi/belah ketupat: cenderung menjadi pola geometris kaku.
            """
        )

    st.markdown("#### Ekspor")
    st.download_button(
        "Unduh SVG",
        data=svg.encode("utf-8"),
        file_name="fractal_geometry.svg",
        mime="image/svg+xml",
        use_container_width=True,
    )

    st.download_button(
        "Unduh PNG",
        data=png,
        file_name="fractal_geometry.png",
        mime="image/png",
        use_container_width=True,
    )


st.markdown("---")
st.markdown(
    """
    **Catatan:** Ini bukan L-System. Tidak ada string, axiom, atau aturan produksi.
    Yang dipakai adalah iterasi transformasi geometri: rotasi, translasi, dan skala.
    """
)
