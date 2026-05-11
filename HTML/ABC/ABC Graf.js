/* ====================================================================== */
/*  ABC Graf.js  —  Bee Colony Optimization untuk Graf (TSP) p5.js       */
/*  Cari rute terpendek yang melewati semua titik dan kembali ke awal    */
/* ====================================================================== */

/* ----------------- Variabel global & parameter ----------------- */

let nodes = [];           // Titik-titik dalam graf
let lebah = [];           // Koloni lebah
let jalurTerbaik = null;  // Rute terbaik global (array indeks node)
let fitnessTerbaik = Infinity;

let jumlahNode = 20;      // Default jumlah titik

const RADIUS_NODE = 14;
const LEBAR_MENU = 320;

let JUMLAH_LEBAH = 40;
let PROP_EMPLOYED = 0.5;
let LIMIT_TRIAL = 40;

let panelKontrol;
let sliderNode, sliderLebah, sliderProp, sliderLimit;
let tombolStartStop, tombolAcakGraf, tombolResetKoloni;
let infoBest, infoParam;

let berjalan = true;
let iterasi = 0;

/* ====================================================================== */
/*                             KELAS LEBAH                                */
/* ====================================================================== */

class Lebah {
    constructor() {
        this.rute = [];
        this.fitness = Infinity;
        this.trial = 0;
        this.posIndex = 0; // posisi kontinu sepanjang rute untuk animasi
    }

    bangunRuteAwal() {
        if (nodes.length < 2) {
            this.rute = [];
            this.fitness = Infinity;
            return;
        }

        // Rute TSP siklus: 0 -> permutasi(1..N-1) -> 0
        const perm = [];
        for (let i = 1; i < nodes.length; i++) perm.push(i);
        shuffle(perm, true);

        this.rute = [0, ...perm, 0];
        this.fitness = hitungPanjangRute(this.rute);
        this.trial = 0;
        // Mulai dari posisi acak di rute demi variasi visual
        this.posIndex = random(this.rute.length - 1);

        perbaruiRuteTerbaik(this);
    }

    cariTetanggaDanUpdate() {
        if (nodes.length < 2) return;

        // Jika rute tidak cocok dengan jumlah node, bangun ulang
        if (!this.rute || this.rute.length !== nodes.length + 1) {
            this.bangunRuteAwal();
            return;
        }

        // Buat rute tetangga dengan 2-opt (reverse segmen di tengah)
        const ruteBaru = this.rute.slice();
        const n = nodes.length;

        let i = floor(random(1, n)); // [1, n-1]
        let j = floor(random(1, n));
        if (i === j) {
            j = (j + 1) % n;
            if (j === 0) j = 1;
        }

        let a = min(i, j);
        let b = max(i, j);

        // Reverse segmen ruteBaru[a..b]
        while (a < b) {
            const tmp = ruteBaru[a];
            ruteBaru[a] = ruteBaru[b];
            ruteBaru[b] = tmp;
            a++;
            b--;
        }

        const fitBaru = hitungPanjangRute(ruteBaru);
        if (fitBaru < this.fitness) {
            this.rute = ruteBaru;
            this.fitness = fitBaru;
            this.trial = 0;
            // posIndex dibiarkan agar lebah "lanjut jalan"
            perbaruiRuteTerbaik(this);
        } else {
            this.trial++;
        }
    }

