from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd


FUZZY_TERMS = ("rendah", "sedang", "tinggi")


@dataclass(frozen=True)
class FuzzySet:
    label: str
    kind: str
    points: tuple[float, ...]


def sample_smartphones() -> pd.DataFrame:
    brands = [
        "Andro",
        "Nusa",
        "Orion",
        "Sagara",
        "Pixelia",
        "Reno",
        "Nova",
        "Zen",
        "Aster",
        "Luna",
        "Poco",
        "Viva",
    ]
    segments = [
        "Entry",
        "Value",
        "Midrange",
        "Lifestyle",
        "Performance",
        "Camera",
        "Gaming",
        "Flagship",
    ]
    rows = []
    for year in range(2016, 2026):
        age = year - 2016
        for index, brand in enumerate(brands):
            segment_id = (index + age) % len(segments)
            segment = segments[segment_id]
            tier = segment_id / (len(segments) - 1)
            ram_options = [2, 3, 4, 6, 8, 12, 16]
            storage_options = [16, 32, 64, 128, 256, 512]
            ram = ram_options[min(len(ram_options) - 1, max(0, int(age * 0.55 + tier * 3.6)))]
            storage = storage_options[min(len(storage_options) - 1, max(0, int(age * 0.45 + tier * 3.2)))]
            battery = int(2800 + age * 230 + tier * 1500 + (index % 4) * 120)
            camera = int(8 + age * 4.2 + tier * 86 + (index % 3) * 6)
            screen = round(5.0 + min(1.9, age * 0.13 + tier * 0.55 + (index % 5) * 0.04), 2)
            weight = int(138 + age * 5 + tier * 38 + (index % 6) * 3)
            price = round(1.0 + age * 0.18 + tier * 13.5 + (index % 4) * 0.45, 1)
            score = round(60 + age * 1.4 + tier * 18 + (index % 5) * 1.2, 1)
            rows.append(
                {
                    "Nama Item": f"{brand} {year}-{index + 1:02d}",
                    "Rilis": year,
                    "Segmen": segment,
                    "Harga Juta": price,
                    "RAM GB": ram,
                    "Storage GB": storage,
                    "Baterai mAh": battery,
                    "Kamera Utama MP": camera,
                    "Layar Inci": screen,
                    "Berat Gram": weight,
                    "Skor Review": min(score, 98.0),
                }
            )
    return pd.DataFrame(rows)


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()


def left_shoulder(x: float, a: float, b: float) -> float:
    if x <= a:
        return 1.0
    if x >= b:
        return 0.0
    return (b - x) / (b - a)


def right_shoulder(x: float, a: float, b: float) -> float:
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a)


def triangle(x: float, a: float, b: float, c: float) -> float:
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)


def default_sets(series: pd.Series) -> dict[str, FuzzySet]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    low = float(values.min())
    high = float(values.max())
    if low == high:
        high = low + 1.0
    q1 = float(values.quantile(0.25))
    q2 = float(values.quantile(0.50))
    q3 = float(values.quantile(0.75))
    if len({low, q1, q2, q3, high}) < 5:
        q1 = low + (high - low) * 0.25
        q2 = low + (high - low) * 0.50
        q3 = low + (high - low) * 0.75
    return {
        "rendah": FuzzySet("rendah", "left", (low, q3)),
        "sedang": FuzzySet("sedang", "triangle", (q1, q2, q3)),
        "tinggi": FuzzySet("tinggi", "right", (q1, high)),
    }


def membership_value(value: float, fuzzy_set: FuzzySet) -> float:
    if pd.isna(value):
        return 0.0
    if fuzzy_set.kind == "left":
        result = left_shoulder(float(value), *fuzzy_set.points)
    elif fuzzy_set.kind == "right":
        result = right_shoulder(float(value), *fuzzy_set.points)
    elif fuzzy_set.kind == "triangle":
        result = triangle(float(value), *fuzzy_set.points)
    else:
        raise ValueError(f"Jenis himpunan fuzzy tidak dikenal: {fuzzy_set.kind}")
    return round(float(np.clip(result, 0.0, 1.0)), 4)


