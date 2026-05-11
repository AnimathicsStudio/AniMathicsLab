import numpy as np
import random


def trimf(x, abc):
    """
    Fungsi keanggotaan segitiga.
    abc = [a, b, c]
    Mendukung bahu kiri [0, 0, 5] dan bahu kanan [5, 10, 10].
    """
    a, b, c = abc
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x, dtype=float)

    if a != b:
        idx = (a < x) & (x < b)
        y[idx] = (x[idx] - a) / (b - a)

    if b != c:
        idx = (b < x) & (x < c)
        y[idx] = (c - x[idx]) / (c - b)

    y[x == b] = 1.0

    if a == b:
        y[x == a] = 1.0

    if b == c:
        y[x == c] = 1.0

    return np.clip(y, 0, 1)


def interp_membership(x, mf, value):
    return float(np.interp(value, x, mf))


def build_default_model(step=0.1):
    x_rasa = np.arange(0, 10 + step, step)
    x_pelayanan = np.arange(0, 10 + step, step)
    x_tip = np.arange(0, 25 + step, step)

    rasa = {
        "Tidak Enak": trimf(x_rasa, [0, 0, 5]),
        "Biasa": trimf(x_rasa, [0, 5, 10]),
        "Enak": trimf(x_rasa, [5, 10, 10]),
    }

    pelayanan = {
        "Jutek": trimf(x_pelayanan, [0, 0, 5]),
        "Sopan": trimf(x_pelayanan, [0, 5, 10]),
        "Ramah": trimf(x_pelayanan, [5, 10, 10]),
    }

    tip = {
        "Rendah": trimf(x_tip, [0, 0, 13]),
        "Sedang": trimf(x_tip, [0, 13, 25]),
        "Tinggi": trimf(x_tip, [13, 25, 25]),
    }

    return {
        "x_rasa": x_rasa,
        "x_pelayanan": x_pelayanan,
        "x_tip": x_tip,
        "rasa": rasa,
        "pelayanan": pelayanan,
        "tip": tip,
    }


def area_trapz(y, x):
    """
    Kompatibel untuk NumPy lama dan baru.
    """
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, x)
    return np.trapz(y, x)


def defuzzify(x, mu, method="centroid"):
    method = method.lower()

    if np.max(mu) <= 0:
        return np.nan

    if method == "centroid":
        penyebut = np.sum(mu)
        if penyebut == 0:
            return np.nan
        return float(np.sum(x * mu) / penyebut)

    if method == "bisector":
        area_total = area_trapz(mu, x)
        area_setengah = area_total / 2

        area_kumulatif = np.zeros_like(x)
        for i in range(1, len(x)):
            area_kumulatif[i] = area_kumulatif[i - 1] + area_trapz(
                mu[i - 1:i + 1],
                x[i - 1:i + 1],
            )

        idx = np.searchsorted(area_kumulatif, area_setengah)
        idx = min(idx, len(x) - 1)
        return float(x[idx])

    max_mu = np.max(mu)
    kandidat = x[np.isclose(mu, max_mu)]

    if method == "mom":
        return float(np.mean(kandidat))

    if method == "som":
        return float(np.min(kandidat))

    if method == "lom":
        return float(np.max(kandidat))

    raise ValueError(f"Metode defuzzifikasi tidak dikenal: {method}")


def interpretasi_tip(nilai_tip):
    if np.isnan(nilai_tip):
        return "Tidak terdefinisi"

    if nilai_tip < 8.33:
        return "Tip cenderung rendah"
    elif nilai_tip < 16.67:
        return "Tip cenderung sedang"
    else:
        return "Tip cenderung tinggi"


def label_tip(nilai_tip):
    if np.isnan(nilai_tip):
        return "Tidak terdefinisi"

    if nilai_tip < 8.33:
        return "Rendah"
    elif nilai_tip < 16.67:
        return "Sedang"
    else:
        return "Tinggi"


def default_active_rules():
    return {
        "R1": True,
        "R2": True,
        "R3": True,
    }


