import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.title("❄️ Koch Snowflake dengan Zoom Interaktif (Plotly)")

# --- Fraktal koch_hexagon sama seperti sebelumnya ---
def rotate(p, angle_rad):
    rot = np.array([
        [np.cos(angle_rad), -np.sin(angle_rad)],
        [np.sin(angle_rad),  np.cos(angle_rad)]
    ])
    return rot @ p

def koch_curve(p1, p2, level):
    if level == 0:
        return [p1, p2]
    else:
        p1 = np.array(p1)
        p2 = np.array(p2)
        delta = p2 - p1
        a = p1 + delta / 3
        b = p1 + 2 * delta / 3
        peak = a + rotate(b - a, np.pi / 3)
        return (
            koch_curve(p1, a, level - 1)[:-1] +
            koch_curve(a, peak, level - 1)[:-1] +
            koch_curve(peak, b, level - 1)[:-1] +
            koch_curve(b, p2, level - 1)
        )

def koch_hexagon(level):
    n_sides = 6
    radius = 1.0
    points = []

    for i in range(n_sides):
        angle1 = 2 * np.pi * i / n_sides
        angle2 = 2 * np.pi * (i + 1) / n_sides
        p1 = [radius * np.cos(angle1), radius * np.sin(angle1)]
        p2 = [radius * np.cos(angle2), radius * np.sin(angle2)]
        curve = koch_curve(p1, p2, level)
        points.extend(curve[:-1])
    points.append(points[0])
    return np.array(points)

# UI
level = st.slider("Level iterasi (0–4)", 0, 4, 1)

# Data fraktal
points = koch_hexagon(level)

# Plot pakai Plotly
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=points[:, 0],
    y=points[:, 1],
    mode="lines",
    line=dict(color="deepskyblue"),
    name=f"Koch Level {level}"
	hoverinfo='skip',
    hovertemplate=None
))
fig.update_layout(
    width=600,
    height=600,
    showlegend=False,
    margin=dict(l=0, r=0, t=30, b=0),
    title=f"Koch Snowflake Level {level}",
    xaxis=dict(scaleanchor="y", visible=False),
    yaxis=dict(visible=False)
)

# Tampilkan di Streamlit

fig.update_layout(
    dragmode='pan',
    xaxis=dict(scaleanchor="y", visible=False),
    yaxis=dict(visible=False),
    width=600, height=600,
    margin=dict(l=0, r=0, t=30, b=0),
)

config = {
    "scrollZoom": True,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d",
        "zoomIn2d", "zoomOut2d", "autoScale2d", 
        "toImage", "sendDataToCloud", "hoverClosestCartesian",
        "hoverCompareCartesian"
    ],
    "displaylogo": False  # ⬅️ Hilangkan logo Plotly
}


st.plotly_chart(fig, use_container_width=True, config=config)
