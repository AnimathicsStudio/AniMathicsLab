from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FuzzySet:
    label: str
    shape: str
    points: tuple[float, ...]
    color: str


@dataclass(frozen=True)
class VariablePreset:
    name: str
    unit: str
    domain: tuple[float, float]
    crisp: float
    sets: list[FuzzySet]


COLORS = {
    "rendah": "#16a34a",
    "sedang": "#2563eb",
    "tinggi": "#dc2626",
    "dingin": "#0891b2",
    "normal": "#2563eb",
    "panas": "#dc2626",
    "murah": "#16a34a",
    "mahal": "#dc2626",
    "dekat": "#16a34a",
    "jauh": "#dc2626",
    "kering": "#ca8a04",
    "lembap": "#2563eb",
    "basah": "#16a34a",
}


PRESETS = {
    "Suhu ruangan": VariablePreset(
        name="Suhu ruangan",
        unit="C",
        domain=(0.0, 45.0),
        crisp=28.0,
        sets=[
            FuzzySet("dingin", "Bahu kiri", (12.0, 22.0), COLORS["dingin"]),
            FuzzySet("normal", "Segitiga", (18.0, 27.0, 34.0), COLORS["normal"]),
            FuzzySet("panas", "Bahu kanan", (30.0, 40.0), COLORS["panas"]),
        ],
    ),
    "Harga produk": VariablePreset(
        name="Harga produk",
        unit="ribu",
        domain=(0.0, 1000.0),
        crisp=420.0,
        sets=[
            FuzzySet("murah", "Bahu kiri", (180.0, 420.0), COLORS["murah"]),
            FuzzySet("sedang", "Trapesium", (260.0, 420.0, 620.0, 780.0), COLORS["sedang"]),
            FuzzySet("mahal", "Bahu kanan", (650.0, 900.0), COLORS["mahal"]),
        ],
    ),
    "Jarak kampus": VariablePreset(
        name="Jarak kampus",
        unit="km",
        domain=(0.0, 30.0),
        crisp=9.0,
        sets=[
            FuzzySet("dekat", "Bahu kiri", (3.0, 9.0), COLORS["dekat"]),
            FuzzySet("sedang", "Segitiga", (6.0, 14.0, 22.0), COLORS["sedang"]),
            FuzzySet("jauh", "Bahu kanan", (18.0, 28.0), COLORS["jauh"]),
        ],
    ),
    "Kelembapan tanah": VariablePreset(
        name="Kelembapan tanah",
        unit="%",
        domain=(0.0, 100.0),
        crisp=54.0,
        sets=[
            FuzzySet("kering", "Bahu kiri", (25.0, 45.0), COLORS["kering"]),
            FuzzySet("lembap", "Trapesium", (35.0, 48.0, 68.0, 82.0), COLORS["lembap"]),
            FuzzySet("basah", "Bahu kanan", (72.0, 92.0), COLORS["basah"]),
        ],
    ),
}


SHAPE_POINT_COUNT = {
    "Segitiga": 3,
    "Trapesium": 4,
    "Bahu kiri": 2,
    "Bahu kanan": 2,
}


def triangular(x: float, a: float, b: float, c: float) -> float:
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a) if b != a else 0.0
    return (c - x) / (c - b) if c != b else 0.0


def trapezoid(x: float, a: float, b: float, c: float, d: float) -> float:
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a) if b != a else 0.0
    return (d - x) / (d - c) if d != c else 0.0


def left_shoulder(x: float, a: float, b: float) -> float:
    if x <= a:
        return 1.0
    if x >= b:
        return 0.0
    return (b - x) / (b - a) if b != a else 0.0


def right_shoulder(x: float, a: float, b: float) -> float:
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a) if b != a else 0.0


def membership_value(x: float, fuzzy_set: FuzzySet) -> float:
    points = tuple(sorted(float(point) for point in fuzzy_set.points))
    if fuzzy_set.shape == "Segitiga":
        return triangular(x, points[0], points[1], points[2])
    if fuzzy_set.shape == "Trapesium":
        return trapezoid(x, points[0], points[1], points[2], points[3])
    if fuzzy_set.shape == "Bahu kiri":
        return left_shoulder(x, points[0], points[1])
    if fuzzy_set.shape == "Bahu kanan":
        return right_shoulder(x, points[0], points[1])
    return 0.0


