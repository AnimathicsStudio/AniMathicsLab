import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go

from fuzzy_engine import (
    evaluate_mamdani,
    interpretasi_tip,
    label_tip,
    compare_defuzzification_methods,
    decision_grid,
    generate_narrative,
    random_challenge,
    explanation_for_challenge,
)

from fuzzy_plot import (
    plot_rasa,
    plot_pelayanan,
    plot_tip_membership,
    plot_rule_cut,
    plot_aggregation,
)


# ============================================================
# KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="Mamdani Fuzzy Playground",
    page_icon="🧠",
    layout="wide",
)


# ============================================================
# FUNGSI BANTU
# ============================================================

@st.cache_data
def cached_decision_grid(n, method, r1, r2, r3):
    active_rules = {"R1": r1, "R2": r2, "R3": r3}
    return decision_grid(n=n, method=method, active_rules=active_rules)


def metric_card(label, value, help_text=None):
    st.metric(label, value, help=help_text)


def defuzz_method_note(method):
    notes = {
        "centroid": {
            "nama": "Centroid",
            "intuisi": "Mengambil titik pusat massa dari daerah fuzzy hasil agregasi.",
            "rumus": r"z^*=\frac{\sum z_i\mu(z_i)}{\sum \mu(z_i)}",
            "catatan": "Memperhatikan seluruh bentuk daerah fuzzy. Biasanya paling stabil dan paling sering digunakan.",
        },
        "bisector": {
            "nama": "Bisector",
            "intuisi": "Mencari titik yang membagi luas daerah fuzzy menjadi dua bagian sama besar.",
            "rumus": r"\int_a^{z^*}\mu(z)\,dz=\int_{z^*}^{b}\mu(z)\,dz",
            "catatan": "Fokus pada pembagian luas, bukan pusat massa.",
        },
        "mom": {
            "nama": "MOM",
            "intuisi": "Mengambil rata-rata dari semua titik yang mencapai derajat keanggotaan maksimum.",
            "rumus": r"z^*=\frac{1}{|M|}\sum_{z\in M}z",
            "catatan": "Hanya memperhatikan bagian puncak tertinggi.",
        },
        "som": {
            "nama": "SOM",
            "intuisi": "Mengambil titik paling kecil dari semua titik yang mencapai maksimum.",
            "rumus": r"z^*=\min M",
            "catatan": "Cenderung memilih nilai output yang lebih konservatif.",
        },
        "lom": {
            "nama": "LOM",
            "intuisi": "Mengambil titik paling besar dari semua titik yang mencapai maksimum.",
            "rumus": r"z^*=\max M",
            "catatan": "Cenderung memilih nilai output yang lebih besar.",
        },
    }

    return notes[method]


