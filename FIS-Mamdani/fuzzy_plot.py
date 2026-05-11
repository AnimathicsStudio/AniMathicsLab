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

    fig, ax = plt.subplots(figsize=(7, 4))

    for nama, mf in tip.items():
        ax.plot(x, mf, linewidth=2, label=f"Tip {nama}")

    ax.set_title("Fungsi Keanggotaan Output Tip")
    ax.set_xlabel("Tip (%)")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 25)
    ax.legend()
    beautify(ax)

    return fig


def plot_rule_cut(result, rule_code):
    model = result["model"]
    x = model["x_tip"]
    tip = model["tip"]
    cut = result["cuts"][rule_code]

    rule = next(r for r in result["rules"] if r["kode"] == rule_code)
    konsekuen = rule["konsekuen"].replace("Tip ", "")

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.plot(x, tip[konsekuen], linestyle="--", linewidth=2, label=rule["konsekuen"])
    ax.fill_between(x, np.zeros_like(x), cut, alpha=0.45)

    ax.set_title(f"{rule_code}: Output Terpotong, α = {rule['alpha']:.3f}")
    ax.set_xlabel("Tip (%)")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 25)
    ax.legend()
    beautify(ax)

    return fig


def plot_aggregation(result):
    model = result["model"]
    x = model["x_tip"]
    tip = model["tip"]
    agregasi = result["agregasi"]
    tip_tegas = result["tip_tegas"]
    mu_tip_tegas = result["mu_tip_tegas"]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    for nama, mf in tip.items():
        ax.plot(x, mf, linestyle="--", linewidth=1.5, label=f"Tip {nama}")

    ax.fill_between(x, np.zeros_like(x), agregasi, alpha=0.5, label="Agregasi")

    if not np.isnan(tip_tegas):
        ax.axvline(tip_tegas, linewidth=2)
        ax.scatter([tip_tegas], [mu_tip_tegas], s=60)
        ax.text(
            tip_tegas,
            mu_tip_tegas + 0.08,
            f"{tip_tegas:.2f}%",
            ha="center",
            fontsize=10,
        )

    ax.set_title("Agregasi dan Defuzzifikasi")
    ax.set_xlabel("Tip (%)")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 25)
    ax.legend()
    beautify(ax)

=======
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

    fig, ax = plt.subplots(figsize=(7, 4))

    for nama, mf in tip.items():
        ax.plot(x, mf, linewidth=2, label=f"Tip {nama}")

    ax.set_title("Fungsi Keanggotaan Output Tip")
    ax.set_xlabel("Tip (%)")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 25)
    ax.legend()
    beautify(ax)

    return fig


def plot_rule_cut(result, rule_code):
    model = result["model"]
    x = model["x_tip"]
    tip = model["tip"]
    cut = result["cuts"][rule_code]

    rule = next(r for r in result["rules"] if r["kode"] == rule_code)
    konsekuen = rule["konsekuen"].replace("Tip ", "")

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.plot(x, tip[konsekuen], linestyle="--", linewidth=2, label=rule["konsekuen"])
    ax.fill_between(x, np.zeros_like(x), cut, alpha=0.45)

    ax.set_title(f"{rule_code}: Output Terpotong, α = {rule['alpha']:.3f}")
    ax.set_xlabel("Tip (%)")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 25)
    ax.legend()
    beautify(ax)

    return fig


def plot_aggregation(result):
    model = result["model"]
    x = model["x_tip"]
    tip = model["tip"]
    agregasi = result["agregasi"]
    tip_tegas = result["tip_tegas"]
    mu_tip_tegas = result["mu_tip_tegas"]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    for nama, mf in tip.items():
        ax.plot(x, mf, linestyle="--", linewidth=1.5, label=f"Tip {nama}")

    ax.fill_between(x, np.zeros_like(x), agregasi, alpha=0.5, label="Agregasi")

    if not np.isnan(tip_tegas):
        ax.axvline(tip_tegas, linewidth=2)
        ax.scatter([tip_tegas], [mu_tip_tegas], s=60)
        ax.text(
            tip_tegas,
            mu_tip_tegas + 0.08,
            f"{tip_tegas:.2f}%",
            ha="center",
            fontsize=10,
        )

    ax.set_title("Agregasi dan Defuzzifikasi")
    ax.set_xlabel("Tip (%)")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 25)
    ax.legend()
    beautify(ax)

    return fig