def validate_set(fuzzy_set: FuzzySet, domain: tuple[float, float]) -> str | None:
    expected = SHAPE_POINT_COUNT[fuzzy_set.shape]
    if len(fuzzy_set.points) != expected:
        return f"{fuzzy_set.label}: bentuk {fuzzy_set.shape} membutuhkan {expected} titik."
    points = tuple(float(point) for point in fuzzy_set.points)
    if any(point < domain[0] or point > domain[1] for point in points):
        return f"{fuzzy_set.label}: semua titik harus berada di dalam domain."
    if list(points) != sorted(points):
        return f"{fuzzy_set.label}: titik harus urut dari kecil ke besar."
    if len(set(points)) != len(points):
        return f"{fuzzy_set.label}: titik tidak boleh sama."
    return None


def plot_rows(domain: tuple[float, float], sets: list[FuzzySet], samples: int = 601) -> pd.DataFrame:
    grid = set(np.linspace(domain[0], domain[1], samples))
    for fuzzy_set in sets:
        grid.update(fuzzy_set.points)
    rows = []
    for x in sorted(grid):
        for fuzzy_set in sets:
            rows.append(
                {
                    "Nilai": float(x),
                    "Derajat": round(membership_value(float(x), fuzzy_set), 6),
                    "Himpunan": fuzzy_set.label,
                    "Warna": fuzzy_set.color,
                }
            )
    return pd.DataFrame(rows)


def degree_table(crisp: float, sets: list[FuzzySet]) -> pd.DataFrame:
    rows = []
    for fuzzy_set in sets:
        degree = membership_value(crisp, fuzzy_set)
        rows.append(
            {
                "Himpunan fuzzy": fuzzy_set.label,
                "Bentuk": fuzzy_set.shape,
                "Titik": " - ".join(f"{point:g}" for point in fuzzy_set.points),
                "Derajat keanggotaan": round(degree, 4),
            }
        )
    return pd.DataFrame(rows).sort_values("Derajat keanggotaan", ascending=False).reset_index(drop=True)


def alpha_cut_for_set(fuzzy_set: FuzzySet, alpha: float, domain: tuple[float, float]) -> str:
    points = tuple(sorted(float(point) for point in fuzzy_set.points))
    alpha = float(np.clip(alpha, 0.0, 1.0))
    if fuzzy_set.shape == "Bahu kiri":
        if alpha == 0:
            return f"{domain[0]:g} sampai {domain[1]:g}"
        right = points[1] - alpha * (points[1] - points[0])
        return f"{domain[0]:g} sampai {right:g}"
    if fuzzy_set.shape == "Bahu kanan":
        if alpha == 0:
            return f"{domain[0]:g} sampai {domain[1]:g}"
        left = points[0] + alpha * (points[1] - points[0])
        return f"{left:g} sampai {domain[1]:g}"
    if fuzzy_set.shape == "Segitiga":
        if alpha == 0:
            return f"{points[0]:g} sampai {points[2]:g}"
        left = points[0] + alpha * (points[1] - points[0])
        right = points[2] - alpha * (points[2] - points[1])
        return f"{left:g} sampai {right:g}"
    if fuzzy_set.shape == "Trapesium":
        if alpha == 0:
            return f"{points[0]:g} sampai {points[3]:g}"
        left = points[0] + alpha * (points[1] - points[0])
        right = points[3] - alpha * (points[3] - points[2])
        return f"{left:g} sampai {right:g}"
    return "-"


def alpha_cut_intervals(sets: list[FuzzySet], alpha: float, domain: tuple[float, float]) -> pd.DataFrame:
    rows = []
    for fuzzy_set in sets:
        rows.append({"Himpunan fuzzy": fuzzy_set.label, "Alpha-cut": alpha_cut_for_set(fuzzy_set, alpha, domain)})
    return pd.DataFrame(rows)


def format_number_id(value: object) -> str:
    if pd.isna(value) or not isinstance(value, (int, float, np.integer, np.floating)):
        return ""
    value_float = float(value)
    if abs(value_float) >= 1000:
        if value_float.is_integer():
            return f"{int(value_float):,}".replace(",", ".")
        whole, decimal = f"{value_float:,.2f}".split(".")
        return f"{whole.replace(',', '.')},{decimal}"
    return f"{value_float:g}"


def display_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    formatters = {column: format_number_id for column in df.select_dtypes(include="number").columns}
    return df.style.format(formatters)