def rule_card(rule, dominant_code):
    aktif = rule["aktif"]
    alpha = rule["alpha"]

    is_dominant = rule["kode"] == dominant_code and alpha > 0

    border = "#2563eb" if is_dominant else "#d1d5db"
    bg = "#eff6ff" if is_dominant else "#ffffff"
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
                min-height: 250px;
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
                color: #1d4ed8;
                background: #dbeafe;
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

            <div class="label">Kekuatan mentah</div>
            <div class="nilai">{rule['alpha_raw']:.3f}</div>

            <div class="label">Kekuatan dipakai</div>
            <div class="nilai">{rule['alpha']:.3f}</div>
        </div>
    </body>
    </html>
    """

    components.html(html, height=330)


# ============================================================
# JUDUL APLIKASI
# ============================================================

st.title("🧠 Mamdani Fuzzy Playground")
st.caption("Belajar inferensi fuzzy dengan menggeser, melihat, menebak, dan membandingkan.")


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
            "Rasa buruk, pelayanan ramah",
            "Rasa enak, pelayanan buruk",
            "Rasa sedang, pelayanan sedang",
            "Rasa enak, pelayanan ramah",
        ],
    )

    preset_values = {
        "Custom": (4.0, 8.0),
        "Rasa buruk, pelayanan buruk": (2.0, 2.0),
        "Rasa buruk, pelayanan ramah": (2.0, 9.0),
        "Rasa enak, pelayanan buruk": (8.0, 3.0),
        "Rasa sedang, pelayanan sedang": (5.0, 5.0),
        "Rasa enak, pelayanan ramah": (9.0, 9.0),
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

    st.markdown("### Metode Defuzzifikasi")

    method = st.selectbox(
        "Pilih metode",
        options=["centroid", "bisector", "mom", "som", "lom"],
        index=0,
    )

    note = defuzz_method_note(method)

    with st.expander("ℹ️ Apa arti metode ini?"):
        st.markdown(f"**{note['nama']}**")
        st.markdown(note["intuisi"])
        st.latex(note["rumus"])
        st.caption(note["catatan"])

    st.divider()

    st.markdown("### Rule Switch")

    r1_on = st.checkbox("R1: buruk/jutek → tip rendah", value=True)
    r2_on = st.checkbox("R2: sopan → tip sedang", value=True)
    r3_on = st.checkbox("R3: enak/ramah → tip tinggi", value=True)

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
        help="Gunakan ini saat mengajar. Naikkan pelan-pelan dari fuzzifikasi sampai defuzzifikasi.",
    )

    show_rule_plots = st.checkbox("Tampilkan grafik output tiap aturan", value=True)


# ============================================================
# EVALUASI SISTEM FUZZY
# ============================================================

result = evaluate_mamdani(
    rasa_value=rasa_value,
    pelayanan_value=pelayanan_value,
    method=method,
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
        Anda makan di sebuah restoran. Setelah selesai makan, Anda ingin menentukan
        besar tip yang wajar.

        Sistem menerima dua input:

        - **Rasa masakan**: `{rasa_value:.1f}` dari `10`
        - **Pelayanan**: `{pelayanan_value:.1f}` dari `10`

        Output yang ingin dicari adalah **besar tip**, dalam rentang `0%` sampai `25%`.
        """
    )

    st.subheader("🧠 Narasi Otomatis Sistem")

    st.info(generate_narrative(result))

    st.subheader("📌 Basis Aturan")

    st.markdown(
        """
        Sistem Mamdani ini memakai tiga aturan:

        1. **R1**: Jika masakan tidak enak ATAU pelayanan jutek, maka tip rendah.
        2. **R2**: Jika pelayanan sopan, maka tip sedang.
        3. **R3**: Jika masakan enak ATAU pelayanan ramah, maka tip tinggi.
        """
    )

    st.warning(
        "Poin penting: dalam sistem fuzzy, beberapa aturan dapat aktif secara bersamaan. "
        "Jadi sistem tidak memilih satu aturan saja, tetapi menggabungkan kontribusi semua aturan yang aktif."
    )


# ============================================================
# TAB 2: STEP-BY-STEP
# ============================================================

