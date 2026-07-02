import math
from collections import Counter, defaultdict

import numpy as np
import pandas as pd


def sample_sales_data():
    dates = pd.date_range("2026-01-01", periods=36, freq="D")
    values = [
        112, 118, 121, 119, 126, 132, 129, 135, 141, 138, 144, 149,
        153, 148, 156, 162, 158, 165, 171, 168, 174, 181, 176, 184,
        189, 185, 193, 199, 196, 204, 211, 207, 216, 222, 218, 226,
    ]
    return pd.DataFrame({"Tanggal": dates, "Penjualan": values})


def clean_timeseries(df, date_col, value_col):
    data = df[[date_col, value_col]].copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data[value_col] = pd.to_numeric(data[value_col], errors="coerce")
    data = data.dropna().sort_values(date_col).reset_index(drop=True)
    data = data.rename(columns={date_col: "Tanggal", value_col: "Nilai"})
    return data


def make_intervals(values, n_intervals, padding_ratio=0.05):
    min_value = float(np.min(values))
    max_value = float(np.max(values))
    span = max(max_value - min_value, 1.0)
    padding = span * padding_ratio
    lower = min_value - padding
    upper = max_value + padding
    edges = np.linspace(lower, upper, n_intervals + 1)
    intervals = []
    for idx in range(n_intervals):
        low = float(edges[idx])
        high = float(edges[idx + 1])
        midpoint = (low + high) / 2
        intervals.append(
            {
                "State": f"A{idx + 1}",
                "Batas Bawah": low,
                "Batas Atas": high,
                "Titik Tengah": midpoint,
            }
        )
    return pd.DataFrame(intervals)


def fuzzify_value(value, intervals):
    for _, row in intervals.iterrows():
        if row["Batas Bawah"] <= value <= row["Batas Atas"]:
            return row["State"]
    if value < intervals.iloc[0]["Batas Bawah"]:
        return intervals.iloc[0]["State"]
    return intervals.iloc[-1]["State"]


def midpoint_for_state(intervals, state):
    row = intervals[intervals["State"] == state].iloc[0]
    return float(row["Titik Tengah"])


def fuzzify_series(data, intervals):
    result = data.copy()
    result["State"] = result["Nilai"].apply(lambda value: fuzzify_value(value, intervals))
    result["Titik Tengah State"] = result["State"].apply(lambda state: midpoint_for_state(intervals, state))
    return result


def build_flr(fuzzy_data):
    rows = []
    for idx in range(len(fuzzy_data) - 1):
        rows.append(
            {
                "Periode": idx + 1,
                "Dari": fuzzy_data.loc[idx, "State"],
                "Ke": fuzzy_data.loc[idx + 1, "State"],
                "Relasi": f"{fuzzy_data.loc[idx, 'State']} -> {fuzzy_data.loc[idx + 1, 'State']}",
            }
        )
    return pd.DataFrame(rows)


def build_flrg(flr):
    grouped = defaultdict(list)
    for _, row in flr.iterrows():
        grouped[row["Dari"]].append(row["Ke"])
    rows = []
    for state in sorted(grouped.keys(), key=lambda item: int(item[1:])):
        next_states = grouped[state]
        rows.append(
            {
                "State": state,
                "Tujuan": ", ".join(next_states),
                "Tujuan Unik": ", ".join(sorted(set(next_states), key=lambda item: int(item[1:]))),
                "Jumlah Relasi": len(next_states),
            }
        )
    return pd.DataFrame(rows)


def chen_forecast_for_state(state, flrg, intervals):
    if state not in set(flrg["State"]):
        return midpoint_for_state(intervals, state)
    destinations = flrg[flrg["State"] == state].iloc[0]["Tujuan"].split(", ")
    mids = [midpoint_for_state(intervals, destination) for destination in destinations]
    return float(np.mean(mids))


