import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go

from tsukamoto_engine import (
    evaluate_tsukamoto,
    interpretasi_tip,
    label_tip,
    decision_grid,
    generate_narrative,
    random_challenge,
    explanation_for_challenge,
)

from tsukamoto_plot import (
    plot_rasa,
    plot_pelayanan,
    plot_tip_membership,
    plot_rule_inverse,
    plot_tsukamoto_points,
    plot_weighted_contribution,
)


# ============================================================
# KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="Tsukamoto Fuzzy Playground",
    page_icon="🧠",
    layout="wide",
)


# ============================================================
# FUNGSI BANTU
# ============================================================

@st.cache_data
def cached_decision_grid(n, r1, r2, r3):
    active_rules = {"R1": r1, "R2": r2, "R3": r3}
    return decision_grid(n=n, active_rules=active_rules)


def metric_card(label, value, help_text=None):
    st.metric(label, value, help=help_text)


def tsukamoto_note():
    return {
        "inti": "Pada Tsukamoto, setiap konsekuen aturan harus berupa himpunan fuzzy monoton. Dari kekuatan aturan αᵢ, kita cari nilai crisp zᵢ melalui invers fungsi keanggotaan.",
        "rumus": r"z^*=\frac{\sum \alpha_i z_i}{\sum \alpha_i}",
        "catatan": "Tsukamoto mirip Sugeno pada rumus akhir, tetapi zᵢ tidak diberikan langsung sebagai fungsi tegas. zᵢ dicari dari konsekuen fuzzy monoton.",
    }


