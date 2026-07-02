import numpy as np
import pandas as pd


def trimf(x, abc):
    a, b, c = abc
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x, dtype=float)

    if a != b:
        left = (a < x) & (x < b)
        y[left] = (x[left] - a) / (b - a)
    y[x == b] = 1.0
    if b != c:
        right = (b < x) & (x < c)
        y[right] = (c - x[right]) / (c - b)
    return np.clip(y, 0, 1)


def trapmf(x, abcd):
    a, b, c, d = abcd
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x, dtype=float)

    if a != b:
        left = (a < x) & (x < b)
        y[left] = (x[left] - a) / (b - a)
    y[(b <= x) & (x <= c)] = 1.0
    if c != d:
        right = (c < x) & (x < d)
        y[right] = (d - x[right]) / (d - c)
    return np.clip(y, 0, 1)


def mf_value(value, mf):
    kind, params = mf
    x = np.array([value], dtype=float)
    if kind == "tri":
        return float(trimf(x, params)[0])
    return float(trapmf(x, params)[0])


def mf_curve(x, mf):
    kind, params = mf
    if kind == "tri":
        return trimf(x, params)
    return trapmf(x, params)


def centroid(x, mu):
    area = np.trapz(mu, x)
    if area <= 0:
        return float(np.mean(x))
    return float(np.trapz(x * mu, x) / area)


def fan_case():
    return {
        "name": "Kipas Otomatis",
        "description": "Sistem menentukan kecepatan kipas dari suhu dan kelembapan udara.",
        "inputs": {
            "Suhu": {
                "unit": "°C",
                "range": (16.0, 40.0),
                "default": 30.0,
                "step": 0.5,
                "sets": {
                    "rendah": ("trap", [16, 16, 20, 25]),
                    "sedang": ("tri", [22, 28, 34]),
                    "tinggi": ("trap", [30, 35, 40, 40]),
                },
            },
            "Kelembapan": {
                "unit": "%",
                "range": (20.0, 95.0),
                "default": 65.0,
                "step": 1.0,
                "sets": {
                    "rendah": ("trap", [20, 20, 35, 50]),
                    "sedang": ("tri", [40, 60, 80]),
                    "tinggi": ("trap", [70, 85, 95, 95]),
                },
            },
        },
        "output": {
            "name": "Kecepatan Kipas",
            "unit": "%",
            "range": (0.0, 100.0),
            "sets": {
                "pelan": ("trap", [0, 0, 25, 45]),
                "sedang": ("tri", [30, 55, 80]),
                "cepat": ("trap", [65, 85, 100, 100]),
            },
            "sugeno": {
                "pelan": 25.0,
                "sedang": 55.0,
                "cepat": 88.0,
            },
        },
        "rules": [
            {"if": {"Suhu": "rendah"}, "then": "pelan", "operator": "AND", "label": "Jika suhu rendah, maka kipas pelan."},
            {"if": {"Suhu": "sedang", "Kelembapan": "rendah"}, "then": "sedang", "operator": "AND", "label": "Jika suhu sedang dan kelembapan rendah, maka kipas sedang."},
            {"if": {"Suhu": "sedang", "Kelembapan": "sedang"}, "then": "sedang", "operator": "AND", "label": "Jika suhu sedang dan kelembapan sedang, maka kipas sedang."},
            {"if": {"Suhu": "tinggi", "Kelembapan": "rendah"}, "then": "cepat", "operator": "AND", "label": "Jika suhu tinggi dan kelembapan rendah, maka kipas cepat."},
            {"if": {"Suhu": "tinggi", "Kelembapan": "sedang"}, "then": "cepat", "operator": "AND", "label": "Jika suhu tinggi dan kelembapan sedang, maka kipas cepat."},
            {"if": {"Suhu": "tinggi", "Kelembapan": "tinggi"}, "then": "cepat", "operator": "AND", "label": "Jika suhu tinggi dan kelembapan tinggi, maka kipas cepat."},
            {"if": {"Kelembapan": "tinggi"}, "then": "cepat", "operator": "AND", "label": "Jika kelembapan tinggi, maka kipas cepat."},
        ],
        "category": [(0, 40, "pelan"), (40, 70, "sedang"), (70, 100.1, "cepat")],
    }