def evaluate_mamdani(
    rasa_value,
    pelayanan_value,
    method="centroid",
    active_rules=None,
):
    """
    Menghitung inferensi fuzzy Mamdani untuk kasus penentuan tip.

    Aturan:
    R1: Jika rasa tidak enak ATAU pelayanan jutek, maka tip rendah.
    R2: Jika pelayanan sopan, maka tip sedang.
    R3: Jika rasa enak ATAU pelayanan ramah, maka tip tinggi.
    """
    if active_rules is None:
        active_rules = default_active_rules()

    model = build_default_model()

    x_rasa = model["x_rasa"]
    x_pelayanan = model["x_pelayanan"]
    x_tip = model["x_tip"]

    rasa = model["rasa"]
    pelayanan = model["pelayanan"]
    tip = model["tip"]

    derajat_rasa = {
        nama: interp_membership(x_rasa, mf, rasa_value)
        for nama, mf in rasa.items()
    }

    derajat_pelayanan = {
        nama: interp_membership(x_pelayanan, mf, pelayanan_value)
        for nama, mf in pelayanan.items()
    }

    alpha_1_raw = max(derajat_rasa["Tidak Enak"], derajat_pelayanan["Jutek"])
    alpha_2_raw = derajat_pelayanan["Sopan"]
    alpha_3_raw = max(derajat_rasa["Enak"], derajat_pelayanan["Ramah"])

    alpha_1 = alpha_1_raw if active_rules.get("R1", True) else 0.0
    alpha_2 = alpha_2_raw if active_rules.get("R2", True) else 0.0
    alpha_3 = alpha_3_raw if active_rules.get("R3", True) else 0.0

    cut_1 = np.minimum(alpha_1, tip["Rendah"])
    cut_2 = np.minimum(alpha_2, tip["Sedang"])
    cut_3 = np.minimum(alpha_3, tip["Tinggi"])

    agregasi = np.maximum.reduce([cut_1, cut_2, cut_3])

    tip_tegas = defuzzify(x_tip, agregasi, method=method)
    mu_tip_tegas = (
        interp_membership(x_tip, agregasi, tip_tegas)
        if not np.isnan(tip_tegas)
        else np.nan
    )

    rules = [
        {
            "kode": "R1",
            "aturan": "Jika masakan tidak enak ATAU pelayanan jutek, maka tip rendah.",
            "aktivasi": "max(μ Tidak Enak, μ Jutek)",
            "alpha_raw": alpha_1_raw,
            "alpha": alpha_1,
            "aktif": active_rules.get("R1", True),
            "konsekuen": "Tip Rendah",
        },
        {
            "kode": "R2",
            "aturan": "Jika pelayanan sopan, maka tip sedang.",
            "aktivasi": "μ Sopan",
            "alpha_raw": alpha_2_raw,
            "alpha": alpha_2,
            "aktif": active_rules.get("R2", True),
            "konsekuen": "Tip Sedang",
        },
        {
            "kode": "R3",
            "aturan": "Jika masakan enak ATAU pelayanan ramah, maka tip tinggi.",
            "aktivasi": "max(μ Enak, μ Ramah)",
            "alpha_raw": alpha_3_raw,
            "alpha": alpha_3,
            "aktif": active_rules.get("R3", True),
            "konsekuen": "Tip Tinggi",
        },
    ]

    dominant_rule = max(rules, key=lambda r: r["alpha"])

    return {
        "model": model,
        "rasa_value": rasa_value,
        "pelayanan_value": pelayanan_value,
        "derajat_rasa": derajat_rasa,
        "derajat_pelayanan": derajat_pelayanan,
        "rules": rules,
        "dominant_rule": dominant_rule,
        "cuts": {
            "R1": cut_1,
            "R2": cut_2,
            "R3": cut_3,
        },
        "agregasi": agregasi,
        "tip_tegas": tip_tegas,
        "mu_tip_tegas": mu_tip_tegas,
        "method": method,
        "active_rules": active_rules,
    }


def compare_defuzzification_methods(rasa_value, pelayanan_value, active_rules=None):
    methods = ["centroid", "bisector", "mom", "som", "lom"]
    rows = []

    for method in methods:
        hasil = evaluate_mamdani(
            rasa_value,
            pelayanan_value,
            method=method,
            active_rules=active_rules,
        )
        rows.append({
            "Metode": method.upper(),
            "Nilai Tip": hasil["tip_tegas"],
            "Kategori": label_tip(hasil["tip_tegas"]),
            "Interpretasi": interpretasi_tip(hasil["tip_tegas"]),
        })

    return rows


