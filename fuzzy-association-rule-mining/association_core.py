from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd


TERMS = ("rendah", "sedang", "tinggi")


def sample_transaction_data() -> pd.DataFrame:
    rng = np.random.default_rng(91)
    profiles = [
        ("hemat", 2.0, 45000, 1.0, 0.2, 0.35, 0.25),
        ("rutin", 4.0, 95000, 2.0, 0.45, 0.55, 0.45),
        ("loyal", 7.0, 170000, 3.5, 0.7, 0.75, 0.65),
        ("premium", 10.0, 285000, 5.0, 0.85, 0.9, 0.78),
    ]
    rows = []
    categories = ["sembako", "minuman", "snack", "perawatan", "elektronik kecil"]
    for profile, freq, spend, items, promo, member, response in profiles:
        for idx in range(45):
            rows.append(
                {
                    "id_transaksi": f"{profile[:3].upper()}-{idx + 1:03d}",
                    "segmen": profile,
                    "kategori": categories[(idx + len(profile)) % len(categories)],
                    "frekuensi_belanja": round(max(1, rng.normal(freq, 1.1)), 2),
                    "nilai_belanja": round(max(12000, rng.normal(spend, spend * 0.18)), 0),
                    "jumlah_item": round(max(1, rng.normal(items, 1.1)), 2),
                    "diskon_persen": round(float(np.clip(rng.normal(promo, 0.12), 0, 1)) * 100, 2),
                    "skor_member": round(float(np.clip(rng.normal(member, 0.14), 0, 1)) * 100, 2),
                    "respons_promo": round(float(np.clip(rng.normal(response, 0.16), 0, 1)) * 100, 2),
                }
            )
    return pd.DataFrame(rows)


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()


def categorical_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(exclude=[np.number]).columns.tolist()


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


def membership_sets(series: pd.Series) -> dict[str, tuple[str, tuple[float, ...]]]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    low = float(values.min())
    high = float(values.max())
    if low == high:
        high = low + 1
    q1 = float(values.quantile(0.25))
    q2 = float(values.quantile(0.50))
    q3 = float(values.quantile(0.75))
    if len({low, q1, q2, q3, high}) < 5:
        q1 = low + (high - low) * 0.25
        q2 = low + (high - low) * 0.5
        q3 = low + (high - low) * 0.75
    return {
        "rendah": ("left", (low, q3)),
        "sedang": ("triangle", (q1, q2, q3)),
        "tinggi": ("right", (q1, high)),
    }


def membership_value(value: float, definition: tuple[str, tuple[float, ...]]) -> float:
    kind, points = definition
    if pd.isna(value):
        return 0.0
    if kind == "left":
        return float(np.clip(left_shoulder(float(value), *points), 0, 1))
    if kind == "right":
        return float(np.clip(right_shoulder(float(value), *points), 0, 1))
    return float(np.clip(triangle(float(value), *points), 0, 1))


def fuzzify_numeric_items(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    for column in columns:
        sets = membership_sets(df[column])
        for term in TERMS:
            result[f"{column}={term}"] = df[column].apply(lambda value, s=sets[term]: membership_value(value, s))
    return result.round(4)


def categorical_items(df: pd.DataFrame, columns: list[str], max_values: int = 8) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    for column in columns:
        values = df[column].astype(str).value_counts().head(max_values).index.tolist()
        for value in values:
            result[f"{column}={value}"] = (df[column].astype(str) == value).astype(float)
    return result


def item_support(item_df: pd.DataFrame, items: tuple[str, ...]) -> float:
    if not items:
        return 0.0
    return float(item_df[list(items)].min(axis=1).mean())


def mine_rules(
    item_df: pd.DataFrame,
    min_support: float,
    min_confidence: float,
    max_antecedent: int = 2,
    top_n: int = 100,
) -> pd.DataFrame:
    item_names = item_df.columns.tolist()
    support_cache = {}

    def support(items: tuple[str, ...]) -> float:
        key = tuple(sorted(items))
        if key not in support_cache:
            support_cache[key] = item_support(item_df, key)
        return support_cache[key]

    rules = []
    for antecedent_size in range(1, max_antecedent + 1):
        for antecedent in combinations(item_names, antecedent_size):
            ant_support = support(antecedent)
            if ant_support <= 0:
                continue
            for consequent in item_names:
                if consequent in antecedent:
                    continue
                both = tuple(sorted((*antecedent, consequent)))
                sup = support(both)
                conf = sup / ant_support if ant_support else 0
                cons_support = support((consequent,))
                lift = conf / cons_support if cons_support else 0
                if sup >= min_support and conf >= min_confidence:
                    rules.append(
                        {
                            "antecedent": " AND ".join(antecedent),
                            "consequent": consequent,
                            "support": round(sup, 4),
                            "confidence": round(conf, 4),
                            "lift": round(lift, 4),
                        }
                    )
    if not rules:
        return pd.DataFrame(columns=["antecedent", "consequent", "support", "confidence", "lift", "interpretasi"])
    result = pd.DataFrame(rules)
    result = result.sort_values(["lift", "confidence", "support"], ascending=False).head(top_n).reset_index(drop=True)
    result["interpretasi"] = result.apply(interpret_rule, axis=1)
    return result


def interpret_rule(row: pd.Series) -> str:
    antecedent = str(row["antecedent"]).replace("=", " ")
    consequent = str(row["consequent"]).replace("=", " ")
    return (
        f"Jika {antecedent}, maka cenderung {consequent} "
        f"(confidence {row['confidence']:.2f}, lift {row['lift']:.2f})."
    )

