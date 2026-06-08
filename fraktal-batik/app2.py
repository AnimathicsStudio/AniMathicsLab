
import math

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="Batik Grammar Studio",
    page_icon="◆",
    layout="wide",
)


PALETTES = {
    "Sogan Klasik": {
        "bg": "#F4E3BF",
        "ink": "#2B1608",
        "brown": "#8B4A1E",
        "gold": "#C58A3A",
        "soft": "#E7C98C",
        "light": "#FFF3D0",
    },
    "Keraton Gelap": {
        "bg": "#17120C",
        "ink": "#F6D985",
        "brown": "#6F3E18",
        "gold": "#C99A3E",
        "soft": "#3A2A16",
        "light": "#FFF0B7",
    },
    "Biru Mega Mendung": {
        "bg": "#DDEAF2",
        "ink": "#102A43",
        "brown": "#2F6F9F",
        "gold": "#66A6C9",
        "soft": "#B7D7E8",
        "light": "#F4FBFF",
    },
    "Merah Bata": {
        "bg": "#F1D5B8",
        "ink": "#3A120A",
        "brown": "#9D2F17",
        "gold": "#D46A3A",
        "soft": "#E8AA7A",
        "light": "#FFE8CE",
    },
    "Indigo Malam": {
        "bg": "#101724",
        "ink": "#D7E7FF",
        "brown": "#3F6EA8",
        "gold": "#8FB7E8",
        "soft": "#1E314D",
        "light": "#EEF6FF",
    },
}


def svg_header(width, height, bg):
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img">
<rect x="0" y="0" width="{width}" height="{height}" fill="{bg}"/>
"""


def svg_footer():
    return "</svg>"


def circle(cx, cy, r, fill, stroke="none", sw=1, opacity=1):
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}" opacity="{opacity:.3f}"/>'


def ellipse(cx, cy, rx, ry, fill, stroke, sw=1, rot=0, opacity=1):
    return (
        f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
        f'transform="rotate({rot:.2f} {cx:.2f} {cy:.2f})" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}" opacity="{opacity:.3f}"/>'
    )


def line(x1, y1, x2, y2, stroke, sw=1, opacity=1):
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{sw:.2f}" opacity="{opacity:.3f}" stroke-linecap="round"/>'
    )


def path(d, fill="none", stroke="#000000", sw=1, opacity=1):
    return (
        f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}" '
        f'opacity="{opacity:.3f}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def polygon(points, fill, stroke, sw=1, opacity=1):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return (
        f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw:.2f}" opacity="{opacity:.3f}" stroke-linejoin="round"/>'
    )


def rect(x, y, w, h, fill="none", stroke="#000", sw=1, opacity=1):
    return (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}" opacity="{opacity:.3f}"/>'
    )


def diamond(cx, cy, rx, ry):
    return [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]


def star_points(cx, cy, r1, r2, n=8, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.radians(rot + 180 * i / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def clip_defs(width, height, margin):
    return f"""
<defs>
  <clipPath id="innerClip">
    <rect x="{margin}" y="{margin}" width="{width-2*margin}" height="{height-2*margin}"/>
  </clipPath>