    gambar(idx, jumlahEmployed) {
        if (!this.rute || this.rute.length < 2) return;

        // Update posisi animasi sepanjang rute
        const kecepatan = 0.03; // makin besar makin cepat
        this.posIndex = (this.posIndex + kecepatan) % (this.rute.length - 1);

        const segmen = floor(this.posIndex);
        const t = this.posIndex - segmen;

        const indexA = this.rute[segmen];
        const indexB = this.rute[segmen + 1];

        const A = nodes[indexA];
        const B = nodes[indexB];

        const x = lerp(A.x, B.x, t);
        const y = lerp(A.y, B.y, t);

        // Garis jejak rute lebah (dari node 0 sampai posisi sekarang)
        strokeWeight(1);
        if (idx < jumlahEmployed) {
            stroke(255, 255, 0, 80);  // employed → kuning transparan
        } else {
            stroke(255, 0, 255, 80);  // onlooker → fuchsia transparan
        }
        noFill();
        beginShape();
        for (let i = 0; i <= segmen; i++) {
            const n = nodes[this.rute[i]];
            vertex(n.x, n.y);
        }
        vertex(x, y);
        endShape();

        // Node lebah (titiknya)
        noStroke();
        if (idx < jumlahEmployed) {
            fill(255, 255, 0);   // employed = kuning solid
        } else {
            fill(255, 0, 255);   // onlooker = fuchsia
        }
        circle(x, y, 8);
    }
}

/* ====================================================================== */
/*                        FUNGSI GRAF & FITNESS                           */
/* ====================================================================== */

function buatGrafAcak() {
    nodes = [];
    const w = width;
    const h = height;
    const margin = 40;

    for (let i = 0; i < jumlahNode; i++) {
        const x = random(margin, w - margin);
        const y = random(margin, h - margin);
        nodes.push({ id: i, x, y });
    }

    // Reset best route ketika graf berubah
    jalurTerbaik = null;
    fitnessTerbaik = Infinity;
}

function jarakNode(i, j) {
    const a = nodes[i];
    const b = nodes[j];
    return dist(a.x, a.y, b.x, b.y);
}

function hitungPanjangRute(rute) {
    if (!rute || rute.length < 2) return Infinity;
    let total = 0;
    for (let i = 0; i < rute.length - 1; i++) {
        const u = rute[i];
        const v = rute[i + 1];
        total += jarakNode(u, v);
    }
    return total;
}

function perbaruiRuteTerbaik(lebah) {
    if (!lebah || !lebah.rute || !isFinite(lebah.fitness)) return;
    if (lebah.fitness < fitnessTerbaik) {
        fitnessTerbaik = lebah.fitness;
        jalurTerbaik = lebah.rute.slice();
    }
}

/* ====================================================================== */
/*                         INISIALISASI KOLONI                            */
/* ====================================================================== */

function inisialisasiKoloni() {
    lebah = [];
    jalurTerbaik = null;
    fitnessTerbaik = Infinity;
    iterasi = 0;

    for (let i = 0; i < JUMLAH_LEBAH; i++) {
        const b = new Lebah();
        b.bangunRuteAwal();
        lebah.push(b);
    }
}

/* ====================================================================== */
/*                          SIKLUS BEE COLONY                             */
/* ====================================================================== */

function jalankanSiklusLebah() {
    if (nodes.length < 2 || lebah.length === 0) return;

    // Urutkan lebah berdasarkan fitness, lebah terbaik menjadi employed
    lebah.sort((a, b) => a.fitness - b.fitness);

    const jumlahEmployed = max(1, floor(PROP_EMPLOYED * lebah.length));
    const employed = lebah.slice(0, jumlahEmployed);
    const onlookers = lebah.slice(jumlahEmployed);

    // Fase Employed: eksplor lokal
    for (const b of employed) {
        b.cariTetanggaDanUpdate();
    }

    // Hitung probabilitas onlooker memilih sumber
    let totalKebalikan = 0;
    const kebalikan = employed.map(b => {
        const val = 1 / (b.fitness + 1e-6);
        totalKebalikan += val;
        return val;
    });

    function pilihSumber() {
        const r = random(totalKebalikan);
        let akum = 0;
        for (let i = 0; i < employed.length; i++) {
            akum += kebalikan[i];
            if (r <= akum) return employed[i];
        }
        return employed[employed.length - 1];
    }

    // Fase Onlooker
    for (const b of onlookers) {
        const sumber = pilihSumber();
        // Copy solusi sumber
        b.rute = sumber.rute.slice();
        b.fitness = sumber.fitness;
        b.trial = sumber.trial;
        // Lanjut eksplor
        b.cariTetanggaDanUpdate();
    }

    // Fase Scout: jika trial terlalu banyak, acak ulang rute
    for (const b of lebah) {
        if (b.trial > LIMIT_TRIAL) {
            b.bangunRuteAwal();
        }
    }

    iterasi++;
}

