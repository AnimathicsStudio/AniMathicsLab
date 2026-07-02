import numpy as np
import pandas as pd


CRITERIA = [
    "IPK",
    "Penghasilan Orang Tua",
    "Jumlah Tanggungan",
    "Prestasi",
    "Keaktifan Organisasi",
]


DEFAULT_TYPES = {
    "IPK": "benefit",
    "Penghasilan Orang Tua": "cost",
    "Jumlah Tanggungan": "benefit",
    "Prestasi": "benefit",
    "Keaktifan Organisasi": "benefit",
}


DEFAULT_WEIGHTS = {
    "IPK": 0.28,
    "Penghasilan Orang Tua": 0.30,
    "Jumlah Tanggungan": 0.18,
    "Prestasi": 0.14,
    "Keaktifan Organisasi": 0.10,
}


def sample_beasiswa_data():
    return pd.DataFrame(
        [
            {
                "Alternatif": "Alya Prameswari",
                "IPK": 3.72,
                "Penghasilan Orang Tua": 2_500_000,
                "Jumlah Tanggungan": 3,
                "Prestasi": 72,
                "Keaktifan Organisasi": 78,
            },
            {
                "Alternatif": "Bagas Wicaksono",
                "IPK": 3.55,
                "Penghasilan Orang Tua": 1_400_000,
                "Jumlah Tanggungan": 5,
                "Prestasi": 65,
                "Keaktifan Organisasi": 82,
            },
            {
                "Alternatif": "Citra Lestari",
                "IPK": 3.88,
                "Penghasilan Orang Tua": 3_800_000,
                "Jumlah Tanggungan": 2,
                "Prestasi": 91,
                "Keaktifan Organisasi": 70,
            },
            {
                "Alternatif": "Dimas Saputra",
                "IPK": 3.36,
                "Penghasilan Orang Tua": 1_900_000,
                "Jumlah Tanggungan": 4,
                "Prestasi": 58,
                "Keaktifan Organisasi": 88,
            },
            {
                "Alternatif": "Eka Rahmawati",
                "IPK": 3.64,
                "Penghasilan Orang Tua": 2_100_000,
                "Jumlah Tanggungan": 6,
                "Prestasi": 76,
                "Keaktifan Organisasi": 64,
            },
        ]
    )


def normalize_weights(weights):
    series = pd.Series(weights, dtype=float)
    total = float(series.sum())
    if total <= 0:
        return pd.Series(1 / len(series), index=series.index)
    return series / total


def decision_matrix(df, criteria):
    clean = df.copy()
    for criterion in criteria:
        clean[criterion] = pd.to_numeric(clean[criterion], errors="coerce")
    clean = clean.dropna(subset=["Alternatif", *criteria]).reset_index(drop=True)
    return clean


def minmax_fuzzy_normalize(df, criteria, criterion_types):
    normalized = pd.DataFrame({"Alternatif": df["Alternatif"]})

    for criterion in criteria:
        values = df[criterion].astype(float)
        min_value = values.min()
        max_value = values.max()
        span = max_value - min_value

        if span == 0:
            normalized[criterion] = 1.0
            continue

        if criterion_types[criterion] == "cost":
            normalized[criterion] = (max_value - values) / span
        else:
            normalized[criterion] = (values - min_value) / span

    return normalized


def saw(df, criteria, weights, criterion_types):
    norm = minmax_fuzzy_normalize(df, criteria, criterion_types)
    weight_series = normalize_weights(weights)
    weighted = norm.copy()

    for criterion in criteria:
        weighted[criterion] = norm[criterion] * weight_series[criterion]

    scores = weighted[criteria].sum(axis=1)
    result = pd.DataFrame(
        {
            "Alternatif": df["Alternatif"],
            "Skor": scores,
        }
    )
    return norm, weighted, rank_scores(result)


def topsis(df, criteria, weights, criterion_types):
    values = df[criteria].astype(float)
    denominator = np.sqrt((values**2).sum(axis=0)).replace(0, np.nan)
    norm_values = values / denominator
    norm_values = norm_values.fillna(0)

    weight_series = normalize_weights(weights)
    weighted_values = norm_values * weight_series[criteria]

    ideal_best = {}
    ideal_worst = {}
    for criterion in criteria:
        if criterion_types[criterion] == "cost":
            ideal_best[criterion] = weighted_values[criterion].min()
            ideal_worst[criterion] = weighted_values[criterion].max()
        else:
            ideal_best[criterion] = weighted_values[criterion].max()
            ideal_worst[criterion] = weighted_values[criterion].min()

    best_vector = pd.Series(ideal_best)
    worst_vector = pd.Series(ideal_worst)
    distance_best = np.sqrt(((weighted_values - best_vector) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_values - worst_vector) ** 2).sum(axis=1))
    closeness = distance_worst / (distance_best + distance_worst).replace(0, np.nan)
    closeness = closeness.fillna(0)

    norm = pd.concat([df[["Alternatif"]], norm_values], axis=1)
    weighted = pd.concat([df[["Alternatif"]], weighted_values], axis=1)
    result = pd.DataFrame(
        {
            "Alternatif": df["Alternatif"],
            "Jarak Ideal Positif": distance_best,
            "Jarak Ideal Negatif": distance_worst,
            "Skor": closeness,
        }
    )
    return norm, weighted, rank_scores(result)


