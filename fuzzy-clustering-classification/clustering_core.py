from __future__ import annotations

import numpy as np
import pandas as pd


def sample_customer_data() -> pd.DataFrame:
    rng = np.random.default_rng(41)
    segments = [
        ("Hemat", 35, 2.0, 18, 4.0, 42, 0.35),
        ("Reguler", 45, 4.0, 35, 6.2, 58, 0.55),
        ("Loyal", 55, 7.0, 65, 8.0, 78, 0.78),
        ("Premium", 70, 10.0, 110, 9.0, 88, 0.9),
    ]
    rows = []
    for label, spend, freq, basket, satisfaction, loyalty, promo in segments:
        for idx in range(35):
            rows.append(
                {
                    "pelanggan": f"{label[:3].upper()}-{idx + 1:02d}",
                    "segmen_awal": label,
                    "belanja_bulanan": round(max(5, rng.normal(spend, 8)), 2),
                    "frekuensi_transaksi": round(max(1, rng.normal(freq, 1.2)), 2),
                    "nilai_keranjang": round(max(5, rng.normal(basket, 14)), 2),
                    "kepuasan": round(float(np.clip(rng.normal(satisfaction, 0.9), 1, 10)), 2),
                    "loyalitas": round(float(np.clip(rng.normal(loyalty, 8), 0, 100)), 2),
                    "respons_promo": round(float(np.clip(rng.normal(promo, 0.12), 0, 1)), 3),
                }
            )
    return pd.DataFrame(rows)


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()


def first_text_column(df: pd.DataFrame) -> str | None:
    columns = df.select_dtypes(exclude=[np.number]).columns.tolist()
    return columns[0] if columns else None


def prepare_matrix(df: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    data = df[features].apply(pd.to_numeric, errors="coerce")
    data = data.fillna(data.median(numeric_only=True))
    x = data.to_numpy(dtype=float)
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std[std == 0] = 1.0
    return (x - mean) / std, mean, std


def run_fcm(
    x: np.ndarray,
    n_clusters: int,
    m: float = 2.0,
    max_iter: int = 150,
    tol: float = 1e-4,
    seed: int = 41,
) -> dict:
    if n_clusters < 2:
        raise ValueError("Jumlah cluster minimal 2.")
    if n_clusters > len(x):
        raise ValueError("Jumlah cluster tidak boleh melebihi jumlah data.")
    if m <= 1:
        raise ValueError("Parameter m harus lebih besar dari 1.")

    rng = np.random.default_rng(seed)
    u = rng.random((len(x), n_clusters))
    u = u / u.sum(axis=1, keepdims=True)
    objectives = []

    for iteration in range(max_iter):
        u_m = u ** m
        centers = (u_m.T @ x) / u_m.sum(axis=0)[:, None]
        distances = np.linalg.norm(x[:, None, :] - centers[None, :, :], axis=2)
        distances = np.fmax(distances, 1e-10)
        objective = float(np.sum(u_m * distances**2))
        objectives.append(objective)

        power = 2 / (m - 1)
        ratio = (distances[:, :, None] / distances[:, None, :]) ** power
        new_u = 1 / ratio.sum(axis=2)

        if np.max(np.abs(new_u - u)) < tol:
            u = new_u
            break
        u = new_u

    labels = np.argmax(u, axis=1)
    return {
        "membership": u,
        "centers_scaled": centers,
        "labels": labels,
        "objectives": objectives,
        "iterations": len(objectives),
    }


def inverse_centers(centers_scaled: np.ndarray, mean: np.ndarray, std: np.ndarray, features: list[str]) -> pd.DataFrame:
    centers = centers_scaled * std + mean
    df = pd.DataFrame(centers, columns=features)
    df.insert(0, "cluster", [f"Cluster {i + 1}" for i in range(len(df))])
    return df


def membership_table(df: pd.DataFrame, membership: np.ndarray, labels: np.ndarray, name_col: str | None) -> pd.DataFrame:
    result = pd.DataFrame()
    if name_col:
        result[name_col] = df[name_col].astype(str)
    for idx in range(membership.shape[1]):
        result[f"mu_cluster_{idx + 1}"] = membership[:, idx].round(4)
    result["cluster_dominan"] = [f"Cluster {label + 1}" for label in labels]
    result["derajat_dominan"] = membership.max(axis=1).round(4)
    return result


def cluster_profile(df: pd.DataFrame, features: list[str], labels: np.ndarray) -> pd.DataFrame:
    prof = df[features].copy()
    prof["cluster"] = [f"Cluster {label + 1}" for label in labels]
    summary = prof.groupby("cluster")[features].mean().round(3)
    summary.insert(0, "jumlah_data", prof.groupby("cluster").size())
    return summary.reset_index()


def classify_by_centers(row: pd.Series, centers: pd.DataFrame, features: list[str]) -> tuple[str, float]:
    x = row[features].to_numpy(dtype=float)
    center_values = centers[features].to_numpy(dtype=float)
    distances = np.linalg.norm(center_values - x, axis=1)
    idx = int(np.argmin(distances))
    similarity = 1 / (1 + distances[idx])
    return str(centers.loc[idx, "cluster"]), round(float(similarity), 4)


def membership_for_point(
    values: np.ndarray,
    centers_scaled: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
    m: float = 2.0,
) -> np.ndarray:
    x_scaled = (values.astype(float) - mean) / std
    distances = np.linalg.norm(x_scaled[None, :] - centers_scaled, axis=1)
    distances = np.fmax(distances, 1e-10)
    power = 2 / (m - 1)
    ratio = (distances[:, None] / distances[None, :]) ** power
    return 1 / ratio.sum(axis=1)
