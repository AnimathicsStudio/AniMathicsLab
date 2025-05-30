import numpy as np
import pandas as pd
import sympy as sp
from collections import defaultdict
from IPython.display import Latex, display
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
x = sp.symbols("x")

# =================================================================================
# Fungsi Tampilan Matriks LaTeX
# =================================================================================
def LMtx(A, baris=None, kolom=None, koma=None, judul=None):
    R, C = A.shape
    m = R if baris is None else min(baris, R // 2)
    n = C if kolom is None else min(kolom, C // 2)
    full_rows = baris is None or baris * 2 >= R
    full_cols = kolom is None or kolom * 2 >= C

    def format_num(x):
        return f"{x:.{koma}f}" if koma is not None else str(x)

    def fmt(row):
        if full_cols:
            return " & ".join(format_num(x) for x in row)
        return (
            " & ".join(format_num(x) for x in row[:n])
            + " & \\cdots & "
            + " & ".join(format_num(x) for x in row[-n:])
        )

    rows = []
    if full_rows:
        rows = [fmt(row) for row in A]
    else:
        rows += [fmt(A[i]) for i in range(m)]
        if not full_cols:
            dots = " & ".join(["\\vdots"] * n + ["\\ddots"] + ["\\vdots"] * n)
        else:
            dots = " & ".join(["\\vdots"] * C)
        rows.append(dots)
        rows += [fmt(A[-i]) for i in range(m, 0, -1)]

    matrix_name = f"{judul} = " if judul is not None else ""
    latex_code = matrix_name + r"\begin{pmatrix}" + r"\\".join(rows) + r"\end{pmatrix}"
    display(Latex(latex_code))


def LMtx_latex_str(A, baris=None, kolom=None, koma=None, judul=None):
    R, C = A.shape
    m = R if baris is None else min(baris, R // 2)
    n = C if kolom is None else min(kolom, C // 2)
    full_rows = baris is None or baris * 2 >= R
    full_cols = kolom is None or kolom * 2 >= C

    def format_num(x):
        return f"{x:.{koma}f}" if koma is not None else str(x)

    def fmt(row):
        if full_cols:
            return " & ".join(format_num(x) for x in row)
        return (
            " & ".join(format_num(x) for x in row[:n])
            + " & \\cdots & "
            + " & ".join(format_num(x) for x in row[-n:])
        )

    rows = []
    if full_rows:
        rows = [fmt(row) for row in A]
    else:
        rows += [fmt(A[i]) for i in range(m)]
        if not full_cols:
            dots = " & ".join(["\\vdots"] * n + ["\\ddots"] + ["\\vdots"] * n)
        else:
            dots = " & ".join(["\\vdots"] * C)
        rows.append(dots)
        rows += [fmt(A[-i]) for i in range(m, 0, -1)]

    matrix_name = f"{judul} = " if judul is not None else ""
    latex_code = r"\begin{pmatrix}" + r"\\".join(rows) + r"\end{pmatrix}"
    return f"{matrix_name}{latex_code}"


# =================================================================================
# Fungsi Triangular Fuzzy Number (TFN)
# =================================================================================
def TFN(x, a, b, c):
    if a == b:
        return sp.Max(sp.Min(1, (c - x) / (c - b)), 0)
    if b == c:
        return sp.Max(sp.Min((x - a) / (b - a), 1), 0)
    else:
        return sp.Max(sp.Min((x - a) / (b - a), (c - x) / (c - b)), 0)


# =================================================================================
# Fungsi Komposisi Matriks FAM Standar
# =================================================================================
def MaxProd(A, M):
    A = np.array(A)[:, :, None]   # (m, k, 1)
    M = np.array(M)[None, :, :]   # (1, k, n)
    return np.max(A * M, axis=1)

def SumProd(A, B):
    return np.dot(A, B)

def MaxMin(A, M):
    A = np.array(A)[:, :, None]    # (m, k, 1)
    M = np.array(M)[None, :, :]    # (1, k, n)
    return np.max(np.minimum(A, M), axis=1)


# =================================================================================
# Fungsi Membentuk Matriks A, B, M
# =================================================================================
def buat_matriks_A(dfFAM, fitur, TFNVariabel, tampilkan=True):
    baris = dfFAM.shape[0]
    AA = []
    for i in range(baris):
        AAA = [
            [
                round(TFNVariabel[c]["L"](dfFAM.iloc[i][c]), 3),
                round(TFNVariabel[c]["M"](dfFAM.iloc[i][c]), 3),
                round(TFNVariabel[c]["U"](dfFAM.iloc[i][c]), 3),
            ]
            for c in fitur
        ]
        AA.append([item for sublist in AAA for item in sublist])
        if tampilkan:
            Ai = np.array([[f"{x:.2f}" for x in AA[-1]]])
            LMtx(Ai, judul=f"A_{{{i+1}}}")

    A = np.array(AA)
    return A

def buat_matriks_B_M(A, metode="SumProd"):
    baris = A.shape[0]
    B = np.eye(baris)
    LMtx(B, baris=4, kolom=4, judul="B")

    M = []
    for i in range(baris):
        M.append(SumProd(A[i].reshape(-1, 1), B[i].reshape(1, -1)))

    return B, M


# =================================================================================
# Fungsi Norma T dan S (Custom)
# =================================================================================
def fungsi_norma_t(a, b, jenis):
    if jenis == "Minimum":
        return np.minimum(a, b)
    elif jenis == "Produk Algebra":
        return a * b
    elif jenis == "Lukasiewicz":
        return np.maximum(0, a + b - 1)
    elif jenis == "Einstein":
        numerator = a * b
        denominator = 2 - (a + b - a * b)
        denominator = np.where(denominator == 0, 1e-10, denominator)
        return numerator / denominator
    elif jenis == "Hamacher":
        numerator = a * b
        denominator = a + b - a * b
        denominator = np.where(denominator == 0, 1e-10, denominator)
        return numerator / denominator
    else:
        raise ValueError(f"T-norm '{jenis}' belum diimplementasikan")

def fungsi_norma_s(a, b, jenis):
    if jenis == "Maximum":
        return np.maximum(a, b)
    elif jenis == "Probabilistic Sum":
        return a + b - a * b
    elif jenis == "Lukasiewicz":
        return np.minimum(1, a + b)
    elif jenis == "Einstein":
        numerator = a + b
        denominator = 1 + a * b
        denominator = np.where(denominator == 0, 1e-10, denominator)
        return numerator / denominator
    elif jenis == "Hamacher":
        numerator = a + b - 2 * a * b
        denominator = 1 - a * b
        denominator = np.where(denominator == 0, 1e-10, denominator)
        return numerator / denominator
    else:
        raise ValueError(f"S-norm '{jenis}' belum diimplementasikan")

def komposisi_custom(A_mat, M_mat, norma_t="Minimum", norma_s="Maximum"):
    A = np.array(A_mat)[:, :, None]   # (m, k, 1)
    M = np.array(M_mat)[None, :, :]   # (1, k, n)

    comp = fungsi_norma_t(A, M, norma_t)  # (m, k, n)
    hasil = comp[:, 0, :]  # mulai dari k=0
    for k in range(1, comp.shape[1]):
        hasil = fungsi_norma_s(hasil, comp[:, k, :], norma_s)

    return hasil


# =================================================================================
# Fungsi Perhitungan FAM dan Evaluasi
# =================================================================================
def hitung_FAM(dfFAM, fitur, label, TFNVariabel, A, metode="SumProd", norma_t=None, norma_s=None):
    HasilPerhitungan = {}
    baris_sampel = dfFAM.shape[0]

    dictMetode = {
        "SumProd": SumProd,
        "MaxProd": MaxProd,
        "MaxMin": MaxMin,
    }

    if metode != "Custom":
        Komposisi = dictMetode.get(metode, SumProd)
    else:
        if norma_t is None or norma_s is None:
            raise ValueError("Untuk metode custom, norma_t dan norma_s harus ditentukan")
        Komposisi = lambda A_mat, M_mat: komposisi_custom(A_mat, M_mat, norma_t, norma_s)

    beda = 0
    for i in range(baris_sampel):
        nilai_komposisi = Komposisi([A[i]], A.T)
        idx = np.argmax(nilai_komposisi)

        StatusAsli = dfFAM.loc[dfFAM.index[i], label]
        StatusPrediksi = dfFAM.loc[dfFAM.index[idx], label]

        if StatusAsli != StatusPrediksi:
            beda += 1
        HasilPerhitungan[i] = StatusPrediksi

    Akurasi = (baris_sampel - beda) / baris_sampel * 100

    hasil_df = pd.DataFrame({
        "Index": dfFAM.index,
        "Status Asli": dfFAM[label].iloc[:baris_sampel],
        "Status Prediksi": [HasilPerhitungan[i] for i in range(baris_sampel)],
        "Sama/Tidak": [
            "✅" if dfFAM[label].iloc[i] == HasilPerhitungan[i] else "❌"
            for i in range(baris_sampel)
        ]
    })

    return hasil_df, Akurasi


# =================================================================================
# Fungsi Ekstraksi dan Penyaringan Aturan Fuzzy
# =================================================================================
def ekstrak_aturan(dfFAM, fitur, label, TFNVariabel):
    rules = []

    for i, row in dfFAM.iterrows():
        antecedents = []
        memberships = []
        for f in fitur:
            nilai = row[f]
            mems = {
                'L': TFNVariabel[f]['L'](nilai),
                'M': TFNVariabel[f]['M'](nilai),
                'U': TFNVariabel[f]['U'](nilai)
            }
            max_kategori = max(mems, key=mems.get)
            antecedents.append(max_kategori)
            memberships.append(mems[max_kategori])

        consequent = row[label]
        rule_degree = np.prod(memberships)

        rule_tuple = tuple(antecedents) + (consequent, rule_degree)
        rules.append(rule_tuple)

    # Hapus aturan kontradiksi
    rule_dict = defaultdict(list)
    for rule in rules:
        antecedent = rule[:-2]
        consequent = rule[-2]
        degree = rule[-1]
        rule_dict[antecedent].append((consequent, degree))

    final_rules = []
    for antecedent, conseq_degrees in rule_dict.items():
        best_consequent, best_degree = max(conseq_degrees, key=lambda x: x[1])
        final_rules.append(antecedent + (best_consequent, best_degree))

    print(f"Total aturan final (kontradiksi diselesaikan): {len(final_rules)}")
    for fr in sorted(final_rules):
        print(fr)

    return final_rules


# =================================================================================
# Fungsi Bantu untuk Load dan Preprocessing Data
# =================================================================================
def ambil_nama_sheet(file):
    xls = pd.ExcelFile(file)
    return xls.sheet_names

def muat_sheet(file, nama_sheet):
    df = pd.read_excel(file, sheet_name=nama_sheet).dropna()
    return df

def bersihkan_ubah_numerik(df, fitur):
    df_copy = df.copy()
    for col in fitur:
        df_copy[col] = df_copy[col].astype(str).str.replace('\xa0', '').str.strip()
        df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
    return df_copy


# =================================================================================
# Fungsi Membuat Variabel TFN
# =================================================================================
def buat_TFN_variabel(df, fitur):
    def TFN(x, a, b, c):
        if a == b:
            return sp.Max(sp.Min(1, (c - x) / (c - b)), 0)
        if b == c:
            return sp.Max(sp.Min((x - a) / (b - a), 1), 0)
        else:
            return sp.Max(sp.Min((x - a) / (b - a), (c - x) / (c - b)), 0)

    TFNVariabel = {}
    for kol in fitur:
        data = df[kol]
        a, b, c = float(data.min()), (float(data.max()) + float(data.min())) / 2, float(data.max())
        TFNVariabel[kol] = {
            "L": sp.lambdify(x, TFN(x, a, a, b), modules="numpy"),
            "M": sp.lambdify(x, TFN(x, a, b, c), modules="numpy"),
            "U": sp.lambdify(x, TFN(x, b, c, c), modules="numpy")
        }
    return TFNVariabel


# =================================================================================
# Fungsi Plot TFN
# =================================================================================
def plot_TFN(dfFAM, fitur, TFNVariabel):
    plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
    Kol = fitur
    labels = [f"$({chr(97+i)})$" for i in range(len(fitur))]
    fig, ax = plt.subplots(2, 2, figsize=(10, 6), dpi=300)
    ax = ax.flat

    for i, kol in enumerate(Kol):
        a, b = float(dfFAM[kol].min()), float(dfFAM[kol].max())
        x_vals = np.linspace(a - (b - a) / 2, b + (b - a) / 2, 500)

        TFN_L = TFNVariabel[kol]["L"]
        TFN_M = TFNVariabel[kol]["M"]
        TFN_U = TFNVariabel[kol]["U"]

        ax[i].plot(x_vals, [TFN_L(val) for val in x_vals], label="$Rendah$", color="#ff0000", linewidth=2)
        ax[i].plot(x_vals, [TFN_M(val) for val in x_vals], label="$Sedang$", color="orange", linewidth=2)
        ax[i].plot(x_vals, [TFN_U(val) for val in x_vals], label="$Tinggi$", color="green", linewidth=2)

        ax[i].set_xlabel("$x$", fontsize=20)
        ax[i].xaxis.set_label_coords(1.0, 0.0)
        ax[i].set_ylabel(rf"$\mu_{{\mathrm{{{kol}}}}}(x)$", fontsize=16, labelpad=5)
        ax[i].set_title(f"Fungsi Keanggotaan: {kol}", fontsize=12, pad=10)
        ax[i].legend(fontsize=10)
        ax[i].text(0.5, -0.1, labels[i], transform=ax[i].transAxes, fontsize=16, va="top", ha="center")

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0.2, hspace=0.5)
    fig.patch.set_alpha(0)

    return fig
