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

    rasa = {
        "Tidak Enak": trimf(x_rasa, [0, 0, 5]),
        "Biasa": trimf(x_rasa, [0, 5, 10]),
        "Enak": trimf(x_rasa, [5, 10, 10]),
    }

    pelayanan = {
        "Buruk": trimf(x_pelayanan, [0, 0, 5]),
        "Cukup": trimf(x_pelayanan, [0, 5, 10]),
        "Baik": trimf(x_pelayanan, [5, 10, 10]),
    }

    return {
        "x_rasa": x_rasa,
        "x_pelayanan": x_pelayanan,
        "rasa": rasa,
        "pelayanan": pelayanan,
    }


def default_active_rules():
    return {
        "R1": True,
        "R2": True,
        "R3": True,
    }


def konsekuen_r1(rasa_value, pelayanan_value):
    return 0.5 * rasa_value + pelayanan_value


def konsekuen_r2(rasa_value, pelayanan_value):
    return 2 * pelayanan_value


def konsekuen_r3(rasa_value, pelayanan_value):
    return 0.5 * (rasa_value + pelayanan_value) + 15


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


def evaluate_sugeno(
    rasa_value,
    pelayanan_value,
    active_rules=None,
):
    """
    Inferensi fuzzy Sugeno untuk kasus penentuan tip.

    R1:
    Jika masakan tidak enak ATAU pelayanan buruk,
    maka z1 = 1/2 rasa + pelayanan.

    R2:
    Jika pelayanan cukup,
    maka z2 = 2 pelayanan.

    R3:
    Jika masakan enak ATAU pelayanan baik,
    maka z3 = 1/2(rasa + pelayanan) + 15.
    """
    if active_rules is None:
        active_rules = default_active_rules()

    model = build_default_model()

    x_rasa = model["x_rasa"]
    x_pelayanan = model["x_pelayanan"]

    rasa = model["rasa"]
    pelayanan = model["pelayanan"]

    derajat_rasa = {
        nama: interp_membership(x_rasa, mf, rasa_value)
        for nama, mf in rasa.items()
    }

    derajat_pelayanan = {
        nama: interp_membership(x_pelayanan, mf, pelayanan_value)
        for nama, mf in pelayanan.items()
    }

    alpha_1_raw = max(
        derajat_rasa["Tidak Enak"],
        derajat_pelayanan["Buruk"],
    )

    alpha_2_raw = derajat_pelayanan["Cukup"]

    alpha_3_raw = max(
        derajat_rasa["Enak"],
        derajat_pelayanan["Baik"],
    )

    alpha_1 = alpha_1_raw if active_rules.get("R1", True) else 0.0
    alpha_2 = alpha_2_raw if active_rules.get("R2", True) else 0.0
    alpha_3 = alpha_3_raw if active_rules.get("R3", True) else 0.0

    z1 = konsekuen_r1(rasa_value, pelayanan_value)
    z2 = konsekuen_r2(rasa_value, pelayanan_value)
    z3 = konsekuen_r3(rasa_value, pelayanan_value)

    pembilang = alpha_1 * z1 + alpha_2 * z2 + alpha_3 * z3
    penyebut = alpha_1 + alpha_2 + alpha_3

    if penyebut == 0:
        z_final = np.nan
    else:
        z_final = pembilang / penyebut

    rules = [
        {
            "kode": "R1",
            "aturan": "Jika masakan tidak enak ATAU pelayanan buruk, maka z₁ = 1/2 rasa + pelayanan.",
            "aktivasi": "max(μ Tidak Enak, μ Buruk)",
            "alpha_raw": alpha_1_raw,
            "alpha": alpha_1,
            "z": z1,
            "alpha_z": alpha_1 * z1,
            "aktif": active_rules.get("R1", True),
            "konsekuen": "z₁ = 1/2 rasa + pelayanan",
        },
        {
            "kode": "R2",
            "aturan": "Jika pelayanan cukup, maka z₂ = 2 × pelayanan.",
            "aktivasi": "μ Cukup",
            "alpha_raw": alpha_2_raw,
            "alpha": alpha_2,
            "z": z2,
            "alpha_z": alpha_2 * z2,
            "aktif": active_rules.get("R2", True),
            "konsekuen": "z₂ = 2 × pelayanan",
        },
        {
            "kode": "R3",
            "aturan": "Jika masakan enak ATAU pelayanan baik, maka z₃ = 1/2(rasa + pelayanan) + 15.",
            "aktivasi": "max(μ Enak, μ Baik)",
            "alpha_raw": alpha_3_raw,
            "alpha": alpha_3,
            "z": z3,
            "alpha_z": alpha_3 * z3,
            "aktif": active_rules.get("R3", True),
            "konsekuen": "z₃ = 1/2(rasa + pelayanan) + 15",
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
        "pembilang": pembilang,
        "penyebut": penyebut,
        "tip_tegas": float(z_final) if not np.isnan(z_final) else np.nan,
        "active_rules": active_rules,
    }


def generate_narrative(result):
    rasa_value = result["rasa_value"]
    pelayanan_value = result["pelayanan_value"]
    tip_tegas = result["tip_tegas"]
    dominant_rule = result["dominant_rule"]

    derajat_rasa = result["derajat_rasa"]
    derajat_pelayanan = result["derajat_pelayanan"]

    if np.isnan(tip_tegas):
        return (
            "Tidak ada aturan yang aktif. Karena semua kekuatan aturan bernilai nol, "
            "sistem Sugeno tidak dapat menghitung rata-rata berbobot."
        )

    rasa_dominan = max(derajat_rasa, key=derajat_rasa.get)
    pelayanan_dominan = max(derajat_pelayanan, key=derajat_pelayanan.get)

    return (
        f"Untuk nilai rasa {rasa_value:.1f}, kategori rasa yang paling dominan adalah "
        f"'{rasa_dominan}' dengan derajat {derajat_rasa[rasa_dominan]:.3f}. "
        f"Untuk nilai pelayanan {pelayanan_value:.1f}, kategori pelayanan yang paling dominan adalah "
        f"'{pelayanan_dominan}' dengan derajat {derajat_pelayanan[pelayanan_dominan]:.3f}. "
        f"Aturan yang paling kuat adalah {dominant_rule['kode']} dengan kekuatan "
        f"{dominant_rule['alpha']:.3f}. Pada Sugeno, setiap aturan menghasilkan nilai tegas zᵢ. "
        f"Nilai akhir diperoleh dari rata-rata berbobot semua zᵢ, yaitu {tip_tegas:.2f}%. "
        f"Interpretasinya: {interpretasi_tip(tip_tegas).lower()}."
    )


def decision_grid(n=41, active_rules=None):
    xs = np.linspace(0, 10, n)
    ys = np.linspace(0, 10, n)
    Z = np.zeros((n, n))

    for i, pelayanan in enumerate(ys):
        for j, rasa in enumerate(xs):
            hasil = evaluate_sugeno(
                rasa,
                pelayanan,
                active_rules=active_rules,
            )
            Z[i, j] = hasil["tip_tegas"]

    return xs, ys, Z


def challenge_bank():
    return [
        {
            "rasa": 2.0,
            "pelayanan": 2.0,
            "pertanyaan": "Rasa kurang baik dan pelayanan juga buruk. Menurut Anda, tip akan cenderung ke mana?",
        },
        {
            "rasa": 2.0,
            "pelayanan": 9.0,
            "pertanyaan": "Rasa kurang baik, tetapi pelayanan baik. Bagaimana efek rata-rata berbobot Sugeno?",
        },
        {
            "rasa": 8.0,
            "pelayanan": 3.0,
            "pertanyaan": "Rasa enak, tetapi pelayanan kurang baik. Aturan mana yang lebih memengaruhi?",
        },
        {
            "rasa": 5.0,
            "pelayanan": 5.0,
            "pertanyaan": "Keduanya berada di tengah. Apakah output Sugeno menjadi sedang?",
        },
        {
            "rasa": 9.0,
            "pelayanan": 9.0,
            "pertanyaan": "Rasa dan pelayanan sama-sama tinggi. Seberapa besar nilai tip Sugeno?",
        },
        {
            "rasa": 0.0,
            "pelayanan": 10.0,
            "pertanyaan": "Kasus ekstrem: rasa sangat buruk, pelayanan sangat baik. Bagaimana rata-rata berbobotnya?",
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