def watering_case():
    return {
        "name": "Penyiraman Tanaman Otomatis",
        "description": "Sistem menentukan durasi penyiraman dari kelembapan tanah, suhu lingkungan, dan intensitas cahaya.",
        "inputs": {
            "Kelembapan Tanah": {
                "unit": "%",
                "range": (0.0, 100.0),
                "default": 35.0,
                "step": 1.0,
                "sets": {
                    "kering": ("trap", [0, 0, 25, 45]),
                    "sedang": ("tri", [30, 55, 80]),
                    "basah": ("trap", [65, 85, 100, 100]),
                },
            },
            "Suhu": {
                "unit": "°C",
                "range": (16.0, 40.0),
                "default": 31.0,
                "step": 0.5,
                "sets": {
                    "rendah": ("trap", [16, 16, 20, 25]),
                    "sedang": ("tri", [22, 28, 34]),
                    "tinggi": ("trap", [30, 35, 40, 40]),
                },
            },
            "Cahaya": {
                "unit": "%",
                "range": (0.0, 100.0),
                "default": 75.0,
                "step": 1.0,
                "sets": {
                    "redup": ("trap", [0, 0, 25, 45]),
                    "sedang": ("tri", [30, 55, 80]),
                    "terik": ("trap", [65, 85, 100, 100]),
                },
            },
        },
        "output": {
            "name": "Durasi Penyiraman",
            "unit": "menit",
            "range": (0.0, 30.0),
            "sets": {
                "pendek": ("trap", [0, 0, 6, 12]),
                "sedang": ("tri", [8, 15, 22]),
                "lama": ("trap", [18, 24, 30, 30]),
            },
            "sugeno": {
                "pendek": 5.0,
                "sedang": 15.0,
                "lama": 25.0,
            },
        },
        "rules": [
            {"if": {"Kelembapan Tanah": "basah"}, "then": "pendek", "operator": "AND", "label": "Jika tanah basah, maka penyiraman pendek."},
            {"if": {"Kelembapan Tanah": "sedang", "Suhu": "rendah"}, "then": "pendek", "operator": "AND", "label": "Jika tanah sedang dan suhu rendah, maka penyiraman pendek."},
            {"if": {"Kelembapan Tanah": "sedang", "Cahaya": "sedang"}, "then": "sedang", "operator": "AND", "label": "Jika tanah sedang dan cahaya sedang, maka penyiraman sedang."},
            {"if": {"Kelembapan Tanah": "sedang", "Cahaya": "terik"}, "then": "sedang", "operator": "AND", "label": "Jika tanah sedang dan cahaya terik, maka penyiraman sedang."},
            {"if": {"Kelembapan Tanah": "kering", "Suhu": "rendah"}, "then": "sedang", "operator": "AND", "label": "Jika tanah kering dan suhu rendah, maka penyiraman sedang."},
            {"if": {"Kelembapan Tanah": "kering", "Suhu": "sedang"}, "then": "lama", "operator": "AND", "label": "Jika tanah kering dan suhu sedang, maka penyiraman lama."},
            {"if": {"Kelembapan Tanah": "kering", "Suhu": "tinggi"}, "then": "lama", "operator": "AND", "label": "Jika tanah kering dan suhu tinggi, maka penyiraman lama."},
            {"if": {"Kelembapan Tanah": "kering", "Cahaya": "terik"}, "then": "lama", "operator": "AND", "label": "Jika tanah kering dan cahaya terik, maka penyiraman lama."},
        ],
        "category": [(0, 10, "pendek"), (10, 20, "sedang"), (20, 30.1, "lama")],
    }


CASES = {
    "Kipas Otomatis": fan_case,
    "Penyiraman Tanaman Otomatis": watering_case,
}


def output_label(value, case):
    for low, high, label in case["category"]:
        if low <= value < high:
            return label
    return case["category"][-1][2]