/* ====================================================================== */
/*                           GAMBARKAN GRAF                               */
/* ====================================================================== */

function gambarGraf() {
    background(10);

    // Gambar rute terbaik sebagai polyline tebal
    if (jalurTerbaik && jalurTerbaik.length > 1) {
        stroke(100, 200, 255);
        strokeWeight(4);
        noFill();
        beginShape();
        for (const idx of jalurTerbaik) {
            const n = nodes[idx];
            vertex(n.x, n.y);
        }
        endShape();
    }

    // Gambar semua node
    textAlign(CENTER, CENTER);
    textSize(12);
    for (const n of nodes) {
        // Node
        stroke(255);
        strokeWeight(2);
        fill(n.id === 0 ? "#2ecc71" : "#3498db"); // node 0 hijau, lainnya biru
        circle(n.x, n.y, RADIUS_NODE * 2);

        // Label ID
        noStroke();
        fill(0);
        text(n.id, n.x, n.y);
    }
}

/* ====================================================================== */
/*                             GAMBARKAN LEBAH                            */
/* ====================================================================== */

function gambarKoloni() {
    if (lebah.length === 0) return;

    const jumlahEmployed = max(1, floor(PROP_EMPLOYED * lebah.length));
    for (let i = 0; i < lebah.length; i++) {
        lebah[i].gambar(i, jumlahEmployed);
    }
}

/* ====================================================================== */
/*                        P5: SETUP & DRAW & UI                           */
/* ====================================================================== */

function setup() {
    const canvasW = windowWidth - LEBAR_MENU;
    const canvasH = windowHeight;
    const cnv = createCanvas(canvasW, canvasH);
    cnv.position(0, 0);

    buatGrafAcak();
    inisialisasiKoloni();
    buatUI(canvasW);
}

function draw() {
    gambarGraf();

    if (berjalan) {
        jalankanSiklusLebah();
    }

    gambarKoloni();
    perbaruiInfo();
}

/* ====================================================================== */
/*                                UI PANEL                                */
/* ====================================================================== */