</defs>
"""


def dot_ring(cx, cy, r, count, dot_r, color, phase=0, opacity=0.75):
    out = []
    for i in range(count):
        a = 2 * math.pi * i / count + phase
        out.append(circle(cx + r * math.cos(a), cy + r * math.sin(a), dot_r, color, opacity=opacity))
    return "\n".join(out)


def nitik_field(width, height, margin, spacing, color, opacity=0.35, r=1.3, stagger=True):
    out = ['<g clip-path="url(#innerClip)">']
    row = 0
    y = margin + spacing * 0.5
    while y < height - margin:
        x0 = margin + spacing * 0.5 + (spacing * 0.5 if stagger and row % 2 else 0)
        x = x0
        col = 0
        while x < width - margin:
            rr = r * (1.45 if (row + col) % 7 == 0 else 1.0)
            out.append(circle(x, y, rr, color, opacity=opacity))
            x += spacing
            col += 1
        y += spacing
        row += 1
    out.append("</g>")
    return "\n".join(out)


def simple_frame(width, height, margin, p, sw):
    out = []
    out.append(rect(margin, margin, width - 2*margin, height - 2*margin, fill="none", stroke=p["ink"], sw=sw, opacity=0.9))
    out.append(rect(margin*1.55, margin*1.55, width - 3.1*margin, height - 3.1*margin, fill="none", stroke=p["brown"], sw=sw*0.65, opacity=0.75))
    return "\n".join(out)


def kawung_tile(cx, cy, s, p, sw, fill_mode=True, detail=1.0):
    out = []
    fill = p["soft"] if fill_mode else "none"
    out.append(ellipse(cx - 0.18*s, cy, 0.24*s, 0.105*s, fill, p["ink"], sw, rot=0, opacity=0.95))
    out.append(ellipse(cx + 0.18*s, cy, 0.24*s, 0.105*s, fill, p["ink"], sw, rot=0, opacity=0.95))
    out.append(ellipse(cx, cy - 0.18*s, 0.24*s, 0.105*s, fill, p["ink"], sw, rot=90, opacity=0.95))
    out.append(ellipse(cx, cy + 0.18*s, 0.24*s, 0.105*s, fill, p["ink"], sw, rot=90, opacity=0.95))
    out.append(polygon(diamond(cx, cy, 0.42*s, 0.42*s), fill="none", stroke=p["brown"], sw=sw*0.7, opacity=0.35))
    out.append(polygon(diamond(cx, cy, 0.075*s, 0.075*s), fill=p["gold"], stroke=p["ink"], sw=sw*0.7, opacity=0.95))
    out.append(circle(cx, cy, 0.026*s, p["ink"], opacity=0.95))
    if detail > 0:
        out.append(dot_ring(cx, cy, 0.315*s, 12, max(1.0, 0.012*s*detail), p["brown"], opacity=0.55))
        for sx in [-1, 1]:
            for sy in [-1, 1]:
                out.append(circle(cx + sx*0.35*s, cy + sy*0.35*s, max(1.1, 0.018*s*detail), p["ink"], opacity=0.55))
    return "\n".join(out)


def pattern_kawung(width, height, p, tile, margin, sw, fill_mode, detail):
    out = [clip_defs(width, height, margin), '<g clip-path="url(#innerClip)">']
    y = margin + tile * 0.5
    row = 0
    while y < height - margin:
        x = margin + tile * 0.5 + (tile*0.5 if row % 2 else 0)
        while x < width - margin:
            out.append(kawung_tile(x, y, tile, p, sw, fill_mode, detail))
            x += tile
        y += tile
        row += 1
    out.append("</g>")
    return "\n".join(out)


def truntum_tile(cx, cy, s, p, sw, fill_mode=True, detail=1.0):
    out = []
    fill = p["gold"] if fill_mode else "none"
    out.append(polygon(star_points(cx, cy, 0.14*s, 0.052*s, n=8), fill=fill, stroke=p["ink"], sw=sw, opacity=0.95))
    out.append(circle(cx, cy, 0.018*s, p["ink"], opacity=0.9))
    if detail > 0:
        out.append(dot_ring(cx, cy, 0.23*s, 8, max(0.8, 0.010*s*detail), p["brown"], phase=math.pi/8, opacity=0.55))
    return "\n".join(out)


def pattern_truntum(width, height, p, tile, margin, sw, fill_mode, detail):
    out = [clip_defs(width, height, margin), '<g clip-path="url(#innerClip)">']
    spacing = tile * 0.52
    y = margin + spacing
    row = 0
    while y < height - margin:
        x = margin + spacing + (spacing*0.5 if row % 2 else 0)
        while x < width - margin:
            out.append(truntum_tile(x, y, tile, p, sw, fill_mode, detail))
            x += spacing
        y += spacing
        row += 1
    out.append("</g>")
    return "\n".join(out)


def ceplok_tile(cx, cy, s, p, sw, fill_mode=True, detail=1.0):
    out = []
    fill = p["soft"] if fill_mode else "none"
    petals = 8
    for i in range(petals):
        a = 2 * math.pi * i / petals
        x = cx + 0.18*s * math.cos(a)
        y = cy + 0.18*s * math.sin(a)
        out.append(ellipse(x, y, 0.20*s, 0.065*s, fill, p["ink"], sw, rot=math.degrees(a), opacity=0.9))
    out.append(circle(cx, cy, 0.09*s, p["gold"], stroke=p["ink"], sw=sw, opacity=0.95))
    out.append(polygon(diamond(cx, cy, 0.42*s, 0.42*s), fill="none", stroke=p["brown"], sw=sw*0.7, opacity=0.6))
    if detail > 0:
        out.append(dot_ring(cx, cy, 0.31*s, 16, max(0.9, 0.009*s*detail), p["brown"], opacity=0.55))
        out.append(dot_ring(cx, cy, 0.17*s, 8, max(0.8, 0.008*s*detail), p["ink"], opacity=0.45))
    return "\n".join(out)


def pattern_ceplok(width, height, p, tile, margin, sw, fill_mode, detail):
    out = [clip_defs(width, height, margin), '<g clip-path="url(#innerClip)">']
    y = margin + tile * 0.5
    while y < height - margin:
        x = margin + tile * 0.5
        while x < width - margin:
            out.append(ceplok_tile(x, y, tile, p, sw, fill_mode, detail))
            x += tile
        y += tile
    out.append("</g>")
    return "\n".join(out)


def parang_element(cx, cy, s, p, sw, fill_mode=True, detail=1.0):
    out = []
    fill = p["soft"] if fill_mode else "none"
    d = (
        f"M {cx-0.38*s:.2f} {cy+0.22*s:.2f} "
        f"C {cx-0.18*s:.2f} {cy-0.12*s:.2f}, {cx+0.12*s:.2f} {cy-0.28*s:.2f}, {cx+0.36*s:.2f} {cy-0.10*s:.2f} "
        f"C {cx+0.12*s:.2f} {cy+0.04*s:.2f}, {cx-0.12*s:.2f} {cy+0.20*s:.2f}, {cx-0.28*s:.2f} {cy+0.42*s:.2f} "
        f"C {cx-0.38*s:.2f} {cy+0.34*s:.2f}, {cx-0.42*s:.2f} {cy+0.28*s:.2f}, {cx-0.38*s:.2f} {cy+0.22*s:.2f} Z"
    )
    out.append(path(d, fill=fill, stroke=p["ink"], sw=sw, opacity=0.95))
    d2 = (
        f"M {cx-0.18*s:.2f} {cy+0.16*s:.2f} "
        f"C {cx+0.02*s:.2f} {cy-0.04*s:.2f}, {cx+0.16*s:.2f} {cy-0.14*s:.2f}, {cx+0.30*s:.2f} {cy-0.08*s:.2f}"
    )
    out.append(path(d2, fill="none", stroke=p["brown"], sw=sw*0.65, opacity=0.75))
    out.append(polygon(diamond(cx-0.28*s, cy+0.30*s, 0.07*s, 0.07*s), fill=p["gold"], stroke=p["ink"], sw=sw*0.55, opacity=0.9))
    if detail > 0:
        for i in range(4):
            out.append(circle(cx - 0.05*s + i*0.07*s, cy + 0.06*s - i*0.04*s, max(1.0, 0.012*s*detail), p["brown"], opacity=0.6))
    return "\n".join(out)


def pattern_parang(width, height, p, tile, margin, sw, fill_mode, detail):
    out = [clip_defs(width, height, margin), '<g clip-path="url(#innerClip)">']
    band = tile * 0.78
    offset = -height
    while offset < width + height:
        out.append(line(-height, -height + offset, width + height, width + height + offset, p["brown"], sw=sw*0.5, opacity=0.22))
        offset += band
    offset = -height
    while offset < width + height:
        t = -height
        while t < width + height:
            cx = t
            cy = t + offset
            if margin - tile < cx < width - margin + tile and margin - tile < cy < height - margin + tile:
                out.append(f'<g transform="rotate(-45 {cx:.2f} {cy:.2f})">')
                out.append(parang_element(cx, cy, tile, p, sw, fill_mode, detail))
                out.append("</g>")
            t += tile * 0.88
        offset += band
    out.append("</g>")
    return "\n".join(out)


def cloud_layer(cx, cy, s, p, sw, fill, scale=1.0, opacity=1.0):
    ss = s * scale
    d = (
        f"M {cx-0.48*ss:.2f} {cy+0.06*ss:.2f} "
        f"C {cx-0.42*ss:.2f} {cy-0.18*ss:.2f}, {cx-0.22*ss:.2f} {cy-0.26*ss:.2f}, {cx-0.06*ss:.2f} {cy-0.15*ss:.2f} "
        f"C {cx+0.03*ss:.2f} {cy-0.35*ss:.2f}, {cx+0.30*ss:.2f} {cy-0.34*ss:.2f}, {cx+0.38*ss:.2f} {cy-0.12*ss:.2f} "
        f"C {cx+0.58*ss:.2f} {cy-0.11*ss:.2f}, {cx+0.65*ss:.2f} {cy+0.14*ss:.2f}, {cx+0.45*ss:.2f} {cy+0.24*ss:.2f} "
        f"L {cx-0.42*ss:.2f} {cy+0.24*ss:.2f} "
        f"C {cx-0.54*ss:.2f} {cy+0.22*ss:.2f}, {cx-0.56*ss:.2f} {cy+0.11*ss:.2f}, {cx-0.48*ss:.2f} {cy+0.06*ss:.2f} Z"
    )
    return path(d, fill=fill, stroke=p["ink"], sw=sw, opacity=opacity)


def mega_mendung_tile(cx, cy, s, p, sw, fill_mode=True, detail=1.0):
    out = []
    fills = [p["light"], p["soft"], p["gold"], p["brown"]]
    scales = [1.00, 0.78, 0.57, 0.37]
    for i, sc in enumerate(scales):
        fill = fills[i] if fill_mode else "none"
        out.append(cloud_layer(cx, cy + i*0.035*s, s, p, sw*(1 if i == 0 else 0.72), fill, scale=sc, opacity=0.93))
    if detail > 0:
        for i in range(5):
            out.append(circle(cx - 0.28*s + i*0.14*s, cy + 0.29*s, max(1.1, 0.012*s*detail), p["ink"], opacity=0.45))
    return "\n".join(out)


def pattern_mega(width, height, p, tile, margin, sw, fill_mode, detail):
    out = [clip_defs(width, height, margin), '<g clip-path="url(#innerClip)">']
    y = margin + tile * 0.52
    row = 0
    while y < height - margin + tile:
        x = margin + tile * 0.55 + (tile*0.55 if row % 2 else 0)
        while x < width - margin + tile:
            out.append(mega_mendung_tile(x, y, tile, p, sw, fill_mode, detail))
            x += tile * 1.15
        y += tile * 0.72
        row += 1
    out.append("</g>")
    return "\n".join(out)


def pattern_tumpal(width, height, p, tile, margin, sw, fill_mode, detail):
    out = [clip_defs(width, height, margin)]
    step = tile * 0.58
    m = max(margin, 28)
    fill_a = p["soft"] if fill_mode else "none"
    x = m
    idx = 0
    while x < width - m:
        fill = fill_a if idx % 2 == 0 else p["light"]
        out.append(polygon([(x, m), (x+step/2, m+step*0.82), (x+step, m)], fill, p["ink"], sw, opacity=0.92))
        out.append(polygon([(x, height-m), (x+step/2, height-m-step*0.82), (x+step, height-m)], fill, p["ink"], sw, opacity=0.92))
        out.append(circle(x+step/2, m+step*0.34, max(1.2, step*0.035), p["brown"], opacity=0.65))
        out.append(circle(x+step/2, height-m-step*0.34, max(1.2, step*0.035), p["brown"], opacity=0.65))
        x += step
        idx += 1
    out.append('<g clip-path="url(#innerClip)">')
    inner = m + step
    y = inner + tile*0.35
    while y < height - inner:
        x = inner + tile*0.35
        while x < width - inner:
            out.append(ceplok_tile(x, y, tile*0.65, p, sw*0.75, fill_mode, detail*0.8))
            x += tile * 0.82
        y += tile * 0.82
    out.append("</g>")
    return "\n".join(out)


def pattern_kain_komplit(width, height, p, tile, margin, sw, fill_mode, detail):
    out = []
    out.append(clip_defs(width, height, margin))
    out.append(nitik_field(width, height, margin, max(10, tile*0.17), p["brown"], opacity=0.22, r=max(0.8, tile*0.010)))
    out.append(pattern_parang(width, height, p, tile*0.95, margin, sw*0.85, fill_mode, detail*0.85))
    out.append(simple_frame(width, height, max(18, margin), p, sw))
    return "\n".join(out)


BUILDERS = {
    "Kawung Klasik": pattern_kawung,
    "Parang / Lereng": pattern_parang,
    "Mega Mendung": pattern_mega,
    "Truntum": pattern_truntum,
    "Ceplok": pattern_ceplok,
    "Tumpal Border": pattern_tumpal,
    "Kain Komplit: Parang + Nitik": pattern_kain_komplit,
}


NOTES = {
    "Kawung Klasik": "Motif kawung terasa dari empat elips berulang, pusat belah ketupat, dan titik-titik isen.",
    "Parang / Lereng": "Motif lereng/parang dibangun dari pita diagonal dan elemen S sederhana.",
    "Mega Mendung": "Mega mendung dibuat dari lapisan kurva awan bertingkat, bukan dari noise atau simulasi biologis.",
    "Truntum": "Truntum memakai bintang kecil berulang dengan titik isen di sekelilingnya.",
    "Ceplok": "Ceplok memakai roset/geometri radial dalam grid.",
    "Tumpal Border": "Tumpal menekankan ornamen pinggir berupa segitiga, lalu bagian tengah diisi ceplok kecil.",
    "Kain Komplit: Parang + Nitik": "Komposisi kain: motif utama parang/lereng dengan latar nitik dan frame sederhana.",
}


def build_svg(width, height, palette, motif, tile, margin, sw, fill_mode, detail, add_nitik, add_frame):
    p = PALETTES[palette]
    parts = [svg_header(width, height, p["bg"])]
    if add_nitik and motif != "Kain Komplit: Parang + Nitik":
        parts.append(clip_defs(width, height, margin))
        parts.append(nitik_field(width, height, margin, max(9, tile*0.16), p["brown"], opacity=0.18, r=max(0.7, tile*0.009)))
    parts.append(BUILDERS[motif](width, height, p, tile, margin, sw, fill_mode, detail))
    if add_frame:
        parts.append(simple_frame(width, height, max(15, margin), p, sw))
    parts.append(svg_footer())
    return "\n".join(parts)


def preview_html(svg, h):
    return f"""
    <div style="
        width:100%;
        height:{h}px;
        overflow:auto;
        border:1px solid rgba(120,120,120,.25);
        border-radius:16px;
        padding:10px;
        background:#fafafa;
        box-sizing:border-box;">
      {svg}
    </div>
    """


st.title("Batik Grammar Studio")
st.caption("Motif dibuat dari tata bahasa visual batik: kawung, parang, mega mendung, truntum, ceplok, tumpal, dan nitik.")

with st.sidebar:
    st.header("Motif")
    motif = st.selectbox("Pilih motif", list(BUILDERS.keys()), index=0)
    st.info(NOTES[motif])
    palette = st.selectbox("Palet", list(PALETTES.keys()), index=0)

    st.header("Kanvas")
    width = st.slider("Lebar", 600, 1800, 1100, 50)
    height = st.slider("Tinggi", 400, 1400, 760, 40)

    st.header("Struktur")
    tile = st.slider("Ukuran modul motif", 50, 240, 125, 5)
    margin = st.slider("Margin", 0, 120, 26, 2)
    sw = st.slider("Ketebalan garis", 0.5, 5.0, 1.7, 0.1)
    detail = st.slider("Kepadatan detail/isen", 0.0, 2.0, 1.0, 0.1)

    fill_mode = st.toggle("Isi bidang motif", value=True)
    add_nitik = st.toggle("Tambahkan latar nitik halus", value=False)
    add_frame = st.toggle("Tambahkan frame", value=False)


svg = build_svg(width, height, palette, motif, tile, margin, sw, fill_mode, detail, add_nitik, add_frame)

left, right = st.columns([1.22, 0.78])

with left:
    st.subheader("Preview")
    ph = min(760, max(430, int(height * 0.72)))
    components.html(preview_html(svg, ph), height=ph+30, scrolling=False)

with right:
    st.subheader("Catatan")
    st.write(NOTES[motif])
    st.markdown(
        f"""
        **Parameter aktif**

        - Motif: `{motif}`
        - Palet: `{palette}`
        - Kanvas: `{width} × {height}`
        - Modul motif: `{tile}`
        - Detail/isen: `{detail}`
        """
    )

    st.download_button(
        "Unduh SVG",
        data=svg.encode("utf-8"),
        file_name=f"batik_grammar_{motif.lower().replace(' ', '_').replace('/', '-')}.svg",
        mime="image/svg+xml",
        use_container_width=True,
    )

    with st.expander("Kenapa ini lebih batik daripada reaction-diffusion?", expanded=True):
        st.write(
            """
            Karena motifnya tidak dibiarkan muncul dari simulasi acak.
            App ini mulai dari keluarga motif yang memang dikenal dalam bahasa visual batik:
            kawung, parang/lereng, mega mendung, truntum, ceplok, tumpal, dan nitik.
            Parameter hanya mengatur repetisi, ukuran, kepadatan isen, dan komposisi.
            """
        )


st.markdown("---")
st.markdown(
    """
    **Arah berikutnya:** tambah variasi khusus untuk setiap motif, misalnya bentuk parang lebih halus,
    mega mendung lebih bertingkat, kawung isi kawung kecil, dan mode seamless tile.
    """
)
