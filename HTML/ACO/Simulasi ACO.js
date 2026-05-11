// --- (KONFIGURASI, PARAMETER ACO, KONTROL ANIMASI... TETAP SAMA) ---
let GRID_ROWS = 4;
let GRID_COLS = 5;
let N_NODES = GRID_ROWS * GRID_COLS;
let POSISI_SIMPUL = [];
let JARINGAN_SISI = [];
let LOKASI_AWAL = 0;
let LOKASI_AKHIR = N_NODES - 1;

let ALFA = 1.5, BETA = 2.5, RHO = 0.05, Q_DEPOSIT = 20.0, FEROMON_AWAL = 1.0;
let MAX_ITERASI = 40;

// <-- DIUBAH: Konfigurasi Koloni
let N_SEMUT = 10; // Jumlah semut per iterasi

let WAKTU_MEMILIH_BASE = 1000;
let WAKTU_BERGERAK_BASE = 500;
let WAKTU_UPDATE_MS = 750;
let waktuStatusTerakhir = 0;
let matriksFeromon, matriksJarak, matriksVisibilitas;

// <-- DIUBAH: Manajemen Semut
// let semut; // Hapus variabel semut tunggal
let koloniSemut = []; // Ganti dengan array koloni
let indeksSemutSaatIni = 0; // Untuk melacak semut mana yang sedang dianimasikan

let iterasiSaatIni = 0;
let panjangMinimumGlobal = Infinity;
let jalurTerbaikGlobal = [];
let statusSimulasi = 'INIT'; // INIT, CHOOSING, MOVING, DEPOSITING, EVAPORATING, FINISHED
let isPaused = true;

let tombolPlayPause, tombolNext, tombolReset;
let sliderKecepatan, labelKecepatan;
let inputJumlahSemut; // <-- TAMBAH: GUI untuk jumlah semut

// --- P5.js SETUP & DRAW ---
function setup() {
    let canvas = createCanvas(550, 550);
    canvas.parent('canvas-container');
    angleMode(DEGREES);
    frameRate(60);

    // --- Inisialisasi Tombol & Slider ---
    tombolPlayPause = createButton('▶ Play');
    tombolPlayPause.parent('kontrol-simulasi');
    tombolPlayPause.mousePressed(togglePlayPause);
    tombolNext = createButton('Next ❯');
    tombolNext.parent('kontrol-simulasi');
    tombolNext.mousePressed(jalankanLangkahBerikutnya);
    tombolReset = createButton('Reset');
    tombolReset.parent('kontrol-simulasi');
    tombolReset.mousePressed(resetSistem);

    // <-- TAMBAH: Input Jumlah Semut
    let labelSemut = createSpan('Jml Semut:');
    labelSemut.parent('kontrol-simulasi');
    inputJumlahSemut = createInput(N_SEMUT.toString(), 'number');
    inputJumlahSemut.parent('kontrol-simulasi');
    inputJumlahSemut.style('width', '50px');
    inputJumlahSemut.attribute('min', '1'); // Min 1 semut
    // <-- Akhir Tambahan

    let sliderContainer = createDiv();
    sliderContainer.class('slider-container');
    sliderContainer.parent('kontrol-simulasi');
    labelKecepatan = createSpan('Kecepatan:');
    labelKecepatan.parent(sliderContainer);
    sliderKecepatan = createSlider(0.5, 50, 1, 0.1);
    sliderKecepatan.parent(sliderContainer);
    sliderKecepatan.style('width', '150px');

    let wrapper = select('#wrapper');
    if (wrapper) {
        wrapper.style('flex-wrap', 'nowrap');
        wrapper.style('align-items', 'center');
    } else {
        console.warn('#wrapper tidak ditemukan. Pastikan ID di HTML sudah benar.');
    }

    inisialisasiSistem();
    updateTombol();
}

