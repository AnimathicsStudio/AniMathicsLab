
import math
import cmath
from collections import deque

import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# Fractal Ornament Studio
# ============================================================
#
# Fokus app:
# Dari proses matematika sederhana menjadi ornamen visual:
# 1. Pythagoras Tree
# 2. Pythagoras Cube
# 3. Dragon Curve Ornament
# 4. Apollonian Circle Ornament
#
# Output utama: SVG.
# Dependencies: Streamlit only.
# ============================================================


st.set_page_config(
    page_title="Fractal Ornament Studio",
    page_icon="✦",
    layout="wide",
)


PALETTES = {
    "Sogan Batik": {
        "bg": "#F4E3BF",
        "ink": "#2B1608",
        "c1": "#8B4A1E",
        "c2": "#C58A3A",
        "c3": "#E7C98C",
        "c4": "#FFF3D0",
        "muted": "#6A3A17",
    },
    "Indigo Malam": {
        "bg": "#101724",
        "ink": "#D7E7FF",
        "c1": "#1E314D",
        "c2": "#3F6EA8",
        "c3": "#8FB7E8",
        "c4": "#EEF6FF",
        "muted": "#789BC4",
    },
    "Keraton Gelap": {
        "bg": "#14100A",
        "ink": "#FFE8A3",
        "c1": "#3A2A16",
        "c2": "#6F3E18",
        "c3": "#B77A2B",
        "c4": "#F2D27D",
        "muted": "#D6A447",
    },
    "Mega Mendung": {
        "bg": "#DDEAF2",
        "ink": "#102A43",
        "c1": "#B7D7E8",
        "c2": "#66A6C9",
        "c3": "#2F6F9F",
        "c4": "#F4FBFF",
        "muted": "#1F4E73",
    },
    "Merah Bata": {
        "bg": "#F1D5B8",
        "ink": "#3A120A",
        "c1": "#E8AA7A",
        "c2": "#D46A3A",
        "c3": "#9D2F17",
        "c4": "#FFE8CE",
        "muted": "#7E2717",
    },
    "Monokrom Tinta": {
        "bg": "#F2EFE8",
        "ink": "#111111",
        "c1": "#D9D4C8",
        "c2": "#999999",
        "c3": "#555555",
        "c4": "#FFFFFF",
        "muted": "#333333",
    },
}


def palette_list(p):
    return [p["c1"], p["c2"], p["c3"], p["c4"], p["c3"], p["c2"]]


# ------------------------------------------------------------
# SVG utilities
# ------------------------------------------------------------
def svg_header(width, height, bg):
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img">
<rect x="0" y="0" width="{width}" height="{height}" fill="{bg}"/>
<defs>
  <clipPath id="canvasClip">
    <rect x="0" y="0" width="{width}" height="{height}"/>
  </clipPath>