def fuzzify_dataframe(
    df: pd.DataFrame, selected_columns: list[str], fuzzy_sets: dict[str, dict[str, FuzzySet]]
) -> pd.DataFrame:
    rows = []
    for index, row in df.iterrows():
        out = {"index": index}
        name_col = first_text_column(df)
        if name_col:
            out[name_col] = row[name_col]
        for column in selected_columns:
            for term in FUZZY_TERMS:
                out[f"{column}.{term}"] = membership_value(row[column], fuzzy_sets[column][term])
        rows.append(out)
    return pd.DataFrame(rows)


def first_text_column(df: pd.DataFrame) -> str | None:
    text_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    if "Nama HP" in df.columns:
        return "Nama HP"
    return text_cols[0] if text_cols else None


def condition_token(column: str, term: str) -> str:
    return f"{safe_identifier(column)}__{term}"


def safe_identifier(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned or "kolom"


def build_condition_frame(
    df: pd.DataFrame, selected_columns: list[str], fuzzy_sets: dict[str, dict[str, FuzzySet]]
) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    for column in selected_columns:
        for term in FUZZY_TERMS:
            result[condition_token(column, term)] = df[column].apply(
                lambda value, fs=fuzzy_sets[column][term]: membership_value(value, fs)
            )
    return result


class QueryEvaluator(ast.NodeVisitor):
    """Evaluator aman untuk ekspresi Tahani: AND=min, OR=max, NOT=1-mu."""

    allowed_binary: dict[type, Callable[[float, float], float]] = {
        ast.BitAnd: min,
        ast.BitOr: max,
    }
    allowed_unary: dict[type, Callable[[float], float]] = {
        ast.Invert: lambda x: 1.0 - x,
        ast.USub: operator.neg,
    }

    def __init__(self, values: dict[str, float]):
        self.values = values

    def visit_Name(self, node: ast.Name) -> float:
        if node.id not in self.values:
            raise ValueError(f"Token query tidak dikenal: {node.id}")
        return float(self.values[node.id])

    def visit_Constant(self, node: ast.Constant) -> float:
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Query hanya menerima token kondisi dan angka.")

    def visit_BinOp(self, node: ast.BinOp) -> float:
        op_type = type(node.op)
        if op_type not in self.allowed_binary:
            raise ValueError("Operator yang didukung hanya AND dan OR.")
        return self.allowed_binary[op_type](self.visit(node.left), self.visit(node.right))

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        op_type = type(node.op)
        if op_type not in self.allowed_unary:
            raise ValueError("Operator unary yang didukung hanya NOT.")
        return self.allowed_unary[op_type](self.visit(node.operand))

    def visit_Expression(self, node: ast.Expression) -> float:
        return self.visit(node.body)

    def generic_visit(self, node: ast.AST) -> float:
        raise ValueError(f"Bagian query tidak didukung: {type(node).__name__}")


def normalize_query(query: str, token_lookup: dict[str, str]) -> str:
    expr = query
    for label, token in sorted(token_lookup.items(), key=lambda item: len(item[0]), reverse=True):
        expr = expr.replace(label, token)
    expr = re.sub(r"\bAND\b", "&", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bOR\b", "|", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bNOT\b", "~", expr, flags=re.IGNORECASE)
    return expr.strip()


def evaluate_query(condition_df: pd.DataFrame, expression: str) -> pd.Series:
    parsed = ast.parse(expression, mode="eval")
    scores = []
    for _, row in condition_df.iterrows():
        evaluator = QueryEvaluator(row.to_dict())
        scores.append(round(float(np.clip(evaluator.visit(parsed), 0.0, 1.0)), 4))
    return pd.Series(scores, index=condition_df.index, name="Derajat Cocok")


def rank_results(df: pd.DataFrame, scores: pd.Series) -> pd.DataFrame:
    result = df.copy()
    result["Derajat Cocok"] = scores
    result["Ranking"] = result["Derajat Cocok"].rank(method="min", ascending=False).astype(int)
    return result.sort_values(["Derajat Cocok", "Ranking"], ascending=[False, True]).reset_index(drop=True)