function draw() {
    background(245, 245, 240);

    // <-- TAMBAH: Dapatkan semut yang sedang aktif untuk digambar
    let semut = (koloniSemut.length > 0 && indeksSemutSaatIni < koloniSemut.length)
        ? koloniSemut[indeksSemutSaatIni]
        : null;

    // 1. Gambar Graf (Selalu update ketebalan)
    gambarSisi();
    gambarJalurTerbaik();
    gambarSimpul();
    gambarStatus(); // Gambar status (iterasi, dll)

    // 2. Jalankan Logika hanya jika tidak di-Pause
    if (!isPaused) {
        jalankanLogikaOtomatis();
    }

    // 3. Gambar Animasi (Gunakan 'semut' yang sedang aktif)
    if (semut) { // Hanya gambar jika semut aktif ada
        if (statusSimulasi === 'MOVING') {
            gambarPosisiSemutAnimasi(semut, millis() - waktuStatusTerakhir);
        } else if (statusSimulasi === 'CHOOSING' || statusSimulasi === 'DEPOSITING') {
            // Saat 'CHOOSING', tunjukkan semut diam dan sorot calon jalur
            sorotCalonJalur(semut);
            gambarPosisiSemutDiam(semut);
        }
    }
    // Saat EVAPORATING atau FINISHED, tidak ada semut yang digambar
}


// --- FUNGSI KONTROL GUI ---

function togglePlayPause() {
    isPaused = !isPaused;
    if (!isPaused) {
        waktuStatusTerakhir = millis();
        if (statusSimulasi === 'INIT' || statusSimulasi === 'FINISHED') {
            inisialisasiIterasiBaru(true); // <-- DIUBAH: Panggil fungsi baru
            statusSimulasi = 'CHOOSING';
        }
    }
    updateTombol();
}

function jalankanLangkahBerikutnya() {
    isPaused = true;
    updateTombol();
    if (statusSimulasi === 'FINISHED') return;

    // Dapatkan semut aktif saat ini
    let semut = (koloniSemut.length > 0 && indeksSemutSaatIni < koloniSemut.length)
        ? koloniSemut[indeksSemutSaatIni]
        : null;

    // Logika "Next" sekarang memandu state machine
    if (statusSimulasi === 'INIT') {
        inisialisasiIterasiBaru(true); // <-- DIUBAH
        statusSimulasi = 'CHOOSING';
    } else if (statusSimulasi === 'CHOOSING') {
        jalankanLangkahSemut();
        statusSimulasi = 'MOVING';
    } else if (statusSimulasi === 'MOVING') {
        // Cek apakah semut saat ini selesai
        if (semut && (semut.lokasi === LOKASI_AKHIR || semut.terperangkap || semut.jalur.length >= N_NODES)) {
            // Semut ini selesai, lanjut ke semut berikutnya
            indeksSemutSaatIni++;
            if (indeksSemutSaatIni >= N_SEMUT) {
                // Semua semut sudah jalan, masuk fase deposit
                statusSimulasi = 'DEPOSITING';
            } else {
                // Masih ada semut tersisa, semut berikutnya memilih
                statusSimulasi = 'CHOOSING';
            }
        } else {
            // Semut belum selesai, lanjut memilih langkah berikutnya
            statusSimulasi = 'CHOOSING';
        }
    } else if (statusSimulasi === 'DEPOSITING') {
        jalankanDepositKoloni(); // <-- DIUBAH: Panggil deposit koloni
        jalankanPenguapanGlobal();
        statusSimulasi = 'EVAPORATING';
    } else if (statusSimulasi === 'EVAPORATING') {
        // Cek apakah iterasi maksimum tercapai
        // iterasiSaatIni di-increment di dalam inisialisasiIterasiBaru
        if (iterasiSaatIni >= MAX_ITERASI - 1) {
            statusSimulasi = 'FINISHED';
        } else {
            inisialisasiIterasiBaru(); // <-- DIUBAH: Siapkan iterasi (koloni) baru
            statusSimulasi = 'CHOOSING';
        }
    }

    waktuStatusTerakhir = millis();
}

function updateTombol() {
    if (isPaused) {
        tombolPlayPause.html('▶ Play');
        tombolNext.removeAttribute('disabled');
    } else {
        tombolPlayPause.html('❚❚ Pause');
        tombolNext.attribute('disabled', '');
    }
    if (statusSimulasi === 'FINISHED') {
        tombolPlayPause.html('▶ Play');
        tombolPlayPause.attribute('disabled', '');
        tombolNext.attribute('disabled', '');
    } else {
        tombolPlayPause.removeAttribute('disabled');
    }
}

function resetSistem() {
    console.log("Sistem di-reset");

    // <-- TAMBAH: Baca nilai jumlah semut dari input
    N_SEMUT = parseInt(inputJumlahSemut.value());
    if (isNaN(N_SEMUT) || N_SEMUT < 1) {
        N_SEMUT = 10; // Default jika input tidak valid
        inputJumlahSemut.value(N_SEMUT.toString());
    }
    // <-- Akhir Tambahan

    inisialisasiSistem();
    isPaused = true;
    sliderKecepatan.value(1);
    updateTombol();
}