def fuzzify(case, inputs):
    result = {}
    for input_name, value in inputs.items():
        result[input_name] = {
            set_name: mf_value(value, mf)
            for set_name, mf in case["inputs"][input_name]["sets"].items()
        }
    return result


def rule_alpha(rule, degrees):
    values = [
        degrees[input_name][set_name]
        for input_name, set_name in rule["if"].items()
    ]
    if not values:
        return 0.0
    if rule.get("operator", "AND") == "OR":
        return float(max(values))
    return float(min(values))


def evaluate_control(case, inputs, method="Mamdani", active_rules=None, resolution=501):
    if active_rules is None:
        active_rules = {idx: True for idx in range(len(case["rules"]))}

    degrees = fuzzify(case, inputs)
    output = case["output"]
    x_output = np.linspace(output["range"][0], output["range"][1], resolution)
    aggregated = np.zeros_like(x_output, dtype=float)
    rules_detail = []
    weighted_sum = 0.0
    alpha_sum = 0.0

    for idx, rule in enumerate(case["rules"]):
        alpha_raw = rule_alpha(rule, degrees)
        enabled = bool(active_rules.get(idx, True))
        alpha = alpha_raw if enabled else 0.0
        consequent = rule["then"]
        consequent_mf = mf_curve(x_output, output["sets"][consequent])
        clipped = np.minimum(alpha, consequent_mf)
        aggregated = np.maximum(aggregated, clipped)

        z = output["sugeno"][consequent]
        weighted_sum += alpha * z
        alpha_sum += alpha
        rules_detail.append(
            {
                "No": idx + 1,
                "Aktif": enabled,
                "Aturan": rule["label"],
                "Konsekuen": consequent,
                "Alpha Mentah": alpha_raw,
                "Alpha": alpha,
                "z Sugeno": z,
                "Alpha x z": alpha * z,
            }
        )

    if method == "Sugeno":
        value = weighted_sum / alpha_sum if alpha_sum > 0 else np.mean(output["range"])
    else:
        value = centroid(x_output, aggregated)

    dominant_rule = max(rules_detail, key=lambda row: row["Alpha"])
    return {
        "inputs": inputs,
        "degrees": degrees,
        "x_output": x_output,
        "aggregated": aggregated,
        "rules": rules_detail,
        "value": float(value),
        "label": output_label(float(value), case),
        "dominant_rule": dominant_rule,
        "weighted_sum": weighted_sum,
        "alpha_sum": alpha_sum,
        "method": method,
    }


def rule_table(case):
    rows = []
    for idx, rule in enumerate(case["rules"]):
        rows.append(
            {
                "No": idx + 1,
                "Kondisi": " AND ".join(
                    f"{name} = {set_name}" for name, set_name in rule["if"].items()
                ),
                "Aksi": rule["then"],
                "Aturan": rule["label"],
            }
        )
    return pd.DataFrame(rows)


def surface_grid(case, method, x_name, y_name, fixed_inputs, active_rules=None, n=25):
    x_min, x_max = case["inputs"][x_name]["range"]
    y_min, y_max = case["inputs"][y_name]["range"]
    xs = np.linspace(x_min, x_max, n)
    ys = np.linspace(y_min, y_max, n)
    z = np.zeros((n, n), dtype=float)

    for row, y in enumerate(ys):
        for col, x in enumerate(xs):
            inputs = dict(fixed_inputs)
            inputs[x_name] = float(x)
            inputs[y_name] = float(y)
            z[row, col] = evaluate_control(
                case, inputs, method=method, active_rules=active_rules, resolution=151
            )["value"]
    return xs, ys, z


def narrative(case, result):
    dominant = result["dominant_rule"]
    output_name = case["output"]["name"].lower()
    unit = case["output"]["unit"]
    input_text = ", ".join(
        f"{name} {value:g}{case['inputs'][name]['unit']}"
        for name, value in result["inputs"].items()
    )
    return (
        f"Dengan input {input_text}, aturan paling kuat adalah R{dominant['No']} "
        f"dengan alpha {dominant['Alpha']:.3f}. Sistem menghasilkan {output_name} "
        f"{result['value']:.2f} {unit}, kategori {result['label']}."
    )