def decision_grid(n=41, method="centroid", active_rules=None):
    xs = np.linspace(0, 10, n)
    ys = np.linspace(0, 10, n)
    Z = np.zeros((n, n))

    for i, pelayanan in enumerate(ys):
        for j, rasa in enumerate(xs):
            hasil = evaluate_mamdani(
                rasa,
                pelayanan,
                method=method,
                active_rules=active_rules,
            )
            Z[i, j] = hasil["tip_tegas"]

    return xs, ys, Z


def generate_narrative(result):
    rasa_value = result["rasa_value"]
    pelayanan_value = result["pelayanan_value"]
    tip_tegas = result["tip_tegas"]
    dominant_rule = result["dominant_rule"]
    derajat_rasa = result["derajat_rasa"]
    derajat_pelayanan = result["derajat_pelayanan"]

    if np.isnan(tip_tegas):
        return (
            "Tidak ada aturan yang aktif. Karena semua aturan dimatikan atau tidak memberikan "
            "kontribusi, sistem tidak dapat menghasilkan nilai tip tegas."
        )

    rasa_dominan = max(derajat_rasa, key=derajat_rasa.get)
    pelayanan_dominan = max(derajat_pelayanan, key=derajat_pelayanan.get)

    return (
        f"Untuk nilai rasa {rasa_value:.1f}, kategori rasa yang paling dominan adalah "
        f"'{rasa_dominan}' dengan derajat keanggotaan {derajat_rasa[rasa_dominan]:.3f}. "
        f"Untuk nilai pelayanan {pelayanan_value:.1f}, kategori pelayanan yang paling dominan adalah "
        f"'{pelayanan_dominan}' dengan derajat keanggotaan {derajat_pelayanan[pelayanan_dominan]:.3f}. "
        f"Aturan yang paling kuat adalah {dominant_rule['kode']} dengan kekuatan "
        f"{dominant_rule['alpha']:.3f}. Setelah semua output aturan digabung dan didefuzzifikasi "
        f"dengan metode {result['method'].upper()}, sistem menghasilkan tip sebesar "
        f"{tip_tegas:.2f}%, yaitu {interpretasi_tip(tip_tegas).lower()}."
    )


def challenge_bank():
    return [
        {
            "rasa": 2.0,
            "pelayanan": 2.0,
            "pertanyaan": "Rasa kurang baik dan pelayanan juga kurang baik. Menurut Anda, tip akan ke mana?",
        },
        {
            "rasa": 2.0,
            "pelayanan": 9.0,
            "pertanyaan": "Rasa kurang baik, tetapi pelayanan sangat ramah. Apakah tip tetap rendah?",
        },
        {
            "rasa": 8.0,
            "pelayanan": 3.0,
            "pertanyaan": "Rasa enak, tetapi pelayanan kurang memuaskan. Bagaimana kecenderungan tip?",
        },
        {
            "rasa": 5.0,
            "pelayanan": 5.0,
            "pertanyaan": "Keduanya berada di tengah. Apakah sistem menghasilkan tip sedang?",
        },
        {
            "rasa": 9.0,
            "pelayanan": 9.0,
            "pertanyaan": "Rasa dan pelayanan sama-sama tinggi. Seberapa besar tip yang muncul?",
        },
        {
            "rasa": 0.0,
            "pelayanan": 10.0,
            "pertanyaan": "Kasus ekstrem: rasa sangat buruk, pelayanan sangat ramah. Aturan mana yang menang?",
        },
    ]


def random_challenge():
    return random.choice(challenge_bank())


def explanation_for_challenge(result, user_answer=None):
    tip_value = result["tip_tegas"]
    system_label = label_tip(tip_value)
    narrative = generate_narrative(result)

    if user_answer is None:
        return narrative

    if user_answer == system_label:
        pembuka = "Prediksi Anda sesuai dengan hasil sistem."
    else:
        pembuka = (
            f"Prediksi Anda adalah {user_answer}, sedangkan kategori hasil sistem adalah "
            f"{system_label}."
        )
    return f"{pembuka} {narrative}"