// --- FUNGSI LOGIKA ACO (Otomatis) ---
function jalankanLogikaOtomatis() {
    let kecepatan = sliderKecepatan.value();
    let waktuPilih = WAKTU_MEMILIH_BASE / kecepatan;
    let waktuGerak = WAKTU_BERGERAK_BASE / kecepatan;
    let waktuUpdate = WAKTU_UPDATE_MS / kecepatan; // Waktu untuk deposit/evap

    let waktuBerlalu = millis() - waktuStatusTerakhir;

    // Dapatkan semut aktif saat ini
    let semut = (koloniSemut.length > 0 && indeksSemutSaatIni < koloniSemut.length)
        ? koloniSemut[indeksSemutSaatIni]
        : null;

    if (statusSimulasi === 'CHOOSING') {
        if (waktuBerlalu > waktuPilih) {
            jalankanLangkahSemut();
            statusSimulasi = 'MOVING';
            waktuStatusTerakhir = millis();
        }
    } else if (statusSimulasi === 'MOVING') {
        if (waktuBerlalu > waktuGerak) {
            // Cek apakah semut saat ini selesai
            if (semut && (semut.lokasi === LOKASI_AKHIR || semut.terperangkap || semut.jalur.length >= N_NODES)) {
                // Semut ini selesai, lanjut ke semut berikutnya
                indeksSemutSaatIni++;
                if (indeksSemutSaatIni >= N_SEMUT) {
                    // Semua semut di iterasi ini selesai
                    statusSimulasi = 'DEPOSITING';
                } else {
                    // Lanjut ke semut berikutnya
                    statusSimulasi = 'CHOOSING';
                }
            } else {
                // Semut belum selesai, lanjut memilih
                statusSimulasi = 'CHOOSING';
            }
            waktuStatusTerakhir = millis();
        }
    } else if (statusSimulasi === 'DEPOSITING') {
        if (waktuBerlalu > waktuUpdate) {
            jalankanDepositKoloni(); // <-- DIUBAH
            jalankanPenguapanGlobal();
            statusSimulasi = 'EVAPORATING';
            waktuStatusTerakhir = millis();
        }
    }
    else if (statusSimulasi === 'EVAPORATING') {
        if (waktuBerlalu > waktuUpdate) {
            // Cek selesai
            if (iterasiSaatIni >= MAX_ITERASI - 1) {
                statusSimulasi = 'FINISHED';
                isPaused = true;
                updateTombol();
            } else {
                inisialisasiIterasiBaru(); // <-- DIUBAH
                statusSimulasi = 'CHOOSING';
            }
            waktuStatusTerakhir = millis();
        }
    }
}


// --- FUNGSI INISIALISASI ---
function inisialisasiSistem() {
    statusSimulasi = 'INIT';
    panjangMinimumGlobal = Infinity;
    jalurTerbaikGlobal = [];
    iterasiSaatIni = 0;
    POSISI_SIMPUL = [];

    // ... (Perhitungan posisi simpul SAMA) ...
    let padding = 60;
    let totalLebar = width - 2 * padding;
    let totalTinggi = height - 2 * padding;
    let ukuranPerSelX = totalLebar / (GRID_COLS - 1);
    let ukuranPerSelY = totalTinggi / (GRID_ROWS - 1);
    let ukuranSel = min(ukuranPerSelX, ukuranPerSelY);
    let offsetX = (width - (ukuranSel * (GRID_COLS - 1))) / 2;
    let offsetY = (height - (ukuranSel * (GRID_ROWS - 1))) / 2;

    for (let r = 0; r < GRID_ROWS; r++) {
        for (let c = 0; c < GRID_COLS; c++) {
            let x = offsetX + c * ukuranSel;
            let y = offsetY + r * ukuranSel;
            POSISI_SIMPUL.push(createVector(x, y));
        }
    }
    // ... (Pembuatan JARINGAN_SISI SAMA) ...
    JARINGAN_SISI = [];
    for (let r = 0; r < GRID_ROWS; r++) {
        for (let c = 0; c < GRID_COLS; c++) {
            let u = r * GRID_COLS + c;
            if (c < GRID_COLS - 1) {
                let v = r * GRID_COLS + (c + 1);
                JARINGAN_SISI.push([u, v, floor(random(1, 10))]);
            }
            if (r < GRID_ROWS - 1) {
                let v = (r + 1) * GRID_COLS + c;
                JARINGAN_SISI.push([u, v, floor(random(1, 10))]);
            }
        }
    }

    matriksFeromon = buatMatriks(N_NODES, FEROMON_AWAL);
    matriksJarak = buatMatriks(N_NODES, 0);
    for (let [u, v, jarak] of JARINGAN_SISI) {
        matriksJarak[u][v] = jarak;
        matriksJarak[v][u] = jarak;
    }
    matriksVisibilitas = hitungVisibilitas(matriksJarak);

    inisialisasiIterasiBaru(true); // <-- DIUBAH: Panggil fungsi baru
}