def chen_detail_for_state(state, flrg, intervals):
    if state not in set(flrg["State"]):
        midpoint = midpoint_for_state(intervals, state)
        return pd.DataFrame(
            [
                {
                    "Dari": state,
                    "Ke": state,
                    "Titik Tengah": midpoint,
                    "Keterangan": "Tidak ada riwayat relasi; memakai titik tengah state saat ini.",
                }
            ]
        )
    destinations = flrg[flrg["State"] == state].iloc[0]["Tujuan"].split(", ")
    counts = Counter(destinations)
    total = sum(counts.values())
    rows = []
    for idx, destination in enumerate(sorted(counts.keys(), key=lambda item: int(item[1:])), start=1):
        midpoint = midpoint_for_state(intervals, destination)
        contribution = counts[destination] * midpoint / total
        rows.append(
            {
                "No": idx,
                "Dari": state,
                "Ke": destination,
                "Frekuensi": int(counts[destination]),
                "Titik Tengah": midpoint,
                "Kontribusi Rata-rata": contribution,
                "Keterangan": f"Muncul {counts[destination]} dari {total} relasi.",
            }
        )
    return pd.DataFrame(rows)


def markov_forecast_for_state(state, flr, intervals):
    subset = flr[flr["Dari"] == state]
    if subset.empty:
        return midpoint_for_state(intervals, state), pd.DataFrame()
    counts = subset["Ke"].value_counts().sort_index()
    total = counts.sum()
    rows = []
    prediction = 0.0
    for target, count in counts.items():
        probability = count / total
        midpoint = midpoint_for_state(intervals, target)
        prediction += probability * midpoint
        rows.append(
            {
                "Dari": state,
                "Ke": target,
                "Frekuensi": int(count),
                "Probabilitas": probability,
                "Titik Tengah": midpoint,
                "Kontribusi": probability * midpoint,
            }
        )
    return float(prediction), pd.DataFrame(rows)


def forecast_series(data, intervals, method):
    fuzzy = fuzzify_series(data, intervals)
    flr = build_flr(fuzzy)
    flrg = build_flrg(flr)

    predictions = [np.nan]
    markov_details = {}
    for idx in range(1, len(fuzzy)):
        previous_state = fuzzy.loc[idx - 1, "State"]
        if method == "Fuzzy Markov Chain":
            pred, detail = markov_forecast_for_state(previous_state, flr.iloc[: idx - 1], intervals)
            if math.isnan(pred):
                pred = midpoint_for_state(intervals, previous_state)
            markov_details[idx] = detail
            predictions.append(pred)
        else:
            local_flr = flr.iloc[: idx - 1]
            local_flrg = build_flrg(local_flr) if not local_flr.empty else flrg.iloc[0:0]
            predictions.append(chen_forecast_for_state(previous_state, local_flrg, intervals))

    result = fuzzy.copy()
    result["Prediksi"] = predictions
    result["Error"] = result["Nilai"] - result["Prediksi"]
    result["Abs Error"] = result["Error"].abs()
    result["APE"] = np.where(result["Nilai"] != 0, result["Abs Error"] / result["Nilai"] * 100, np.nan)

    last_state = fuzzy.iloc[-1]["State"]
    if method == "Fuzzy Markov Chain":
        next_forecast, next_detail = markov_forecast_for_state(last_state, flr, intervals)
    else:
        next_forecast = chen_forecast_for_state(last_state, flrg, intervals)
        next_detail = chen_detail_for_state(last_state, flrg, intervals)

    return {
        "fuzzy": fuzzy,
        "flr": flr,
        "flrg": flrg,
        "forecast": result,
        "next_forecast": float(next_forecast),
        "last_state": last_state,
        "next_detail": next_detail,
        "markov_details": markov_details,
    }


def evaluate_forecast(forecast):
    valid = forecast.dropna(subset=["Prediksi"]).copy()
    if valid.empty:
        return {"MAE": np.nan, "MAPE": np.nan, "RMSE": np.nan}
    mae = float(valid["Abs Error"].mean())
    mape = float(valid["APE"].mean())
    rmse = float(np.sqrt((valid["Error"] ** 2).mean()))
    return {"MAE": mae, "MAPE": mape, "RMSE": rmse}