def wp(df, criteria, weights, criterion_types):
    values = df[criteria].astype(float).copy()
    values = values.replace(0, np.nan)

    weight_series = normalize_weights(weights)
    powers = pd.Series(index=criteria, dtype=float)
    for criterion in criteria:
        sign = -1 if criterion_types[criterion] == "cost" else 1
        powers[criterion] = sign * weight_series[criterion]

    powered = values.copy()
    for criterion in criteria:
        powered[criterion] = values[criterion] ** powers[criterion]

    vector_s = powered.prod(axis=1).replace([np.inf, -np.inf], np.nan).fillna(0)
    total = vector_s.sum()
    scores = vector_s / total if total > 0 else vector_s

    norm = minmax_fuzzy_normalize(df, criteria, criterion_types)
    weighted = pd.concat([df[["Alternatif"]], powered], axis=1)
    result = pd.DataFrame(
        {
            "Alternatif": df["Alternatif"],
            "Vektor S": vector_s,
            "Skor": scores,
        }
    )
    return norm, weighted, rank_scores(result)


def rank_scores(result):
    ranked = result.sort_values("Skor", ascending=False).reset_index(drop=True)
    ranked.insert(0, "Peringkat", np.arange(1, len(ranked) + 1))
    return ranked


def compare_methods(df, criteria, weights, criterion_types):
    _, _, saw_rank = saw(df, criteria, weights, criterion_types)
    _, _, topsis_rank = topsis(df, criteria, weights, criterion_types)
    _, _, wp_rank = wp(df, criteria, weights, criterion_types)

    combined = pd.DataFrame({"Alternatif": df["Alternatif"]})
    for method_name, rank in {
        "SAW": saw_rank,
        "TOPSIS": topsis_rank,
        "WP": wp_rank,
    }.items():
        method_cols = rank[["Alternatif", "Peringkat", "Skor"]].rename(
            columns={
                "Peringkat": f"Peringkat {method_name}",
                "Skor": f"Skor {method_name}",
            }
        )
        combined = combined.merge(method_cols, on="Alternatif", how="left")

    return combined


def calculate_method(method, df, criteria, weights, criterion_types):
    if method == "SAW":
        return saw(df, criteria, weights, criterion_types)
    if method == "TOPSIS":
        return topsis(df, criteria, weights, criterion_types)
    if method == "WP":
        return wp(df, criteria, weights, criterion_types)
    raise ValueError(f"Metode tidak dikenal: {method}")


def sensitivity_analysis(df, criteria, weights, criterion_types, focus_criterion, method):
    rows = []
    base_weights = normalize_weights(weights)

    for focus_weight in np.linspace(0.05, 0.70, 14):
        adjusted = base_weights.copy()
        other_criteria = [c for c in criteria if c != focus_criterion]
        remaining = max(1 - focus_weight, 0)
        other_total = base_weights[other_criteria].sum()

        adjusted[focus_criterion] = focus_weight
        if other_total <= 0:
            for criterion in other_criteria:
                adjusted[criterion] = remaining / len(other_criteria)
        else:
            for criterion in other_criteria:
                adjusted[criterion] = base_weights[criterion] / other_total * remaining

        _, _, rank = calculate_method(
            method, df, criteria, adjusted.to_dict(), criterion_types
        )
        for _, item in rank.iterrows():
            rows.append(
                {
                    "Bobot Fokus": focus_weight,
                    "Alternatif": item["Alternatif"],
                    "Peringkat": item["Peringkat"],
                    "Skor": item["Skor"],
                }
            )

    return pd.DataFrame(rows)


def best_reason(df, ranking, criteria, weights, criterion_types):
    if ranking.empty:
        return "Belum ada alternatif yang dapat diranking."

    best_name = ranking.iloc[0]["Alternatif"]
    best_row = df[df["Alternatif"] == best_name].iloc[0]
    weight_series = normalize_weights(weights)
    top_criteria = list(weight_series.sort_values(ascending=False).head(2).index)
    phrases = []

    for criterion in top_criteria:
        value = best_row[criterion]
        ctype = criterion_types[criterion]
        if ctype == "cost":
            phrases.append(f"{criterion.lower()} relatif rendah ({value:,.0f})")
        else:
            phrases.append(f"{criterion.lower()} kuat ({value:,.2f})")

    return (
        f"{best_name} menjadi rekomendasi utama karena memiliki kombinasi "
        + " dan ".join(phrases)
        + ". Hasil ini tetap bergantung pada bobot dan tipe kriteria yang dipilih."
    )