// --- FUNGSI LOGIKA ACO LAINNYA ---

// <-- DIUBAH: Nama fungsi dan logikanya
function inisialisasiIterasiBaru(inisialisasiSistem = false) {
    if (!inisialisasiSistem) {
        iterasiSaatIni++; // Increment iterasi
    } else {
        iterasiSaatIni = 0; // Reset iterasi jika ini reset sistem global
    }

    koloniSemut = []; // Kosongkan koloni lama
    // Buat N_SEMUT baru
    for (let i = 0; i < N_SEMUT; i++) {
        koloniSemut.push({
            lokasi: LOKASI_AWAL,
            jalur: [LOKASI_AWAL],
            panjang: 0,
            selesai: false,
            terperangkap: false,
            simpulAsal: LOKASI_AWAL,
            simpulTujuan: LOKASI_AWAL
        });
    }

    indeksSemutSaatIni = 0; // Mulai animasi dari semut pertama

    if (!inisialisasiSistem) {
        statusSimulasi = 'CHOOSING';
    }
}

function jalankanLangkahSemut() {
    // Ambil semut yang aktif saat ini
    let semut = koloniSemut[indeksSemutSaatIni];
    if (!semut) return; // Pengaman jika semut tidak ada

    // Kalau sudah selesai / terperangkap, tidak usah digerakkan lagi
    if (semut.selesai || semut.terperangkap) return;

    let nextNode = pilihSimpulBerikutnya(semut, matriksFeromon, matriksVisibilitas, ALFA, BETA);

    if (nextNode !== null) {
        semut.simpulAsal   = semut.lokasi;
        semut.simpulTujuan = nextNode;

        let jarakLangkah = matriksJarak[semut.simpulAsal][nextNode];
        semut.panjang += jarakLangkah;

        semut.lokasi = nextNode;
        semut.jalur.push(nextNode);

        if (semut.lokasi === LOKASI_AKHIR) {
            semut.selesai = true;
        }
    } else {
        // 🔴 BUNTU:
        semut.terperangkap = true;

        // ⬇️ KUNCI: jangan ada edge baru yang dianimasikan
        semut.simpulAsal   = semut.lokasi;
        semut.simpulTujuan = semut.lokasi;
    }
}



// <-- DIUBAH: Fungsi ini sekarang menerima 'semut' sebagai parameter
function evaluasiDanDeposit(semut) {
    // 1. Evaluasi (Cek rute terbaik global)
    if (semut.selesai && semut.panjang < panjangMinimumGlobal) {
        panjangMinimumGlobal = semut.panjang;
        jalurTerbaikGlobal = [...semut.jalur];
        console.log(`Iterasi ${iterasiSaatIni}: Rute Terbaik Baru! Panjang: ${panjangMinimumGlobal.toFixed(2)}`);
    }

    // 2. Deposit (Hanya jika semut berhasil sampai tujuan)
    if (semut.selesai) {
        let deposit = Q_DEPOSIT / semut.panjang;
        for (let k = 0; k < semut.jalur.length - 1; k++) {
            let u = semut.jalur[k];
            let v = semut.jalur[k + 1];
            matriksFeromon[u][v] += deposit;
            matriksFeromon[v][u] += deposit; // Asumsikan graf tidak berarah
        }
    }
}

// <-- TAMBAH: Fungsi baru untuk menjalankan deposit untuk seluruh koloni
function jalankanDepositKoloni() {
    console.log(`Iterasi ${iterasiSaatIni}: Fase Deposit oleh ${N_SEMUT} semut...`);
    for (let semut of koloniSemut) {
        evaluasiDanDeposit(semut); // Panggil fungsi evaluasi/deposit untuk tiap semut
    }
}


