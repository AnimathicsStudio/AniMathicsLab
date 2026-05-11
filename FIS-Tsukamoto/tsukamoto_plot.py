import numpy as np
import matplotlib.pyplot as plt


def beautify(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle=":", alpha=0.7)
    ax.set_ylim(-0.05, 1.05)


def plot_rasa(result):
    model = result["model"]
    x = model["x_rasa"]
    rasa = model["rasa"]
    value = result["rasa_value"]
    derajat = result["derajat_rasa"]

    fig, ax = plt.subplots(figsize=(7, 4))

    for nama, mf in rasa.items():
        ax.plot(x, mf, linewidth=2, label=nama)
        ax.scatter([value], [derajat[nama]], s=45)

    ax.axvline(value, linestyle="--", linewidth=1.5)
    ax.set_title("Fuzzifikasi Variabel Rasa")
    ax.set_xlabel("Nilai rasa")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 10)
    ax.legend()
    beautify(ax)

    return fig


def plot_pelayanan(result):
    model = result["model"]
    x = model["x_pelayanan"]
    pelayanan = model["pelayanan"]
    value = result["pelayanan_value"]
    derajat = result["derajat_pelayanan"]

    fig, ax = plt.subplots(figsize=(7, 4))

    for nama, mf in pelayanan.items():
        ax.plot(x, mf, linewidth=2, label=nama)
        ax.scatter([value], [derajat[nama]], s=45)

    ax.axvline(value, linestyle="--", linewidth=1.5)
    ax.set_title("Fuzzifikasi Variabel Pelayanan")
    ax.set_xlabel("Nilai pelayanan")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 10)
    ax.legend()
    beautify(ax)

    return fig


def plot_tip_membership(result):
    model = result["model"]
    x = model["x_tip"]
    tip = model["tip"]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    for nama, mf in tip.items():
        ax.plot(x, mf, linewidth=2, label=f"Tip {nama}")

    ax.set_title("Konsekuen Monoton pada Metode Tsukamoto")
    ax.set_xlabel("Tip (%)")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 25)
    ax.legend()
    beautify(ax)

    return fig


def plot_rule_inverse(result, rule_code):
    model = result["model"]
    x = model["x_tip"]
    tip = model["tip"]

    rule = next(r for r in result["rules"] if r["kode"] == rule_code)

    mf = tip[rule["output_key"]]
    alpha = rule["alpha"]
    z = rule["z"]

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.plot(x, mf, linewidth=2, label=rule["konsekuen"])

    ax.axhline(alpha, linestyle="--", linewidth=1.5)
    ax.axvline(z, linestyle="--", linewidth=1.5)
    ax.scatter([z], [alpha], s=80)

    ax.text(
        z,
        min(alpha + 0.08, 1.02),
        f"z = {z:.2f}\nα = {alpha:.2f}",
        ha="center",
    )

    ax.set_title(f"{rule_code}: Cari z dari α pada {rule['konsekuen']}")
    ax.set_xlabel("Tip (%)")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 25)
    ax.legend()
    beautify(ax)

    return fig


def plot_tsukamoto_points(result):
    rules = result["rules"]

    labels = [r["kode"] for r in rules]
    z_values = [r["z"] for r in rules]
    alpha_values = [r["alpha"] for r in rules]
    tip_final = result["tip_tegas"]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    ax.scatter(z_values, alpha_values, s=140)

    for label, z, alpha in zip(labels, z_values, alpha_values):
        ax.text(
            z,
            alpha + 0.04,
            f"{label}\nz={z:.2f}\nα={alpha:.2f}",
            ha="center",
        )

    if not np.isnan(tip_final):
        ax.axvline(tip_final, linewidth=2, linestyle="--")
        ax.text(tip_final, 1.04, f"z* = {tip_final:.2f}", ha="center")

    ax.set_title("Titik Crisp zᵢ dari Setiap Aturan Tsukamoto")
    ax.set_xlabel("Nilai output aturan zᵢ")
    ax.set_ylabel("Kekuatan aturan αᵢ")
    ax.set_xlim(0, 25)
    ax.set_ylim(-0.05, 1.15)
    ax.grid(True, linestyle=":", alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return fig


def plot_weighted_contribution(result):
    rules = result["rules"]

    labels = [r["kode"] for r in rules]
    values = [r["alpha_z"] for r in rules]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    ax.bar(labels, values)

    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom")

    ax.set_title("Kontribusi Berbobot αᵢzᵢ")
    ax.set_xlabel("Aturan")
    ax.set_ylabel("Kontribusi αᵢzᵢ")
    ax.grid(True, axis="y", linestyle=":", alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return fig