function buatUI(offsetX) {
    panelKontrol = createDiv();
    panelKontrol.position(offsetX, 0);
    panelKontrol.size(LEBAR_MENU, windowHeight);
    panelKontrol.style("background", "#181818");
    panelKontrol.style("padding", "12px");
    panelKontrol.style("box-sizing", "border-box");
    panelKontrol.style("overflow-y", "auto");
    panelKontrol.style("font-size", "13px");

    // ==== Modern Button CSS (Bootstrap-like) ====================================
    const style = document.createElement("style");
    style.innerHTML = `
        .btn-modern {
            background: #0d6efd;
            color: white;
            border: none;
            padding: 8px 14px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: 0.15s;
            margin-right: 6px;
            margin-top: 6px;
        }
        .btn-modern:hover {
            background: #0b5ed7;
        }
        .btn-danger {
            background: #dc3545;
        }
        .btn-danger:hover {
            background: #bb2d3b;
        }
        .btn-warning {
            background: #ffc107;
            color: #000;
        }
        .btn-warning:hover {
            background: #e0a800;
        }
        .button-row {
            display: flex;
            flex-direction: row;
            flex-wrap: wrap;
            margin-top: 6px;
        }
        `;
    document.head.appendChild(style);

    const judul = createElement("h2", "ABC untuk Graf (TSP)");
    judul.parent(panelKontrol);
    judul.style("margin", "4px 0 8px 0");
    judul.style("font-size", "18px");

    const deskripsi = createP(
        ""
    );
    deskripsi.parent(panelKontrol);

    // Slider jumlah node
    createP("<b>Banyaknya Titik</b> (10–30)").parent(panelKontrol);
    sliderNode = createSlider(10, 30, jumlahNode, 1);
    sliderNode.parent(panelKontrol);
    sliderNode.input(() => {
        jumlahNode = sliderNode.value();
        buatGrafAcak();
        inisialisasiKoloni();
    });

    // Slider jumlah lebah
    createP("<b>Banyaknya lebah</b> (10–100)").parent(panelKontrol);
    sliderLebah = createSlider(10, 100, JUMLAH_LEBAH, 1);
    sliderLebah.parent(panelKontrol);
    sliderLebah.input(() => {
        JUMLAH_LEBAH = sliderLebah.value();
        inisialisasiKoloni();
    });

    // Slider prop employed
    createP("<b>Proporsi employed</b> (0.1–0.9)").parent(panelKontrol);
    sliderProp = createSlider(0.1, 0.9, PROP_EMPLOYED, 0.05);
    sliderProp.parent(panelKontrol);
    sliderProp.input(() => {
        PROP_EMPLOYED = sliderProp.value();
    });

    // Slider limit trial
    createP("<b>Batas <i>trial</i> untuk scout</b> (10–100)").parent(panelKontrol);
    sliderLimit = createSlider(10, 100, LIMIT_TRIAL, 5);
    sliderLimit.parent(panelKontrol);
    sliderLimit.input(() => {
        LIMIT_TRIAL = sliderLimit.value();
    });

    // Tombol kontrol
    // ===== BARIS TOMBOL =========================================================
    const row = createDiv();
    row.parent(panelKontrol);
    row.addClass("button-row");

    // Tombol acak graf
    tombolAcakGraf = createButton("Acak Graf");
    tombolAcakGraf.parent(row);
    tombolAcakGraf.addClass("btn-modern btn-warning");
    tombolAcakGraf.mousePressed(() => {
        buatGrafAcak();
        inisialisasiKoloni();
    });

    // Tombol reset koloni
    tombolResetKoloni = createButton("Reset Koloni");
    tombolResetKoloni.parent(row);
    tombolResetKoloni.addClass("btn-modern btn-danger");
    tombolResetKoloni.mousePressed(() => {
        inisialisasiKoloni();
    });


    infoBest = createP("");
    infoBest.parent(panelKontrol);
    infoBest.style("margin-top", "10px");
    infoBest.style("font-size", "13px");

    infoParam = createP(
        "Warna:<br>" +
        "• Titik 0 (awal/akhir): hijau<br>" +
        "• Titik lain: biru<br>" +
        "• Rute terbaik: garis biru muda tebal<br>" +
        "• Lebah employed: kuning<br>" +
        "• Lebah onlooker: ungu"
    );
    infoParam.parent(panelKontrol);
}

function perbaruiInfo() {
    if (!infoBest) return;
    const fitTxt = isFinite(fitnessTerbaik) ? fitnessTerbaik.toFixed(1) : "belum ada";
    infoBest.html(
        `Iterasi: ${iterasi}<br>` +
        `Panjang rute terbaik: ${fitTxt}<br>` +
        `Banyak Titik: ${nodes.length}<br>` +
        `Lebah: ${lebah.length} (employed ≈ ${(PROP_EMPLOYED * 100).toFixed(0)}%)`
    );
}

/* ====================================================================== */
/*                          HANDLER WINDOW RESIZE                         */
/* ====================================================================== */

function windowResized() {
    const canvasW = windowWidth - LEBAR_MENU;
    const canvasH = windowHeight;
    resizeCanvas(canvasW, canvasH);

    if (panelKontrol) {
        panelKontrol.position(canvasW, 0);
        panelKontrol.size(LEBAR_MENU, canvasH);
    }

    // Regenerasi posisi node agar tetap proporsional dengan ukuran baru
    buatGrafAcak();
    inisialisasiKoloni();
}
