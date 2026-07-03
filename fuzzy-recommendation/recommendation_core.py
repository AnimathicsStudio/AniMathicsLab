from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


FEATURES = {
    "price_idr": {"label": "Harga", "type": "cost", "unit": "IDR"},
    "rating": {"label": "Rating", "type": "benefit", "unit": "poin"},
    "ram_gb": {"label": "RAM", "type": "benefit", "unit": "GB"},
    "storage_gb": {"label": "Storage", "type": "benefit", "unit": "GB"},
    "battery_mah": {"label": "Baterai", "type": "benefit", "unit": "mAh"},
    "screen_size_in": {"label": "Ukuran layar", "type": "benefit", "unit": "inci"},
    "resolution_width_px": {"label": "Resolusi", "type": "benefit", "unit": "px"},
    "rear_camera_max_mp": {"label": "Kamera utama", "type": "benefit", "unit": "MP"},
    "front_camera_mp": {"label": "Kamera depan", "type": "benefit", "unit": "MP"},
    "clock_ghz": {"label": "Clock CPU", "type": "benefit", "unit": "GHz"},
    "network_generation": {"label": "Generasi jaringan", "type": "benefit", "unit": "G"},
    "nfc": {"label": "NFC", "type": "benefit", "unit": ""},
}

TERM_TARGET = {"rendah": 0.15, "sedang": 0.5, "tinggi": 0.85}
TERM_FROM_SLIDER = {0: "rendah", 1: "sedang", 2: "tinggi"}

PERSONAS = {
    "Pelajar hemat": {
        "terms": {"price_idr": "rendah", "rating": "sedang", "battery_mah": "tinggi", "ram_gb": "sedang"},
        "weights": {"price_idr": 5, "rating": 3, "battery_mah": 4, "ram_gb": 3},
    },
    "Gamer": {
        "terms": {"price_idr": "sedang", "ram_gb": "tinggi", "clock_ghz": "tinggi", "battery_mah": "tinggi", "screen_size_in": "tinggi"},
        "weights": {"price_idr": 2, "ram_gb": 5, "clock_ghz": 5, "battery_mah": 4, "screen_size_in": 3},
    },
    "Content creator": {
        "terms": {"price_idr": "sedang", "rear_camera_max_mp": "tinggi", "front_camera_mp": "tinggi", "storage_gb": "tinggi", "rating": "tinggi"},
        "weights": {"price_idr": 2, "rear_camera_max_mp": 5, "front_camera_mp": 4, "storage_gb": 4, "rating": 3},
    },
    "Pekerja mobile": {
        "terms": {"price_idr": "sedang", "battery_mah": "tinggi", "nfc": "tinggi", "network_generation": "tinggi", "rating": "tinggi"},
        "weights": {"price_idr": 2, "battery_mah": 5, "nfc": 4, "network_generation": 4, "rating": 4},
    },
}


def load_default_data(base_path: Path) -> pd.DataFrame:
    return pd.read_csv(base_path / "sample_data" / "smartphones_tahani.csv")


def numeric_feature_columns(df: pd.DataFrame) -> list[str]:
    candidates = [column for column in FEATURES if column in df.columns]
    return [column for column in candidates if pd.api.types.is_numeric_dtype(df[column])]


def normalize_feature(series: pd.Series, feature_type: str) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    min_value = values.min()
    max_value = values.max()
    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        return pd.Series(0.5, index=series.index)
    normalized = (values - min_value) / (max_value - min_value)
    if feature_type == "cost":
        normalized = 1 - normalized
    return normalized.clip(0, 1).fillna(0.0)


def feature_match(normalized: pd.Series, target_term: str) -> pd.Series:
    target = TERM_TARGET[target_term]
    return (1 - (normalized - target).abs()).clip(0, 1)


def recommend(
    df: pd.DataFrame,
    selected_features: list[str],
    terms: dict[str, str],
    weights: dict[str, int],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    details = pd.DataFrame(index=df.index)
    weighted_parts = []
    total_weight = 0

    for feature in selected_features:
        meta = FEATURES[feature]
        normalized = normalize_feature(df[feature], meta["type"])
        score = feature_match(normalized, terms[feature])
        weight = int(weights.get(feature, 1))
        details[f"{feature}_normalized"] = normalized.round(4)
        details[f"{feature}_match"] = score.round(4)
        weighted_parts.append(score * weight)
        total_weight += weight

    total_score = sum(weighted_parts) / max(total_weight, 1)
    result = df.copy()
    result["_source_index"] = df.index
    result["Skor Cocok"] = total_score.round(4)
    result["Ranking"] = result["Skor Cocok"].rank(method="min", ascending=False).astype(int)
    result = result.sort_values(["Skor Cocok", "Ranking"], ascending=[False, True]).reset_index(drop=True)
    details["Skor Cocok"] = total_score.round(4)
    return result, details


def reason_for_item(row: pd.Series, selected_features: list[str], terms: dict[str, str], details_row: pd.Series) -> str:
    parts = []
    for feature in selected_features:
        label = FEATURES[feature]["label"]
        term = terms[feature]
        match = details_row[f"{feature}_match"]
        if match >= 0.8:
            parts.append(f"{label} sangat sesuai ({term})")
        elif match >= 0.6:
            parts.append(f"{label} cukup sesuai ({term})")
    if not parts:
        return "Kecocokan tersebar, tidak ada fitur yang sangat dominan."
    return "; ".join(parts[:4]) + "."


def format_number_id(value: object) -> str:
    if pd.isna(value) or not isinstance(value, (int, float, np.integer, np.floating)):
        return ""
    if abs(float(value)) >= 1000:
        if float(value).is_integer():
            return f"{int(value):,}".replace(",", ".")
        whole, decimal = f"{float(value):,.2f}".split(".")
        return f"{whole.replace(',', '.')},{decimal}"
    return f"{float(value):g}"


def display_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    formatters = {column: format_number_id for column in df.select_dtypes(include="number").columns}
    return df.style.format(formatters)