def rule_card(rule, dominant_code):
    aktif = rule["aktif"]
    alpha = rule["alpha"]

    is_dominant = rule["kode"] == dominant_code and alpha > 0

    border = "#d97706" if is_dominant else "#d1d5db"
    bg = "#fff7ed" if is_dominant else "#ffffff"
    status = "Aktif" if aktif else "Dimatikan"
    status_color = "#15803d" if aktif else "#dc2626"
    badge = "Aturan dominan" if is_dominant else "Aturan"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background: transparent;
            }}

            .card {{
                border: 2px solid {border};
                border-radius: 18px;
                padding: 20px;
                background-color: {bg};
                color: #111827;
                min-height: 330px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.12);
                box-sizing: border-box;
            }}

            .kode {{
                font-size: 30px;
                font-weight: 800;
                margin-bottom: 4px;
                color: #111827;
            }}

            .badge {{
                display: inline-block;
                font-size: 12px;
                font-weight: 700;
                color: #92400e;
                background: #fed7aa;
                padding: 4px 8px;
                border-radius: 999px;
                margin-bottom: 10px;
            }}

            .status {{
                font-size: 14px;
                font-weight: 700;
                color: {status_color};
                margin-bottom: 12px;
            }}

            .aturan {{
                font-size: 15px;
                line-height: 1.45;
                margin-bottom: 14px;
                color: #111827;
            }}

            .label {{
                font-size: 13px;
                font-weight: 700;
                margin-top: 10px;
                color: #374151;
            }}

            .code {{
                display: inline-block;
                font-family: Consolas, monospace;
                font-size: 13px;
                color: #111827;
                background-color: #e5e7eb;
                padding: 4px 8px;
                border-radius: 8px;
                margin-top: 4px;
            }}

            .nilai {{
                font-size: 15px;
                font-weight: 700;
                color: #111827;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="kode">{rule['kode']}</div>
            <div class="badge">{badge}</div>
            <div class="status">{status}</div>

            <div class="aturan">
                {rule['aturan']}
            </div>

            <div class="label">Aktivasi</div>
            <div class="code">{rule['aktivasi']}</div>

            <div class="label">Konsekuen Tsukamoto</div>
            <div class="code">{rule['konsekuen']}</div>

            <div class="label">Invers konsekuen</div>
            <div class="code">{rule['inverse_text']}</div>

            <div class="label">Kekuatan aturan αᵢ</div>
            <div class="nilai">{rule['alpha']:.3f}</div>

            <div class="label">Output aturan zᵢ</div>
            <div class="nilai">{rule['z']:.3f}</div>

            <div class="label">Kontribusi αᵢzᵢ</div>
            <div class="nilai">{rule['alpha_z']:.3f}</div>
        </div>
    </body>
    </html>
    """

    components.html(html, height=420)


# ============================================================
# JUDUL APLIKASI
# ============================================================

st.title("🧠 Tsukamoto Fuzzy Playground")
st.caption(
    "Belajar inferensi fuzzy Tsukamoto: fuzzifikasi, aktivasi aturan, invers konsekuen monoton, dan rata-rata berbobot."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("🎛️ Panel Kontrol")

    st.markdown("### Input Kasus")

    preset = st.selectbox(
        "Preset kasus",
        [
            "Custom",
            "Rasa buruk, pelayanan buruk",
            "Rasa buruk, pelayanan baik",
            "Rasa enak, pelayanan buruk",
            "Rasa sedang, pelayanan sedang",
            "Rasa enak, pelayanan baik",
        ],
    )

    preset_values = {
        "Custom": (4.0, 8.0),
        "Rasa buruk, pelayanan buruk": (2.0, 2.0),
        "Rasa buruk, pelayanan baik": (2.0, 9.0),
        "Rasa enak, pelayanan buruk": (8.0, 3.0),
        "Rasa sedang, pelayanan sedang": (5.0, 5.0),
        "Rasa enak, pelayanan baik": (9.0, 9.0),
    }

    default_rasa, default_pelayanan = preset_values[preset]

    rasa_value = st.slider(
        "Nilai rasa masakan",
        min_value=0.0,
        max_value=10.0,
        value=default_rasa,
        step=0.1,
    )

    pelayanan_value = st.slider(
        "Nilai pelayanan",
        min_value=0.0,
        max_value=10.0,
        value=default_pelayanan,
        step=0.1,
    )

    st.divider()

    st.markdown("### Inti Tsukamoto")

    note = tsukamoto_note()

    with st.expander("ℹ️ Apa ciri khas Tsukamoto?"):
        st.markdown(note["inti"])
        st.latex(note["rumus"])
        st.caption(note["catatan"])

    st.divider()

    st.markdown("### Rule Switch")

    r1_on = st.checkbox("R1: buruk → tip rendah", value=True)
    r2_on = st.checkbox("R2: cukup → tip sedang", value=True)
    r3_on = st.checkbox("R3: baik → tip tinggi", value=True)

    active_rules = {
        "R1": r1_on,
        "R2": r2_on,
        "R3": r3_on,
    }

    st.divider()

    st.markdown("### Mode Presentasi")

    presenter_level = st.slider(
        "Buka proses sampai tahap ke-",
        min_value=1,
        max_value=5,
        value=5,
        step=1,
        help="Gunakan ini saat mengajar. Naikkan pelan-pelan dari fuzzifikasi sampai rata-rata berbobot.",
    )


# ============================================================
# EVALUASI SISTEM TSUKAMOTO
# ============================================================

result = evaluate_tsukamoto(
    rasa_value=rasa_value,
    pelayanan_value=pelayanan_value,
    active_rules=active_rules,
)

tip_tegas = result["tip_tegas"]
interpretasi = interpretasi_tip(tip_tegas)
kategori = label_tip(tip_tegas)
dominant_code = result["dominant_rule"]["kode"]


# ============================================================
# RINGKASAN HASIL
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    metric_card("Rasa", f"{rasa_value:.1f} / 10")

with col2:
    metric_card("Pelayanan", f"{pelayanan_value:.1f} / 10")

with col3:
    if pd.isna(tip_tegas):
        metric_card("Tip akhir", "Tidak ada")
    else:
        metric_card("Tip akhir", f"{tip_tegas:.2f}%")

with col4:
    metric_card("Kategori", kategori)


# ============================================================
# TAB UTAMA
# ============================================================

tab_story, tab_step, tab_experiment, tab_map, tab_quiz = st.tabs(
    [
        "📖 Cerita",
        "🪜 Step-by-Step",
        "🧪 Eksperimen",
        "🗺️ Peta Keputusan",
        "🎯 Kuis",
    ]
)


# ============================================================
# TAB 1: CERITA
# ============================================================

with tab_story:
    st.subheader("📖 Cerita Kasus")

    st.markdown(
        f"""
        Anda makan di sebuah restoran. Setelah selesai makan, Anda ingin menentukan besar tip yang wajar.

        Sistem menerima dua input:

        - **Rasa masakan**: `{rasa_value:.1f}` dari `10`
        - **Pelayanan**: `{pelayanan_value:.1f}` dari `10`

        Pada Tsukamoto, output setiap aturan masih berupa himpunan fuzzy, tetapi himpunan fuzzy konsekuennya harus **monoton**.
        Karena monoton, setiap kekuatan aturan $\\alpha_i$ dapat dipakai untuk mencari satu nilai crisp $z_i$.
        """
    )

    st.subheader("🧠 Narasi Otomatis Sistem")

    st.info(generate_narrative(result))

    st.subheader("📌 Basis Aturan Tsukamoto")

    st.markdown(
        r"""
        Sistem Tsukamoto ini memakai tiga aturan:

        1. **R1:** Jika masakan tidak enak ATAU pelayanan buruk, maka **tip rendah**.  
           Konsekuen rendah dibuat monoton turun, sehingga:
        """
    )
    st.latex(r"\mu_{\text{rendah}}(z_1)=\alpha_1")

    st.markdown(
        r"""
        2. **R2:** Jika pelayanan cukup, maka **tip sedang**.  
           Konsekuen sedang dibuat monoton naik berbentuk kurva S, sehingga:
        """
    )
    st.latex(r"\mu_{\text{sedang}}(z_2)=\alpha_2")

    st.markdown(
        r"""
        3. **R3:** Jika masakan enak ATAU pelayanan baik, maka **tip tinggi**.  
           Konsekuen tinggi dibuat monoton naik, sehingga:
        """
    )
    st.latex(r"\mu_{\text{tinggi}}(z_3)=\alpha_3")

    st.warning(
        "Poin penting: Tsukamoto tidak langsung mengambil luas daerah fuzzy seperti Mamdani. "
        "Setiap aturan menghasilkan satu zᵢ melalui invers konsekuen monoton, lalu semua zᵢ dirata-ratakan berbobot."
    )


# ============================================================
# TAB 2: STEP-BY-STEP
# ============================================================

with tab_step:
    st.subheader("🪜 Inferensi Tsukamoto Langkah demi Langkah")

    st.markdown(
        """
        Gunakan slider **Mode Presentasi** di sidebar untuk membuka proses secara bertahap.
        """
    )

    tahap = [
        "1. Fuzzifikasi input",
        "2. Aktivasi aturan",
        "3. Cari zᵢ dari invers konsekuen",
        "4. Hitung kontribusi αᵢzᵢ",
        "5. Rata-rata berbobot",
    ]

    st.progress(presenter_level / 5)
    st.caption("Tahap terbuka: " + ", ".join(tahap[:presenter_level]))

    if presenter_level >= 1:
        st.markdown("---")
        st.subheader("1. Fuzzifikasi Input")

        st.info(
            "Fuzzifikasi mengubah input tegas menjadi derajat keanggotaan pada beberapa himpunan fuzzy."
        )

        col_a, col_b = st.columns(2)

        with col_a:
            st.pyplot(plot_rasa(result), use_container_width=True)

        with col_b:
            st.pyplot(plot_pelayanan(result), use_container_width=True)

        df_rasa = pd.DataFrame(
            {
                "Himpunan Fuzzy": list(result["derajat_rasa"].keys()),
                "Derajat Keanggotaan": list(result["derajat_rasa"].values()),
            }
        )

        df_pelayanan = pd.DataFrame(
            {
                "Himpunan Fuzzy": list(result["derajat_pelayanan"].keys()),
                "Derajat Keanggotaan": list(result["derajat_pelayanan"].values()),
            }
        )

        col_c, col_d = st.columns(2)

        with col_c:
            st.markdown("#### Rasa")
            st.dataframe(
                df_rasa.style.format({"Derajat Keanggotaan": "{:.3f}"}),
                use_container_width=True,
                hide_index=True,
            )

        with col_d:
            st.markdown("#### Pelayanan")
            st.dataframe(
                df_pelayanan.style.format({"Derajat Keanggotaan": "{:.3f}"}),
                use_container_width=True,
                hide_index=True,
            )

    if presenter_level >= 2:
        st.markdown("---")
        st.subheader("2. Aktivasi Aturan")

        st.info(
            "Setiap aturan memiliki kekuatan aktivasi αᵢ. Pada Tsukamoto, αᵢ akan dipakai untuk mencari zᵢ dari konsekuen monoton."
        )

        df_rules = pd.DataFrame(result["rules"])
        df_rules = df_rules.rename(
            columns={
                "kode": "Kode",
                "aturan": "Aturan",
                "aktivasi": "Aktivasi",
                "alpha_raw": "Kekuatan Mentah",
                "alpha": "Kekuatan Dipakai αᵢ",
                "z": "Output zᵢ",
                "alpha_z": "Kontribusi αᵢzᵢ",
                "aktif": "Status Aktif",
                "konsekuen": "Konsekuen",
            }
        )

        st.dataframe(
            df_rules[
                [
                    "Kode",
                    "Status Aktif",
                    "Aturan",
                    "Aktivasi",
                    "Kekuatan Mentah",
                    "Kekuatan Dipakai αᵢ",
                    "Konsekuen",
                    "Output zᵢ",
                    "Kontribusi αᵢzᵢ",
                ]
            ].style.format(
                {
                    "Kekuatan Mentah": "{:.3f}",
                    "Kekuatan Dipakai αᵢ": "{:.3f}",
                    "Output zᵢ": "{:.3f}",
                    "Kontribusi αᵢzᵢ": "{:.3f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        cols = st.columns(3)

        for col, rule in zip(cols, result["rules"]):
            with col:
                rule_card(rule, dominant_code)

    if presenter_level >= 3:
        st.markdown("---")
        st.subheader("3. Cari zᵢ dari Invers Konsekuen")

        st.info(
            "Inilah bagian khas Tsukamoto. Karena konsekuen monoton, persamaan μ(zᵢ)=αᵢ dapat dibalik untuk mendapatkan zᵢ."
        )

        st.pyplot(plot_tip_membership(result), use_container_width=True)

        col_r1, col_r2, col_r3 = st.columns(3)

        with col_r1:
            st.pyplot(plot_rule_inverse(result, "R1"), use_container_width=True)

        with col_r2:
            st.pyplot(plot_rule_inverse(result, "R2"), use_container_width=True)

        with col_r3:
            st.pyplot(plot_rule_inverse(result, "R3"), use_container_width=True)

        df_z = pd.DataFrame(
            [
                {
                    "Aturan": r["kode"],
                    "Konsekuen": r["konsekuen"],
                    "αᵢ": r["alpha"],
                    "Cara mencari zᵢ": r["inverse_text"],
                    "zᵢ": r["z"],
                }
                for r in result["rules"]
            ]
        )

        st.dataframe(
            df_z.style.format(
                {
                    "αᵢ": "{:.3f}",
                    "zᵢ": "{:.3f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    if presenter_level >= 4:
        st.markdown("---")
        st.subheader("4. Hitung Kontribusi αᵢzᵢ")

        st.info(
            "Setelah zᵢ diperoleh, setiap zᵢ dikalikan dengan bobot αᵢ. "
            "Aturan yang lebih kuat memberi kontribusi lebih besar."
        )

        df_contrib = pd.DataFrame(
            [
                {
                    "Aturan": r["kode"],
                    "αᵢ": r["alpha"],
                    "zᵢ": r["z"],
                    "αᵢzᵢ": r["alpha_z"],
                }
                for r in result["rules"]
            ]
        )

        st.dataframe(
            df_contrib.style.format(
                {
                    "αᵢ": "{:.3f}",
                    "zᵢ": "{:.3f}",
                    "αᵢzᵢ": "{:.3f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.pyplot(plot_weighted_contribution(result), use_container_width=True)

    if presenter_level >= 5:
        st.markdown("---")
        st.subheader("5. Rata-Rata Berbobot")

        col_left, col_right = st.columns([1.2, 1])

        with col_left:
            if pd.isna(tip_tegas):
                st.error(
                    "Tidak ada nilai tip tegas karena tidak ada aturan yang memberikan kontribusi."
                )
            else:
                st.success(
                    f"Nilai akhir Tsukamoto adalah **{tip_tegas:.2f}%**. "
                    f"Interpretasinya: **{interpretasi}**."
                )

            st.markdown(
                r"""
                Pada Tsukamoto, hasil akhir dihitung dengan rata-rata berbobot:

                $$
                z^*=\frac{\alpha_1z_1+\alpha_2z_2+\alpha_3z_3}
                {\alpha_1+\alpha_2+\alpha_3}
                $$

                Atau secara umum:

                $$
                z^*=\frac{\sum \alpha_i z_i}{\sum \alpha_i}
                $$
                """
            )

            st.markdown(
                f"""
                Dalam kasus ini:

                - pembilang = **{result['pembilang']:.3f}**
                - penyebut = **{result['penyebut']:.3f}**
                """
            )

        with col_right:
            st.pyplot(plot_tsukamoto_points(result), use_container_width=True)


# ============================================================
# TAB 3: EKSPERIMEN
# ============================================================

with tab_experiment:
    st.subheader("🧪 Eksperimen")

    st.markdown(
        """
        Bagian ini digunakan untuk melihat bagaimana aturan Tsukamoto membentuk output akhir.
        Coba aktifkan/nonaktifkan aturan dari sidebar, lalu amati perubahan nilai tip.
        """
    )

    with st.expander("📌 Ringkasan Mamdani, Sugeno, dan Tsukamoto"):
        st.markdown(
            r"""
| Aspek | Mamdani | Sugeno | Tsukamoto |
|---|---|---|---|
| Konsekuen aturan | Himpunan fuzzy | Fungsi tegas/konstanta | Himpunan fuzzy monoton |
| Output tiap aturan | Daerah fuzzy terpotong | Angka zᵢ langsung | Angka zᵢ dari invers konsekuen |
| Syarat konsekuen monoton | Tidak wajib | Tidak relevan | Wajib |
| Agregasi akhir | Gabungan daerah fuzzy | Rata-rata berbobot | Rata-rata berbobot |
| Ide utama | Bentuk daerah output | Fungsi output aturan | Balik nilai α menjadi zᵢ |
            """
        )

        st.info(
            "Cara cepat membedakan: Mamdani membentuk daerah fuzzy, Sugeno memberi rumus zᵢ langsung, "
            "sedangkan Tsukamoto mencari zᵢ dari konsekuen fuzzy yang monoton."
        )

    st.markdown("### Tabel Perhitungan Tsukamoto")

    df_calc = pd.DataFrame(
        [
            {
                "Aturan": r["kode"],
                "Aktif": r["aktif"],
                "αᵢ": r["alpha"],
                "zᵢ": r["z"],
                "αᵢzᵢ": r["alpha_z"],
            }
            for r in result["rules"]
        ]
    )

    st.dataframe(
        df_calc.style.format(
            {
                "αᵢ": "{:.3f}",
                "zᵢ": "{:.3f}",
                "αᵢzᵢ": "{:.3f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Pertanyaan Reflektif")

    dominant_rule = result["dominant_rule"]

    st.info(
        f"""
        Saat ini aturan paling dominan adalah **{dominant_rule['kode']}**
        dengan kekuatan **{dominant_rule['alpha']:.3f}**.

        Coba lakukan eksperimen berikut:

        1. Matikan aturan **{dominant_rule['kode']}** dari sidebar.
        2. Perhatikan perubahan nilai tip akhir.
        3. Bandingkan: apakah nilai akhir mendekati zᵢ dari aturan yang paling kuat?
        """
    )

    st.markdown("### Skenario Cepat")

    st.markdown(
        """
        Gunakan pilihan **Preset kasus** di sidebar untuk mencoba beberapa situasi ekstrem:

        - rasa buruk dan pelayanan buruk,
        - rasa buruk tetapi pelayanan baik,
        - rasa enak tetapi pelayanan buruk,
        - rasa dan pelayanan sama-sama sedang,
        - rasa dan pelayanan sama-sama tinggi.
        """
    )


# ============================================================
# TAB 4: PETA KEPUTUSAN
# ============================================================

with tab_map:
    st.subheader("🗺️ Peta Keputusan")

    st.markdown(
        """
        Peta ini menunjukkan bagaimana nilai tip Tsukamoto berubah untuk berbagai kombinasi
        rasa dan pelayanan. Titik merah menunjukkan posisi input saat ini.
        """
    )

    n_grid = st.slider(
        "Resolusi peta keputusan",
        min_value=21,
        max_value=81,
        value=41,
        step=10,
    )

    xs, ys, Z = cached_decision_grid(
        n_grid,
        r1_on,
        r2_on,
        r3_on,
    )

    heatmap = go.Figure()

    heatmap.add_trace(
        go.Heatmap(
            z=Z,
            x=xs,
            y=ys,
            colorbar=dict(title="Tip (%)"),
        )
    )

    heatmap.add_trace(
        go.Scatter(
            x=[rasa_value],
            y=[pelayanan_value],
            mode="markers+text",
            marker=dict(size=14, color="red", symbol="x"),
            text=["Input saat ini"],
            textposition="top center",
            name="Input saat ini",
        )
    )

    heatmap.update_layout(
        title="Heatmap Nilai Tip Tsukamoto",
        xaxis_title="Rasa Masakan",
        yaxis_title="Pelayanan",
        height=620,
    )

    st.plotly_chart(heatmap, use_container_width=True)

    with st.expander("Tampilkan surface 3D"):
        surface = go.Figure(
            data=[
                go.Surface(
                    z=Z,
                    x=xs,
                    y=ys,
                    colorbar=dict(title="Tip (%)"),
                )
            ]
        )

        if not pd.isna(tip_tegas):
            surface.add_trace(
                go.Scatter3d(
                    x=[rasa_value],
                    y=[pelayanan_value],
                    z=[tip_tegas],
                    mode="markers+text",
                    marker=dict(size=6, color="red"),
                    text=["Input"],
                    name="Input saat ini",
                )
            )

        surface.update_layout(
            title="Permukaan Keputusan Tsukamoto",
            scene=dict(
                xaxis_title="Rasa",
                yaxis_title="Pelayanan",
                zaxis_title="Tip (%)",
            ),
            height=720,
        )

        st.plotly_chart(surface, use_container_width=True)


# ============================================================
# TAB 5: KUIS
# ============================================================

with tab_quiz:
    st.subheader("🎯 Mode Tantangan")

    if "challenge" not in st.session_state:
        st.session_state.challenge = random_challenge()

    if st.button("🎲 Ambil kasus baru", use_container_width=True):
        st.session_state.challenge = random_challenge()

    challenge = st.session_state.challenge

    ch_rasa = challenge["rasa"]
    ch_pelayanan = challenge["pelayanan"]

    challenge_result = evaluate_tsukamoto(
        rasa_value=ch_rasa,
        pelayanan_value=ch_pelayanan,
        active_rules=active_rules,
    )

    st.markdown(
        f"""
        ### Kasus

        {challenge['pertanyaan']}

        - Rasa masakan: **{ch_rasa:.1f}**
        - Pelayanan: **{ch_pelayanan:.1f}**
        """
    )

    user_answer = st.radio(
        "Menurut Anda, kategori tip akhirnya apa?",
        ["Rendah", "Sedang", "Tinggi"],
        horizontal=True,
    )

    show_answer = st.button("Lihat jawaban Tsukamoto", use_container_width=True)

    if show_answer:
        ch_tip = challenge_result["tip_tegas"]
        ch_label = label_tip(ch_tip)

        if pd.isna(ch_tip):
            st.error("Sistem tidak menghasilkan nilai tip karena tidak ada aturan yang aktif.")
        else:
            st.success(
                f"Hasil sistem: **{ch_tip:.2f}%**, kategori **{ch_label}**."
            )

        st.info(
            explanation_for_challenge(
                challenge_result,
                user_answer=user_answer,
            )
        )

        col_ch1, col_ch2 = st.columns(2)

        with col_ch1:
            st.pyplot(plot_rasa(challenge_result), use_container_width=True)

        with col_ch2:
            st.pyplot(plot_pelayanan(challenge_result), use_container_width=True)

        st.pyplot(plot_tsukamoto_points(challenge_result), use_container_width=True)

    else:
        st.warning(
            "Tebak dulu hasilnya, lalu klik tombol untuk melihat jawaban sistem Tsukamoto."
        )