with tab_step:
    st.subheader("🪜 Inferensi Mamdani Langkah demi Langkah")

    st.markdown(
        """
        Gunakan slider **Mode Presentasi** di sidebar untuk membuka proses secara bertahap.
        """
    )

    tahap = [
        "1. Fuzzifikasi input",
        "2. Aktivasi aturan",
        "3. Implikasi output tiap aturan",
        "4. Agregasi output",
        "5. Defuzzifikasi",
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
            "Setiap aturan memiliki kekuatan aktivasi. Semakin besar nilainya, semakin kuat aturan itu memengaruhi output."
        )

        df_rules = pd.DataFrame(result["rules"])
        df_rules = df_rules.rename(
            columns={
                "kode": "Kode",
                "aturan": "Aturan",
                "aktivasi": "Aktivasi",
                "alpha_raw": "Kekuatan Mentah",
                "alpha": "Kekuatan Dipakai",
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
                    "Kekuatan Dipakai",
                    "Konsekuen",
                ]
            ].style.format(
                {
                    "Kekuatan Mentah": "{:.3f}",
                    "Kekuatan Dipakai": "{:.3f}",
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
        st.subheader("3. Implikasi Output Tiap Aturan")

        st.info(
            "Pada Mamdani, kekuatan aturan digunakan untuk memotong fungsi keanggotaan output."
        )

        if show_rule_plots:
            col_r1, col_r2, col_r3 = st.columns(3)

            with col_r1:
                st.pyplot(plot_rule_cut(result, "R1"), use_container_width=True)

            with col_r2:
                st.pyplot(plot_rule_cut(result, "R2"), use_container_width=True)

            with col_r3:
                st.pyplot(plot_rule_cut(result, "R3"), use_container_width=True)
        else:
            st.info("Grafik output tiap aturan disembunyikan. Aktifkan dari sidebar.")

    if presenter_level >= 4:
        st.markdown("---")
        st.subheader("4. Agregasi Output")

        st.info(
            "Setelah setiap aturan menghasilkan output terpotong, semua output digabungkan. "
            "Pada Mamdani, penggabungan biasanya menggunakan operator maksimum."
        )

        st.pyplot(plot_aggregation(result), use_container_width=True)

    if presenter_level >= 5:
        st.markdown("---")
        st.subheader("5. Defuzzifikasi")

        col_left, col_right = st.columns([1.2, 1])

        with col_left:
            if pd.isna(tip_tegas):
                st.error(
                    "Tidak ada nilai tip tegas karena tidak ada aturan yang memberikan kontribusi."
                )
            else:
                st.success(
                    f"Dengan metode **{method.upper()}**, nilai tip tegas adalah "
                    f"**{tip_tegas:.2f}%**. Interpretasinya: **{interpretasi}**."
                )

            st.markdown(
                """
                Defuzzifikasi mengubah daerah fuzzy hasil agregasi menjadi satu nilai tegas.
                Nilai inilah yang menjadi keputusan akhir sistem.
                """
            )

            note = defuzz_method_note(method)

            st.markdown("### Metode yang sedang dipakai")
            st.markdown(f"**{note['nama']}** — {note['intuisi']}")
            st.latex(note["rumus"])
            st.caption(note["catatan"])

        with col_right:
            st.pyplot(plot_tip_membership(result), use_container_width=True)


# ============================================================
# TAB 3: EKSPERIMEN
# ============================================================

with tab_experiment:
    st.subheader("🧪 Eksperimen")

    st.markdown(
        """
        Bagian ini digunakan untuk membandingkan pengaruh metode defuzzifikasi dan aturan.
        Coba aktifkan/nonaktifkan aturan dari sidebar, lalu amati perubahan nilai tip.
        """
    )

    with st.expander("📌 Ringkasan metode defuzzifikasi"):
        st.markdown(
            """
| Metode | Intuisi utama | Yang diperhatikan |
|---|---|---|
| Centroid | Titik pusat massa | Seluruh bentuk daerah |
| Bisector | Pembagi luas menjadi dua | Luas kiri dan kanan |
| MOM | Rata-rata titik maksimum | Puncak tertinggi |
| SOM | Titik maksimum paling kiri | Puncak tertinggi, pilihan kecil |
| LOM | Titik maksimum paling kanan | Puncak tertinggi, pilihan besar |
            """
        )

        st.info(
            "Centroid dan bisector melihat seluruh daerah fuzzy. "
            "MOM, SOM, dan LOM hanya melihat bagian yang mencapai nilai maksimum."
        )

    st.markdown("### Perbandingan Metode Defuzzifikasi")

    df_compare = pd.DataFrame(
        compare_defuzzification_methods(
            rasa_value,
            pelayanan_value,
            active_rules=active_rules,
        )
    )

    st.dataframe(
        df_compare.style.format({"Nilai Tip": "{:.3f}"}),
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
        3. Jelaskan mengapa nilai tip berubah atau tidak berubah terlalu banyak.
        """
    )

    st.markdown("### Skenario Cepat")

    st.markdown(
        """
        Gunakan pilihan **Preset kasus** di sidebar untuk mencoba beberapa situasi ekstrem:

        - rasa buruk dan pelayanan buruk,
        - rasa buruk tetapi pelayanan ramah,
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
        Peta ini menunjukkan bagaimana nilai tip berubah untuk berbagai kombinasi
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
        method,
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
        title="Heatmap Nilai Tip",
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
            title="Permukaan Keputusan Mamdani",
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

    challenge_result = evaluate_mamdani(
        rasa_value=ch_rasa,
        pelayanan_value=ch_pelayanan,
        method=method,
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

    show_answer = st.button("Lihat jawaban Mamdani", use_container_width=True)

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

        st.pyplot(plot_aggregation(challenge_result), use_container_width=True)

    else:
        st.warning(
            "Tebak dulu hasilnya, lalu klik tombol untuk melihat jawaban sistem Mamdani."
=======
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go

from fuzzy_engine import (
    evaluate_mamdani,
    interpretasi_tip,
    label_tip,
    compare_defuzzification_methods,
    decision_grid,
    generate_narrative,
    random_challenge,
    explanation_for_challenge,
)

from fuzzy_plot import (
    plot_rasa,
    plot_pelayanan,
    plot_tip_membership,
    plot_rule_cut,
    plot_aggregation,
)


# ============================================================
# KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="Mamdani Fuzzy Playground",
    page_icon="🧠",
    layout="wide",
)


# ============================================================
# FUNGSI BANTU
# ============================================================

@st.cache_data
def cached_decision_grid(n, method, r1, r2, r3):
    active_rules = {"R1": r1, "R2": r2, "R3": r3}
    return decision_grid(n=n, method=method, active_rules=active_rules)


def metric_card(label, value, help_text=None):
    st.metric(label, value, help=help_text)


def defuzz_method_note(method):
    notes = {
        "centroid": {
            "nama": "Centroid",
            "intuisi": "Mengambil titik pusat massa dari daerah fuzzy hasil agregasi.",
            "rumus": r"z^*=\frac{\sum z_i\mu(z_i)}{\sum \mu(z_i)}",
            "catatan": "Memperhatikan seluruh bentuk daerah fuzzy. Biasanya paling stabil dan paling sering digunakan.",
        },
        "bisector": {
            "nama": "Bisector",
            "intuisi": "Mencari titik yang membagi luas daerah fuzzy menjadi dua bagian sama besar.",
            "rumus": r"\int_a^{z^*}\mu(z)\,dz=\int_{z^*}^{b}\mu(z)\,dz",
            "catatan": "Fokus pada pembagian luas, bukan pusat massa.",
        },
        "mom": {
            "nama": "MOM",
            "intuisi": "Mengambil rata-rata dari semua titik yang mencapai derajat keanggotaan maksimum.",
            "rumus": r"z^*=\frac{1}{|M|}\sum_{z\in M}z",
            "catatan": "Hanya memperhatikan bagian puncak tertinggi.",
        },
        "som": {
            "nama": "SOM",
            "intuisi": "Mengambil titik paling kecil dari semua titik yang mencapai maksimum.",
            "rumus": r"z^*=\min M",
            "catatan": "Cenderung memilih nilai output yang lebih konservatif.",
        },
        "lom": {
            "nama": "LOM",
            "intuisi": "Mengambil titik paling besar dari semua titik yang mencapai maksimum.",
            "rumus": r"z^*=\max M",
            "catatan": "Cenderung memilih nilai output yang lebih besar.",
        },
    }

    return notes[method]


def rule_card(rule, dominant_code):
    aktif = rule["aktif"]
    alpha = rule["alpha"]

    is_dominant = rule["kode"] == dominant_code and alpha > 0

    border = "#2563eb" if is_dominant else "#d1d5db"
    bg = "#eff6ff" if is_dominant else "#ffffff"
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
                min-height: 250px;
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
                color: #1d4ed8;
                background: #dbeafe;
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

            <div class="label">Kekuatan mentah</div>
            <div class="nilai">{rule['alpha_raw']:.3f}</div>

            <div class="label">Kekuatan dipakai</div>
            <div class="nilai">{rule['alpha']:.3f}</div>
        </div>
    </body>
    </html>
    """

    components.html(html, height=330)


# ============================================================
# JUDUL APLIKASI
# ============================================================

st.title("🧠 Mamdani Fuzzy Playground")
st.caption("Belajar inferensi fuzzy dengan menggeser, melihat, menebak, dan membandingkan.")


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
            "Rasa buruk, pelayanan ramah",
            "Rasa enak, pelayanan buruk",
            "Rasa sedang, pelayanan sedang",
            "Rasa enak, pelayanan ramah",
        ],
    )

    preset_values = {
        "Custom": (4.0, 8.0),
        "Rasa buruk, pelayanan buruk": (2.0, 2.0),
        "Rasa buruk, pelayanan ramah": (2.0, 9.0),
        "Rasa enak, pelayanan buruk": (8.0, 3.0),
        "Rasa sedang, pelayanan sedang": (5.0, 5.0),
        "Rasa enak, pelayanan ramah": (9.0, 9.0),
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

    st.markdown("### Metode Defuzzifikasi")

    method = st.selectbox(
        "Pilih metode",
        options=["centroid", "bisector", "mom", "som", "lom"],
        index=0,
    )

    note = defuzz_method_note(method)

    with st.expander("ℹ️ Apa arti metode ini?"):
        st.markdown(f"**{note['nama']}**")
        st.markdown(note["intuisi"])
        st.latex(note["rumus"])
        st.caption(note["catatan"])

    st.divider()

    st.markdown("### Rule Switch")

    r1_on = st.checkbox("R1: buruk/jutek → tip rendah", value=True)
    r2_on = st.checkbox("R2: sopan → tip sedang", value=True)
    r3_on = st.checkbox("R3: enak/ramah → tip tinggi", value=True)

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
        help="Gunakan ini saat mengajar. Naikkan pelan-pelan dari fuzzifikasi sampai defuzzifikasi.",
    )

    show_rule_plots = st.checkbox("Tampilkan grafik output tiap aturan", value=True)


# ============================================================
# EVALUASI SISTEM FUZZY
# ============================================================

result = evaluate_mamdani(
    rasa_value=rasa_value,
    pelayanan_value=pelayanan_value,
    method=method,
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
        Anda makan di sebuah restoran. Setelah selesai makan, Anda ingin menentukan
        besar tip yang wajar.

        Sistem menerima dua input:

        - **Rasa masakan**: `{rasa_value:.1f}` dari `10`
        - **Pelayanan**: `{pelayanan_value:.1f}` dari `10`

        Output yang ingin dicari adalah **besar tip**, dalam rentang `0%` sampai `25%`.
        """
    )

    st.subheader("🧠 Narasi Otomatis Sistem")

    st.info(generate_narrative(result))

    st.subheader("📌 Basis Aturan")

    st.markdown(
        """
        Sistem Mamdani ini memakai tiga aturan:

        1. **R1**: Jika masakan tidak enak ATAU pelayanan jutek, maka tip rendah.
        2. **R2**: Jika pelayanan sopan, maka tip sedang.
        3. **R3**: Jika masakan enak ATAU pelayanan ramah, maka tip tinggi.
        """
    )

    st.warning(
        "Poin penting: dalam sistem fuzzy, beberapa aturan dapat aktif secara bersamaan. "
        "Jadi sistem tidak memilih satu aturan saja, tetapi menggabungkan kontribusi semua aturan yang aktif."
    )


# ============================================================
# TAB 2: STEP-BY-STEP
# ============================================================

with tab_step:
    st.subheader("🪜 Inferensi Mamdani Langkah demi Langkah")

    st.markdown(
        """
        Gunakan slider **Mode Presentasi** di sidebar untuk membuka proses secara bertahap.
        """
    )

    tahap = [
        "1. Fuzzifikasi input",
        "2. Aktivasi aturan",
        "3. Implikasi output tiap aturan",
        "4. Agregasi output",
        "5. Defuzzifikasi",
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
            "Setiap aturan memiliki kekuatan aktivasi. Semakin besar nilainya, semakin kuat aturan itu memengaruhi output."
        )

        df_rules = pd.DataFrame(result["rules"])
        df_rules = df_rules.rename(
            columns={
                "kode": "Kode",
                "aturan": "Aturan",
                "aktivasi": "Aktivasi",
                "alpha_raw": "Kekuatan Mentah",
                "alpha": "Kekuatan Dipakai",
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
                    "Kekuatan Dipakai",
                    "Konsekuen",
                ]
            ].style.format(
                {
                    "Kekuatan Mentah": "{:.3f}",
                    "Kekuatan Dipakai": "{:.3f}",
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
        st.subheader("3. Implikasi Output Tiap Aturan")

        st.info(
            "Pada Mamdani, kekuatan aturan digunakan untuk memotong fungsi keanggotaan output."
        )

        if show_rule_plots:
            col_r1, col_r2, col_r3 = st.columns(3)

            with col_r1:
                st.pyplot(plot_rule_cut(result, "R1"), use_container_width=True)

            with col_r2:
                st.pyplot(plot_rule_cut(result, "R2"), use_container_width=True)

            with col_r3:
                st.pyplot(plot_rule_cut(result, "R3"), use_container_width=True)
        else:
            st.info("Grafik output tiap aturan disembunyikan. Aktifkan dari sidebar.")

    if presenter_level >= 4:
        st.markdown("---")
        st.subheader("4. Agregasi Output")

        st.info(
            "Setelah setiap aturan menghasilkan output terpotong, semua output digabungkan. "
            "Pada Mamdani, penggabungan biasanya menggunakan operator maksimum."
        )

        st.pyplot(plot_aggregation(result), use_container_width=True)

    if presenter_level >= 5:
        st.markdown("---")
        st.subheader("5. Defuzzifikasi")

        col_left, col_right = st.columns([1.2, 1])

        with col_left:
            if pd.isna(tip_tegas):
                st.error(
                    "Tidak ada nilai tip tegas karena tidak ada aturan yang memberikan kontribusi."
                )
            else:
                st.success(
                    f"Dengan metode **{method.upper()}**, nilai tip tegas adalah "
                    f"**{tip_tegas:.2f}%**. Interpretasinya: **{interpretasi}**."
                )

            st.markdown(
                """
                Defuzzifikasi mengubah daerah fuzzy hasil agregasi menjadi satu nilai tegas.
                Nilai inilah yang menjadi keputusan akhir sistem.
                """
            )

            note = defuzz_method_note(method)

            st.markdown("### Metode yang sedang dipakai")
            st.markdown(f"**{note['nama']}** — {note['intuisi']}")
            st.latex(note["rumus"])
            st.caption(note["catatan"])

        with col_right:
            st.pyplot(plot_tip_membership(result), use_container_width=True)


# ============================================================
# TAB 3: EKSPERIMEN
# ============================================================

with tab_experiment:
    st.subheader("🧪 Eksperimen")

    st.markdown(
        """
        Bagian ini digunakan untuk membandingkan pengaruh metode defuzzifikasi dan aturan.
        Coba aktifkan/nonaktifkan aturan dari sidebar, lalu amati perubahan nilai tip.
        """
    )

    with st.expander("📌 Ringkasan metode defuzzifikasi"):
        st.markdown(
            """
| Metode | Intuisi utama | Yang diperhatikan |
|---|---|---|
| Centroid | Titik pusat massa | Seluruh bentuk daerah |
| Bisector | Pembagi luas menjadi dua | Luas kiri dan kanan |
| MOM | Rata-rata titik maksimum | Puncak tertinggi |
| SOM | Titik maksimum paling kiri | Puncak tertinggi, pilihan kecil |
| LOM | Titik maksimum paling kanan | Puncak tertinggi, pilihan besar |
            """
        )

        st.info(
            "Centroid dan bisector melihat seluruh daerah fuzzy. "
            "MOM, SOM, dan LOM hanya melihat bagian yang mencapai nilai maksimum."
        )

    st.markdown("### Perbandingan Metode Defuzzifikasi")

    df_compare = pd.DataFrame(
        compare_defuzzification_methods(
            rasa_value,
            pelayanan_value,
            active_rules=active_rules,
        )
    )

    st.dataframe(
        df_compare.style.format({"Nilai Tip": "{:.3f}"}),
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
        3. Jelaskan mengapa nilai tip berubah atau tidak berubah terlalu banyak.
        """
    )

    st.markdown("### Skenario Cepat")

    st.markdown(
        """
        Gunakan pilihan **Preset kasus** di sidebar untuk mencoba beberapa situasi ekstrem:

        - rasa buruk dan pelayanan buruk,
        - rasa buruk tetapi pelayanan ramah,
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
        Peta ini menunjukkan bagaimana nilai tip berubah untuk berbagai kombinasi
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
        method,
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
        title="Heatmap Nilai Tip",
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
            title="Permukaan Keputusan Mamdani",
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

    challenge_result = evaluate_mamdani(
        rasa_value=ch_rasa,
        pelayanan_value=ch_pelayanan,
        method=method,
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

    show_answer = st.button("Lihat jawaban Mamdani", use_container_width=True)

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

        st.pyplot(plot_aggregation(challenge_result), use_container_width=True)

    else:
        st.warning("Tebak dulu hasilnya, lalu klik tombol untuk melihat jawaban sistem Mamdani.")
        