function jalankanPenguapanGlobal() {
    console.log("Fase Penguapan...");
    for (let [u, v] of JARINGAN_SISI) {
        matriksFeromon[u][v] *= (1 - RHO);
        matriksFeromon[v][u] = matriksFeromon[u][v]; // Jaga simetri
    }
}

function pilihSimpulBerikutnya(ant, T, H, alfa, beta) {
    let i = ant.lokasi;
    let simpulDiizinkan = [];

    // Kumpulkan semua simpul tetangga yang:
    // 1) Ada sisinya (jarak > 0)
    // 2) Belum pernah dikunjungi semut ini (tidak ada di ant.jalur)
    for (let j = 0; j < N_NODES; j++) {
        if (matriksJarak[i][j] > 0 && !ant.jalur.includes(j)) {
            simpulDiizinkan.push(j);
        }
    }

    // Jika tidak ada simpul diizinkan → semut buntu
    if (simpulDiizinkan.length === 0) {
        return null;  // TIDAK ada fallback ke simpul sebelumnya
    }

    // Hitung probabilitas transisi
    let probabilitas = [];
    let penyebut = 0;
    for (let j of simpulDiizinkan) {
        let pembilang = Math.pow(T[i][j], alfa) * Math.pow(H[i][j], beta);
        probabilitas.push({ node: j, nilai: pembilang });
        penyebut += pembilang;
    }

    // Jika semua pembilang 0 (misal feromon/visibilitas nol), pilih acak dari kandidat
    if (penyebut === 0) {
        return random(simpulDiizinkan);
    }

    // Roulette wheel selection
    let r = Math.random();
    let akumulasi = 0;
    for (let item of probabilitas) {
        akumulasi += item.nilai / penyebut;
        if (r <= akumulasi) {
            return item.node;
        }
    }

    // Pengaman numerik: kalau karena pembulatan tidak terpilih,
    // ambil kandidat terakhir
    return probabilitas[probabilitas.length - 1].node;
}

function buatMatriks(n, val) { return Array(n).fill(0).map(() => Array(n).fill(val)); }
function hitungVisibilitas(D) {
    let H = buatMatriks(N_NODES, 0);
    for (let i = 0; i < N_NODES; i++) for (let j = 0; j < N_NODES; j++) if (D[i][j] > 0) H[i][j] = 1.0 / D[i][j];
    return H;
}