</defs>
"""


def svg_footer():
    return "</svg>"


def polygon(points, fill, stroke="#000", sw=1, opacity=1):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return (
        f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw:.2f}" opacity="{opacity:.3f}" stroke-linejoin="round"/>'
    )


def circle(cx, cy, r, fill="none", stroke="#000", sw=1, opacity=1):
    return (
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}" opacity="{opacity:.3f}"/>'
    )


def line(x1, y1, x2, y2, stroke="#000", sw=1, opacity=1):
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{sw:.2f}" opacity="{opacity:.3f}" stroke-linecap="round"/>'
    )


def path(d, fill="none", stroke="#000", sw=1, opacity=1):
    return (
        f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}" '
        f'opacity="{opacity:.3f}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def polyline_path(points):
    if not points:
        return ""
    d = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    for x, y in points[1:]:
        d.append(f"L {x:.2f} {y:.2f}")
    return " ".join(d)


def preview_html(svg, height):
    return f"""
    <div style="
        width:100%;
        height:{height}px;
        overflow:auto;
        border:1px solid rgba(120,120,120,.28);
        border-radius:18px;
        background:#fafafa;
        padding:10px;
        box-sizing:border-box;">
        {svg}
    </div>
    """


def add_texture(width, height, p, density=220, seed=1):
    # Deterministic simple pseudo-random dots without importing random globally.
    # This is only visual finishing, not part of the mathematics.
    import random
    rng = random.Random(seed)
    out = []
    for _ in range(density):
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)
        r = rng.uniform(0.35, 1.25)
        color = p["c4"] if rng.random() < 0.55 else p["muted"]
        opacity = rng.uniform(0.035, 0.11)
        out.append(circle(x, y, r, fill=color, stroke="none", opacity=opacity))
    return "\n".join(out)


# ------------------------------------------------------------
# Pythagoras Tree / Cube
# ------------------------------------------------------------
def square_from_base(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    nx = dy
    ny = -dx
    q1 = (x1 + nx, y1 + ny)
    q2 = (x2 + nx, y2 + ny)
    return [p1, p2, q2, q1], q1, q2


def pythagoras_nodes(p1, p2, depth, angle_deg, min_size=1.5):
    nodes = []

    def rec(a, b, level):
        x1, y1 = a
        x2, y2 = b
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)

        if L < min_size:
            return

        sq, q1, q2 = square_from_base(a, b)
        cx = sum(x for x, _ in sq) / 4
        cy = sum(y for _, y in sq) / 4
        nodes.append(
            {
                "square": sq,
                "center": (cx, cy),
                "side": L,
                "level": level,
            }
        )

        if level >= depth:
            return

        alpha = math.radians(angle_deg)
        ux = (q2[0] - q1[0]) / L
        uy = (q2[1] - q1[1]) / L

        # normal pointing outward from the current square
        nx = uy
        ny = -ux

        # Pythagoras triangle apex on top of square.
        proj = L * (math.cos(alpha) ** 2)
        h = L * math.sin(alpha) * math.cos(alpha)
        apex = (q1[0] + ux * proj + nx * h, q1[1] + uy * proj + ny * h)

        rec(q1, apex, level + 1)
        rec(apex, q2, level + 1)

    rec(p1, p2, 0)
    return nodes


def oriented_base(center, length, outward_angle_deg):
    cx, cy = center
    phi = math.radians(outward_angle_deg)
    gx = math.cos(phi)
    gy = math.sin(phi)

    # base vector b such that normal(dy,-dx) equals growth direction g.
    bx = -gy
    by = gx
    p1 = (cx - bx * length / 2, cy - by * length / 2)
    p2 = (cx + bx * length / 2, cy + by * length / 2)
    return p1, p2


def build_pythagoras_tree_svg(width, height, p, depth, angle, base_len, mode, reps, stroke_width, fill_mode, texture, seed):
    out = [svg_header(width, height, p["bg"])]
    if texture:
        out.append(add_texture(width, height, p, int(width * height / 4200), seed))

    colors = palette_list(p)
    out.append('<g clip-path="url(#canvasClip)">')

    if mode == "Single":
        centers_angles = [((width / 2, height * 0.84), -90)]
    elif mode == "Mirror":
        centers_angles = [
            ((width * 0.36, height * 0.84), -90),
            ((width * 0.64, height * 0.84), -90),
        ]
    elif mode == "Radial":
        centers_angles = []
        cx, cy = width / 2, height / 2
        inner_r = min(width, height) * 0.10
        for k in range(reps):
            phi = -90 + 360 * k / reps
            rad = math.radians(phi)
            center = (cx + inner_r * math.cos(rad), cy + inner_r * math.sin(rad))
            centers_angles.append((center, phi))
    else:
        centers_angles = [((width / 2, height * 0.84), -90)]

    all_nodes = []
    for center, phi in centers_angles:
        p1, p2 = oriented_base(center, base_len, phi)
        all_nodes.extend(pythagoras_nodes(p1, p2, depth, angle, min_size=1.2))

    # Draw larger/lower levels first.
    for node in sorted(all_nodes, key=lambda z: z["level"]):
        level = node["level"]
        fill = colors[level % len(colors)] if fill_mode else "none"
        opacity = max(0.18, 0.94 - 0.035 * level)
        out.append(polygon(node["square"], fill=fill, stroke=p["ink"], sw=stroke_width, opacity=opacity))

    out.append("</g>")
    out.append(svg_footer())
    return "\n".join(out), len(all_nodes)


def iso_cube(cx, cy, s, p, level, stroke_width):
    w = s * 0.42
    h = s * 0.30
    # scale down for readability
    top = [(cx, cy - h), (cx + w, cy - h / 2), (cx, cy), (cx - w, cy - h / 2)]
    left = [(cx - w, cy - h / 2), (cx, cy), (cx, cy + h), (cx - w, cy + h / 2)]
    right = [(cx + w, cy - h / 2), (cx, cy), (cx, cy + h), (cx + w, cy + h / 2)]
    colors = palette_list(p)
    c = colors[level % len(colors)]
    return "\n".join(
        [
            polygon(left, fill=p["c1"], stroke=p["ink"], sw=stroke_width, opacity=0.92),
            polygon(right, fill=p["c2"], stroke=p["ink"], sw=stroke_width, opacity=0.92),
            polygon(top, fill=c, stroke=p["ink"], sw=stroke_width, opacity=0.96),
        ]
    )


def build_pythagoras_cube_svg(width, height, p, depth, angle, base_len, mode, reps, stroke_width, texture, seed):
    out = [svg_header(width, height, p["bg"])]
    if texture:
        out.append(add_texture(width, height, p, int(width * height / 4300), seed))
    out.append('<g clip-path="url(#canvasClip)">')

    if mode == "Single":
        centers_angles = [((width / 2, height * 0.82), -90)]
    elif mode == "Radial":
        centers_angles = []
        cx, cy = width / 2, height / 2
        inner_r = min(width, height) * 0.08
        for k in range(reps):
            phi = -90 + 360 * k / reps
            rad = math.radians(phi)
            center = (cx + inner_r * math.cos(rad), cy + inner_r * math.sin(rad))
            centers_angles.append((center, phi))
    else:
        centers_angles = [((width / 2, height * 0.82), -90)]

    all_nodes = []
    for center, phi in centers_angles:
        p1, p2 = oriented_base(center, base_len, phi)
        all_nodes.extend(pythagoras_nodes(p1, p2, depth, angle, min_size=3.5))

    # Draw from high level first or low? Cubes look better if small behind first.
    for node in sorted(all_nodes, key=lambda z: z["level"], reverse=True):
        cx, cy = node["center"]
        s = node["side"]
        if s >= 4:
            out.append(iso_cube(cx, cy, s, p, node["level"], stroke_width))

    out.append("</g>")
    out.append(svg_footer())
    return "\n".join(out), len(all_nodes)


# ------------------------------------------------------------
# Dragon Curve
# ------------------------------------------------------------
def dragon_turns(order):
    turns = []
    for _ in range(order):
        inv_rev = [-t for t in reversed(turns)]
        turns = turns + [1] + inv_rev
    return turns


def dragon_raw_points(order, turn_angle_deg=90):
    turns = dragon_turns(order)
    angle = 0.0
    x, y = 0.0, 0.0
    pts = [(x, y)]
    step = 1.0
    for t in turns:
        # Move, then turn.
        x += step * math.cos(math.radians(angle))
        y += step * math.sin(math.radians(angle))
        pts.append((x, y))
        angle += t * turn_angle_deg
    # final segment
    x += step * math.cos(math.radians(angle))
    y += step * math.sin(math.radians(angle))
    pts.append((x, y))
    return pts


def normalize_points(points, width, height, margin):
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    spanx = max(1e-9, maxx - minx)
    spany = max(1e-9, maxy - miny)
    scale = min((width - 2 * margin) / spanx, (height - 2 * margin) / spany)
    ox = (width - scale * (minx + maxx)) / 2
    oy = (height - scale * (miny + maxy)) / 2
    return [(ox + x * scale, oy + y * scale) for x, y in points]


def rotate_points(points, cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in points:
        u, v = x - cx, y - cy
        out.append((cx + ca * u - sa * v, cy + sa * u + ca * v))
    return out


def build_dragon_svg(width, height, p, order, turn_angle, mode, reps, stroke_width, glow, texture, seed):
    out = [svg_header(width, height, p["bg"])]
    if texture:
        out.append(add_texture(width, height, p, int(width * height / 4700), seed))
    out.append('<g clip-path="url(#canvasClip)">')

    raw = dragon_raw_points(order, turn_angle)
    base = normalize_points(raw, width, height, margin=50)
    cx, cy = width / 2, height / 2

    if mode == "Single":
        copies = [(base, 0)]
    elif mode == "Mirror":
        mirrored = [(width - x, y) for x, y in base]
        copies = [(base, 0), (mirrored, 0)]
    elif mode == "Radial":
        copies = [(rotate_points(base, cx, cy, 360 * k / reps), k) for k in range(reps)]
    else:
        copies = [(base, 0)]

    colors = palette_list(p)

    for pts, idx in copies:
        d = polyline_path(pts)
        if glow:
            out.append(path(d, fill="none", stroke=p["c4"], sw=stroke_width * 3.0, opacity=0.12))
            out.append(path(d, fill="none", stroke=p["c2"], sw=stroke_width * 1.8, opacity=0.23))
        out.append(path(d, fill="none", stroke=colors[idx % len(colors)], sw=stroke_width, opacity=0.95))
        out.append(path(d, fill="none", stroke=p["ink"], sw=max(0.35, stroke_width * 0.28), opacity=0.62))

    # center marker for radial ornament
    if mode == "Radial":
        out.append(circle(cx, cy, max(3, stroke_width * 1.8), fill=p["c4"], stroke=p["ink"], sw=stroke_width * 0.45, opacity=0.95))

    out.append("</g>")
    out.append(svg_footer())
    return "\n".join(out), len(raw) - 1


# ------------------------------------------------------------
# Apollonian Circle Ornament
# ------------------------------------------------------------
def initial_apollonian():
    # Unit outer circle, three equal mutually tangent inner circles.
    R = 1.0
    r = math.sqrt(3) / (2 + math.sqrt(3))
    d = R - r
    outer = (-1.0, 0 + 0j, 0)
    circles = [outer]
    for ang in [90, 210, 330]:
        z = d * complex(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        circles.append((1 / r, z, 0))
    return circles


def replace_circle(q, i):
    b = [c[0] for c in q]
    z = [c[1] for c in q]
    b_new = 2 * sum(b[j] for j in range(4) if j != i) - b[i]
    bz_new = 2 * sum(b[j] * z[j] for j in range(4) if j != i) - b[i] * z[i]
    if abs(b_new) < 1e-12:
        return None
    z_new = bz_new / b_new
    return (b_new, z_new)


def generate_apollonian(depth, min_radius=0.003):
    start = initial_apollonian()
    all_circles = {}
    q0 = tuple(start)
    queue = deque([(q0, 0)])

    def add_circle(b, z, level):
        if b <= 0:
            return
        r = 1 / b
        if r < min_radius:
            return
        key = (round(z.real, 5), round(z.imag, 5), round(r, 5))
        if key not in all_circles or level < all_circles[key][2]:
            all_circles[key] = (b, z, level)

    for b, z, level in start:
        add_circle(b, z, level)

    seen_quad = set()
    while queue:
        q, level = queue.popleft()
        if level >= depth:
            continue

        quad_key = tuple((round(c[0], 6), round(c[1].real, 6), round(c[1].imag, 6)) for c in q)
        if quad_key in seen_quad:
            continue
        seen_quad.add(quad_key)

        for i in range(4):
            new = replace_circle(q, i)
            if new is None:
                continue
            b_new, z_new = new
            new_circle = (b_new, z_new, level + 1)
            if b_new > 0 and 1 / b_new >= min_radius:
                add_circle(b_new, z_new, level + 1)

            q_list = list(q)
            q_list[i] = new_circle
            queue.append((tuple(q_list), level + 1))

    return list(all_circles.values())


def build_apollonian_svg(width, height, p, depth, stroke_width, fill_mode, show_outer, texture, seed):
    out = [svg_header(width, height, p["bg"])]
    if texture:
        out.append(add_texture(width, height, p, int(width * height / 4300), seed))
    out.append('<g clip-path="url(#canvasClip)">')

    circles = generate_apollonian(depth, min_radius=0.0025)
    scale = min(width, height) * 0.43
    cx, cy = width / 2, height / 2
    colors = palette_list(p)

    # Draw larger circles first.
    positive = [(b, z, lvl) for b, z, lvl in circles if b > 0]
    positive.sort(key=lambda c: 1 / c[0], reverse=True)

    for b, z, lvl in positive:
        r = 1 / b
        x = cx + z.real * scale
        y = cy - z.imag * scale
        rr = r * scale
        fill = colors[lvl % len(colors)] if fill_mode else "none"
        opacity = max(0.18, 0.82 - lvl * 0.035)
        out.append(circle(x, y, rr, fill=fill, stroke=p["ink"], sw=stroke_width, opacity=opacity))

    if show_outer:
        out.append(circle(cx, cy, scale, fill="none", stroke=p["ink"], sw=stroke_width * 1.5, opacity=0.95))
        out.append(circle(cx, cy, scale * 0.985, fill="none", stroke=p["muted"], sw=stroke_width * 0.55, opacity=0.8))

    # Ornament center dot
    out.append(circle(cx, cy, max(2.0, stroke_width * 1.3), fill=p["c4"], stroke=p["ink"], sw=stroke_width * 0.5, opacity=0.9))

    out.append("</g>")
    out.append(svg_footer())
    return "\n".join(out), len(positive)


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("Fractal Ornament Studio")
st.caption("Dari aturan matematika sederhana menjadi ornamen visual: Pythagoras, Dragon Curve, dan Apollonian circle packing.")

with st.sidebar:
    st.header("Mesin Ornamen")
    engine = st.selectbox(
        "Pilih mesin",
        [
            "Pythagoras Tree",
            "Pythagoras Cube",
            "Dragon Curve Ornament",
            "Apollonian Circle Ornament",
        ],
        index=0,
    )

    palette_name = st.selectbox("Palet", list(PALETTES.keys()), index=0)
    p = PALETTES[palette_name]

    st.header("Kanvas")
    width = st.slider("Lebar", 700, 1900, 1200, 50)
    height = st.slider("Tinggi", 500, 1500, 850, 50)
    texture = st.toggle("Tekstur latar halus", value=True)
    seed = st.number_input("Seed tekstur", min_value=1, max_value=999999, value=17, step=1)

    if engine in ["Pythagoras Tree", "Pythagoras Cube"]:
        st.header("Parameter Pythagoras")
        depth_max = 11 if engine == "Pythagoras Tree" else 9
        depth_default = 8 if engine == "Pythagoras Tree" else 7
        depth = st.slider("Iterasi / kedalaman", 0, depth_max, depth_default, 1)
        angle = st.slider("Sudut segitiga", 18, 72, 45, 1)
        base_len = st.slider("Ukuran persegi awal", 25, 220, 92, 2)
        mode = st.selectbox("Mode komposisi", ["Single", "Mirror", "Radial"], index=0)
        reps = st.slider("Jumlah salinan radial", 3, 14, 8, 1)
        stroke_width = st.slider("Ketebalan outline", 0.2, 4.0, 1.0, 0.1)
        fill_mode = True
        if engine == "Pythagoras Tree":
            fill_mode = st.toggle("Isi bidang persegi", value=True)

    elif engine == "Dragon Curve Ornament":
        st.header("Parameter Dragon Curve")
        order = st.slider("Iterasi / order", 1, 16, 12, 1)
        turn_angle = st.slider("Sudut belok", 45, 135, 90, 1)
        mode = st.selectbox("Mode komposisi", ["Single", "Mirror", "Radial"], index=0)
        reps = st.slider("Jumlah salinan radial", 3, 18, 8, 1)
        stroke_width = st.slider("Ketebalan garis", 0.3, 7.0, 2.0, 0.1)
        glow = st.toggle("Efek glow/lapisan warna", value=True)

    else:
        st.header("Parameter Apollonian")
        depth = st.slider("Iterasi / kedalaman", 0, 9, 5, 1)
        stroke_width = st.slider("Ketebalan outline", 0.2, 3.5, 0.9, 0.1)
        fill_mode = st.toggle("Isi lingkaran", value=True)
        show_outer = st.toggle("Tampilkan lingkaran luar", value=True)


if engine == "Pythagoras Tree":
    svg, count = build_pythagoras_tree_svg(
        width=width,
        height=height,
        p=p,
        depth=depth,
        angle=angle,
        base_len=base_len,
        mode=mode,
        reps=reps,
        stroke_width=stroke_width,
        fill_mode=fill_mode,
        texture=texture,
        seed=int(seed),
    )
    process_note = (
        "Mulai dari satu persegi. Di atasnya dibangun segitiga siku-siku. "
        "Dua sisi segitiga melahirkan dua persegi baru. Proses ini diulang."
    )
    active_count_label = f"Jumlah persegi: {count}"

elif engine == "Pythagoras Cube":
    svg, count = build_pythagoras_cube_svg(
        width=width,
        height=height,
        p=p,
        depth=depth,
        angle=angle,
        base_len=base_len,
        mode=mode,
        reps=reps,
        stroke_width=stroke_width,
        texture=texture,
        seed=int(seed),
    )
    process_note = (
        "Struktur cabangnya memakai Pythagoras Tree, tetapi setiap persegi divisualkan sebagai kubus isometrik. "
        "Hasilnya tampak seperti pohon kubus, kristal, atau kota fraktal."
    )
    active_count_label = f"Jumlah kubus: {count}"

elif engine == "Dragon Curve Ornament":
    svg, count = build_dragon_svg(
        width=width,
        height=height,
        p=p,
        order=order,
        turn_angle=turn_angle,
        mode=mode,
        reps=reps,
        stroke_width=stroke_width,
        glow=glow,
        texture=texture,
        seed=int(seed),
    )
    process_note = (
        "Dragon curve lahir dari aturan belok kanan-kiri yang sederhana. "
        "Setiap iterasi menggandakan pola belokan, lalu kurva menjadi semakin kompleks."
    )
    active_count_label = f"Jumlah segmen: {count}"

else:
    svg, count = build_apollonian_svg(
        width=width,
        height=height,
        p=p,
        depth=depth,
        stroke_width=stroke_width,
        fill_mode=fill_mode,
        show_outer=show_outer,
        texture=texture,
        seed=int(seed),
    )
    process_note = (
        "Apollonian ornament mengisi ruang kosong di antara lingkaran-lingkaran yang saling bersinggungan. "
        "Setiap ruang baru diisi lagi dengan lingkaran baru, terus secara rekursif."
    )
    active_count_label = f"Jumlah lingkaran: {count}"


left, right = st.columns([1.24, 0.76])

with left:
    st.subheader("Preview")
    ph = min(820, max(450, int(height * 0.72)))
    components.html(preview_html(svg, ph), height=ph + 34, scrolling=False)

with right:
    st.subheader("Narasi Matematika")
    st.write(process_note)

    st.markdown(
        f"""
        **Parameter aktif**

        - Mesin: `{engine}`
        - Palet: `{palette_name}`
        - Kanvas: `{width} × {height}`
        - {active_count_label}
        """
    )

    if engine in ["Pythagoras Tree", "Pythagoras Cube"]:
        st.markdown(
            f"""
            **Ide jualan:**  
            Dari Teorema Pythagoras, satu persegi dapat tumbuh menjadi ornamen fraktal.

            **Parameter kunci:** sudut `{angle}°`, iterasi `{depth}`, ukuran awal `{base_len}`.
            """
        )
    elif engine == "Dragon Curve Ornament":
        st.markdown(
            f"""
            **Ide jualan:**  
            Dari aturan belok sederhana, lahir kurva naga yang kompleks.

            **Parameter kunci:** order `{order}`, sudut belok `{turn_angle}°`.
            """
        )
    else:
        st.markdown(
            f"""
            **Ide jualan:**  
            Ruang kosong diisi terus-menerus oleh lingkaran yang saling bersinggungan.

            **Parameter kunci:** kedalaman rekursi `{depth}`.
            """
        )

    st.download_button(
        "Unduh SVG",
        data=svg.encode("utf-8"),
        file_name=f"fractal_ornament_{engine.lower().replace(' ', '_')}.svg",
        mime="image/svg+xml",
        use_container_width=True,
    )

    with st.expander("Saran eksplorasi cepat", expanded=True):
        if engine == "Pythagoras Tree":
            st.markdown(
                """
                - Coba sudut `30°`, `45°`, dan `60°`.
                - Mode `Radial` bagus untuk mandala.
                - Palet `Sogan Batik` memberi rasa ornamen tekstil.
                """
            )
        elif engine == "Pythagoras Cube":
            st.markdown(
                """
                - Gunakan iterasi 6–8 agar bentuk tidak terlalu padat.
                - Mode `Radial` menghasilkan kristal/kota fraktal.
                - Palet gelap biasanya membuat efek kubus lebih kuat.
                """
            )
        elif engine == "Dragon Curve Ornament":
            st.markdown(
                """
                - Order 10–13 biasanya sudah menarik.
                - Sudut 90° adalah dragon klasik.
                - Mode `Radial` membuatnya seperti ornamen naga/keris.
                """
            )
        else:
            st.markdown(
                """
                - Depth 4–6 sudah cukup untuk komposisi rapi.
                - Isi lingkaran aktif membuatnya seperti permata/kawung modern.
                - Matikan isi untuk hasil matematis minimalis.
                """
            )


st.markdown("---")
st.markdown(
    """
    **Catatan:** app ini sengaja tidak memaksa bentuk menjadi batik literal.
    Fokusnya adalah ornamen berbasis proses matematika yang kuat, mudah dijelaskan, dan visualnya bisa dikembangkan menjadi motif dekoratif.
    """
)