// --- FUNGSI GAMBAR ---
function gambarSisi() {
    let feromonMaksimum = -Infinity, feromonMinimum = Infinity;
    for (let [u, v] of JARINGAN_SISI) {
        let f = matriksFeromon[u][v];
        if (f > feromonMaksimum) feromonMaksimum = f;
        if (f < feromonMinimum) feromonMinimum = f;
    }
    if (feromonMaksimum === feromonMinimum) feromonMaksimum += 0.001;

    for (let [u, v, jarak] of JARINGAN_SISI) {
        let pA = POSISI_SIMPUL[u];
        let pB = POSISI_SIMPUL[v];
        let ketebalanGaris = map(matriksFeromon[u][v], feromonMinimum, feromonMaksimum, 1, 12);
        stroke(150, 150, 150, 180);
        strokeWeight(ketebalanGaris);
        line(pA.x, pA.y, pB.x, pB.y);

        let titikTengah = p5.Vector.lerp(pA, pB, 0.5);

        // --- MODIFIKASI LABEL SISI (dari permintaan sebelumnya) ---
        noStroke();
        fill(0, 0, 150);     // Warna font (biru tua)
        textSize(12);        // Ukuran font diperbesar
        textStyle(BOLD);     // Font tebal
        textAlign(CENTER, CENTER);

        let offsetX = (pA.y === pB.y) ? 0 : 10;
        let offsetY = (pA.x === pB.x) ? 10 : 0;

        text(jarak, titikTengah.x + offsetX, titikTengah.y + offsetY);

        textStyle(NORMAL); // Reset text style
        // --- MODIFIKASI LABEL SISI SELESAI ---
    }
}
function sorotCalonJalur(ant) {
    if (!ant || ant.selesai || ant.terperangkap) return;
    let i = ant.lokasi;
    let simpulDiizinkan = [];
    // <-- DIUBAH: Logika sama dengan 'pilihSimpulBerikutnya'
    for (let j = 0; j < N_NODES; j++) {
        if (matriksJarak[i][j] > 0 && !ant.jalur.includes(j)) {
            simpulDiizinkan.push(j);
        }
    }

    for (let j of simpulDiizinkan) {
        let pA = POSISI_SIMPUL[i];
        let pB = POSISI_SIMPUL[j];
        stroke(255, 200, 0, 150);
        strokeWeight(5);
        line(pA.x, pA.y, pB.x, pB.y);
    }
}
function gambarSimpul() {
    for (let i = 0; i < N_NODES; i++) {
        let p = POSISI_SIMPUL[i];
        fill(255);
        strokeWeight(2);
        stroke(50);
        if (i === LOKASI_AWAL) {
            fill(60, 179, 113);
            stroke(40, 120, 80);
        } else if (i === LOKASI_AKHIR) {
            fill(220, 20, 60);
            stroke(150, 10, 30);
        }
        ellipse(p.x, p.y, 24, 24);
        fill(0);
        noStroke();
        textSize(11);
        textAlign(CENTER, CENTER);
        text(i, p.x, p.y);
    }
}
function gambarJalurTerbaik() {
    if (jalurTerbaikGlobal.length > 1) {
        stroke(220, 20, 60, 200);
        strokeWeight(4);
        noFill();
        beginShape();
        for (let simpul of jalurTerbaikGlobal) vertex(POSISI_SIMPUL[simpul].x, POSISI_SIMPUL[simpul].y);
        endShape();
    }
}
function gambarPosisiSemutAnimasi(ant, waktuBerlalu) {
    if (ant.terperangkap) {
        gambarPosisiSemutDiam(ant);
        return;
    }

    let kecepatan = sliderKecepatan.value();
    let waktuGerak = WAKTU_BERGERAK_BASE / kecepatan;
    let porsentase = constrain(waktuBerlalu / waktuGerak, 0, 1);
    let pA = POSISI_SIMPUL[ant.simpulAsal];
    let pB = POSISI_SIMPUL[ant.simpulTujuan];
    let pos = p5.Vector.lerp(pA, pB, porsentase);

    fill(0, 100, 255);
    stroke(255);
    strokeWeight(2);
    ellipse(pos.x, pos.y, 10, 10);
}
function gambarPosisiSemutDiam(ant) {
    if (!ant) return;
    let p = POSISI_SIMPUL[ant.lokasi];
    fill(0, 100, 255);
    stroke(255);
    strokeWeight(2);
    ellipse(p.x, p.y, 10, 10);
}

function gambarStatus() {
    fill(0);
    noStroke();
    textSize(14);
    textAlign(LEFT, TOP);
    text(`Iterasi: ${iterasiSaatIni} / ${MAX_ITERASI}`, 10, 10);
    text(`Rute Terbaik Sejauh Ini: ${panjangMinimumGlobal.toFixed(2)}`, 10, 30);

    // <-- DIUBAH: Menampilkan status semut saat ini
    let semutAktifTeks = (statusSimulasi === 'CHOOSING' || statusSimulasi === 'MOVING')
        ? `(Semut ${indeksSemutSaatIni + 1} dari ${N_SEMUT})`
        : "";
    text(`Kecepatan: ${sliderKecepatan.value()}x`, 10, 50);

    let statusTeks = "";
    if (statusSimulasi === 'FINISHED') {
        fill(220, 20, 60); textSize(20);
        statusTeks = "SIMULASI SELESAI";
    } else if (statusSimulasi === 'INIT') {
        fill(0, 150, 0); textSize(18);
        statusTeks = "Graf siap. Klik 'Play' atau 'Next'";
    } else if (statusSimulasi === 'CHOOSING' && isPaused) {
        fill(255, 165, 0); textSize(16);
        statusTeks = `Semut ${indeksSemutSaatIni + 1} sedang memilih... (Klik Next)`;
    } else if (statusSimulasi === 'CHOOSING') {
        fill(255, 165, 0); textSize(16);
        statusTeks = `Memilih... ${semutAktifTeks}`;
    } else if (statusSimulasi === 'MOVING') {
        fill(0, 100, 255); textSize(16);
        statusTeks = `Bergerak... ${semutAktifTeks}`;
    } else if (statusSimulasi === 'DEPOSITING') {
        fill(0, 100, 255); textSize(16);
        statusTeks = `Semua semut menyimpan Feromon...`;
    } else if (statusSimulasi === 'EVAPORATING') {
        fill(100, 100, 100); textSize(16);
        statusTeks = "Feromon Menguap (Evaporation)...";
    }

    textAlign(CENTER, CENTER);
    text(statusTeks, width / 2, height / 2 - 20);
}