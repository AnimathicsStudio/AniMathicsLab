/* ====================================================================== */
/*  ABC Labirin.js  —  Bee Colony Optimization untuk Labirin p5.js        */
/*  Versi dengan visualisasi lebah yang benar-benar "cari jalan"         */
/* ====================================================================== */

/* ----------------- Variabel global & parameter ----------------- */

let grid = [];
let mulai = null;
let akhir = null;
let bufferLabirin = null;

let KOLOM = 0;
let BARIS = 0;
const UKURAN_SEL = 25;
const LEBAR_MENU = 320;

/* Parameter Bee Colony & Maze (default) */
let JUMLAH_LEBAH      = 30;
let PROP_EMPLOYED     = 0.5;   // 50% employed, 50% onlooker
let LIMIT_TRIAL       = 60;    // Batas trial sebelum jadi scout
let PELUANG_BUAT_LOOP = 0.05;  // Probabilitas membuka dinding tambahan

/* Koloni lebah & solusi terbaik */
let lebah = [];
let jalurTerbaik = null;
let fitnessTerbaik = Infinity;

/* Visual lebah */
let jumlahEmployedTerakhir = 0;     // untuk membedakan employed vs onlooker secara visual
const KECEPATAN_LEBAH = 0.25;      // seberapa cepat lebah bergerak sepanjang jalur
const FREKUENSI_ABC   = 10;        // jalankan ABC tiap N frame

/* UI p5 (panel, slider, tombol) */
let ui = {
  menuPanel: null,
  mazePanel: null,
  sliders: {},
  labels: {},
  button: null
};

/* ====================================================================== */
/*                             KELAS  Sel                                 */
/* ====================================================================== */

class Sel {
  constructor(i, j) {
    this.i = i;
    this.j = j;

    // Dinding labirin
    this.dinding = { atas: true, kanan: true, bawah: true, kiri: true };
    this.sudahDikunjungi = false;

    // Tetangga graf (diisi setelah dinding dihapus)
    this.tetangga = [];

    // Blokir manual oleh user
    this.terblokir = false;
  }

  tampilkanDinding(buffer) {
    const x = this.i * UKURAN_SEL;
    const y = this.j * UKURAN_SEL;

    buffer.stroke(255);
    buffer.strokeWeight(2);
    buffer.strokeCap(PROJECT);

    if (this.dinding.atas)  buffer.line(x, y, x + UKURAN_SEL, y);
    if (this.dinding.kanan) buffer.line(x + UKURAN_SEL, y, x + UKURAN_SEL, y + UKURAN_SEL);
    if (this.dinding.bawah) buffer.line(x, y + UKURAN_SEL, x + UKURAN_SEL, y + UKURAN_SEL);
    if (this.dinding.kiri)  buffer.line(x, y, x, y + UKURAN_SEL);
  }

  cekTetanggaBelumDikunjungi() {
    const daftar = [];
    const atas  = ambilSel(this.i,     this.j - 1);
    const kanan = ambilSel(this.i + 1, this.j);
    const bawah = ambilSel(this.i,     this.j + 1);
    const kiri  = ambilSel(this.i - 1, this.j);

    if (atas  && !atas.sudahDikunjungi)  daftar.push(atas);
    if (kanan && !kanan.sudahDikunjungi) daftar.push(kanan);
    if (bawah && !bawah.sudahDikunjungi) daftar.push(bawah);
    if (kiri  && !kiri.sudahDikunjungi)  daftar.push(kiri);

    return daftar;
  }
}

/* ====================================================================== */
/*                             KELAS  Lebah                               */
/* ====================================================================== */

class Lebah {
  constructor() {
    this.jalur = [];
    this.fitness = Infinity;
    this.trial = 0;

    // posisi lebah di sepanjang jalur untuk visualisasi
    this.posIndex = 0;
  }

  bangunJalurAwal() {
    const path = buatJalurAcak(mulai, akhir);
    if (path) {
      this.jalur = path;
      this.fitness = hitungFitness(path);
      // mulai dari posisi acak di jalur supaya lebah tersebar
      this.posIndex = random(0, this.jalur.length);
    } else {
      this.jalur = [];
      this.fitness = Infinity;
      this.posIndex = 0;
    }
    this.trial = 0;
    perbaruiJalurTerbaik(this);
  }

  cariTetanggaDanUpdate() {
    if (!mulai || !akhir) return;

    if (!this.jalur || this.jalur.length === 0 || !isFinite(this.fitness)) {
      this.bangunJalurAwal();
      return;
    }

    const jalurBaru = buatJalurTetangga(this.jalur);
    if (jalurBaru) {
      const fitBaru = hitungFitness(jalurBaru);
      if (fitBaru < this.fitness) {
        this.jalur = jalurBaru;
        this.fitness = fitBaru;
        this.trial = 0;
        // posIndex TIDAK di-reset → lebah lanjut jalan di jalur barunya
        perbaruiJalurTerbaik(this);
      } else {
        this.trial++;
      }
    } else {
      this.trial++;
    }
  }
}

/* ====================================================================== */
/*                    UTILITAS LABIRIN / GRAF                             */
/* ====================================================================== */

function indeks(i, j) {
  if (i < 0 || j < 0 || i >= KOLOM || j >= BARIS) return -1;
  return i + j * KOLOM;
}

function ambilSel(i, j) {
  const idx = indeks(i, j);
  if (idx < 0 || idx >= grid.length) return null;
  return grid[idx];
}

function hapusDinding(a, b) {
  const dx = a.i - b.i;
  const dy = a.j - b.j;

  if (dx === 1) {          // b di kiri a
    a.dinding.kiri = false;
    b.dinding.kanan = false;
  } else if (dx === -1) {  // b di kanan a
    a.dinding.kanan = false;
    b.dinding.kiri = false;
  }

  if (dy === 1) {          // b di atas a
    a.dinding.atas = false;
    b.dinding.bawah = false;
  } else if (dy === -1) {  // b di bawah a
    a.dinding.bawah = false;
    b.dinding.atas = false;
  }
}

function bangunGrafTetangga() {
  for (const sel of grid) {
    sel.tetangga = [];

    const atas  = ambilSel(sel.i, sel.j - 1);
    const kanan = ambilSel(sel.i + 1, sel.j);
    const bawah = ambilSel(sel.i, sel.j + 1);
    const kiri  = ambilSel(sel.i - 1, sel.j);

    if (atas  && !sel.dinding.atas)   sel.tetangga.push(atas);
    if (kanan && !sel.dinding.kanan)  sel.tetangga.push(kanan);
    if (bawah && !sel.dinding.bawah)  sel.tetangga.push(bawah);
    if (kiri  && !sel.dinding.kiri)   sel.tetangga.push(kiri);
  }
}

/* ====================================================================== */
/*                      GENERATE LABIRIN + LOOP                           */
/* ====================================================================== */

function buatLabirinDanGraf() {
  grid = [];

  // Buat semua sel
  for (let j = 0; j < BARIS; j++) {
    for (let i = 0; i < KOLOM; i++) {
      grid.push(new Sel(i, j));
    }
  }

  // Start & goal
  mulai = ambilSel(0, 0);
  akhir = ambilSel(KOLOM - 1, BARIS - 1);

  // DFS backtracker
  for (const sel of grid) {
    sel.sudahDikunjungi = false;
  }

  let current = mulai;
  current.sudahDikunjungi = true;
  const stack = [current];

  while (stack.length > 0) {
    current = stack[stack.length - 1];
    const tetangga = current.cekTetanggaBelumDikunjungi();

    if (tetangga.length > 0) {
      const next = random(tetangga);
      next.sudahDikunjungi = true;
      hapusDinding(current, next);
      stack.push(next);
    } else {
      stack.pop();
    }
  }

  // Tambah beberapa loop (longgar)
  buatLoop();

  // Bangun graf tetangga
  bangunGrafTetangga();
}

function buatLoop() {
  for (const sel of grid) {
    const kanan = ambilSel(sel.i + 1, sel.j);
    if (kanan && sel.dinding.kanan && random() < PELUANG_BUAT_LOOP) {
      hapusDinding(sel, kanan);
    }

    const bawah = ambilSel(sel.i, sel.j + 1);
    if (bawah && sel.dinding.bawah && random() < PELUANG_BUAT_LOOP) {
      hapusDinding(sel, bawah);
    }
  }
}

function gambarLabirinKeBuffer() {
  if (!bufferLabirin) return;
  bufferLabirin.background(30, 30, 30);
  for (const sel of grid) {
    sel.tampilkanDinding(bufferLabirin);
  }
}

/* ====================================================================== */
/*                     UTILITAS JALUR / BEE COLONY                        */
/* ====================================================================== */

function hitungFitness(jalur) {
  if (!jalur || jalur.length === 0) return Infinity;
  return jalur.length; // semakin pendek semakin baik
}

function tetanggaValid(sel, visitedSet) {
  const hasil = [];
  for (const t of sel.tetangga) {
    if (!t.terblokir && !visitedSet.has(t)) {
      hasil.push(t);
    }
  }
  return hasil;
}

function buatJalurAcak(start, goal) {
  if (!start || !goal) return null;

  const path = [start];
  const visited = new Set([start]);

  while (path.length > 0) {
    const current = path[path.length - 1];
    if (current === goal) {
      return [...path];
    }

    const kandidat = tetanggaValid(current, visited);
    if (kandidat.length > 0) {
      const next = random(kandidat);
      visited.add(next);
      path.push(next);
    } else {
      path.pop();
    }
  }

  return null;
}

function buatJalurDariSel(start, goal, visitedAwal) {
  if (!start || !goal) return null;

  const path = [start];
  const visited = new Set(visitedAwal || []);
  visited.add(start);

  while (path.length > 0) {
    const current = path[path.length - 1];
    if (current === goal) {
      return [...path];
    }

    const kandidat = tetanggaValid(current, visited);
    if (kandidat.length > 0) {
      const next = random(kandidat);
      visited.add(next);
      path.push(next);
    } else {
      path.pop();
    }
  }

  return null;
}

function buatJalurTetangga(jalurLama) {
  if (!jalurLama || jalurLama.length < 2) {
    return buatJalurAcak(mulai, akhir);
  }

  const panjang = jalurLama.length;
  const maxIndex = Math.max(0, panjang - 2); // jangan potong di goal
  const cutIndex = Math.floor(random(0, maxIndex + 1));

  const prefix = jalurLama.slice(0, cutIndex + 1);
  const titikPotong = prefix[prefix.length - 1];

  const suffix = buatJalurDariSel(titikPotong, akhir, prefix);
  if (!suffix) {
    return buatJalurAcak(mulai, akhir);
  }

  // suffix sudah mengandung titikPotong sebagai elemen pertama
  return prefix.slice(0, -1).concat(suffix);
}

function perbaruiJalurTerbaik(b) {
  if (!b.jalur || b.jalur.length === 0) return;
  if (!isFinite(b.fitness)) return;

  if (b.fitness < fitnessTerbaik) {
    fitnessTerbaik = b.fitness;
    jalurTerbaik = [...b.jalur];
  }
}

/* ====================================================================== */
/*                        FUNGSI Bee Colony utama                         */
/* ====================================================================== */

function inisialisasiLebah() {
  lebah = [];
  jalurTerbaik = null;
  fitnessTerbaik = Infinity;
  jumlahEmployedTerakhir = 0;

  for (let i = 0; i < JUMLAH_LEBAH; i++) {
    const b = new Lebah();
    b.bangunJalurAwal();
    lebah.push(b);
  }
}

function hitungProbabilitasEmployed(employedArray) {
  const bobot = employedArray.map(b => {
    if (!b.jalur || b.jalur.length === 0 || !isFinite(b.fitness)) return 0;
    return 1 / (b.fitness + 1e-9);
  });

  const total = bobot.reduce((a, v) => a + v, 0);
  if (total <= 0) return [];

  return bobot.map(w => w / total);
}

function rouletteWheelSelect(prob) {
  if (!prob || prob.length === 0) return 0;
  const r = random();
  let akum = 0;
  for (let i = 0; i < prob.length; i++) {
    akum += prob[i];
    if (r <= akum) return i;
  }
  return prob.length - 1;
}

function jalankanSiklusLebah(iter = 1) {
  if (!lebah || lebah.length === 0) return;
  if (!mulai || !akhir) return;

  for (let k = 0; k < iter; k++) {
    const jumlahEmployed = Math.max(1, Math.floor(PROP_EMPLOYED * lebah.length));
    jumlahEmployedTerakhir = jumlahEmployed;     // simpan untuk visualisasi
    lebah.sort((a, b) => a.fitness - b.fitness);
    const employed = lebah.slice(0, jumlahEmployed);
    const onlooker = lebah.slice(jumlahEmployed);

    // 1. Employed bees: local search
    for (const b of employed) {
      b.cariTetanggaDanUpdate();
    }

    // 2. Onlooker bees
    const prob = hitungProbabilitasEmployed(employed);
    if (prob.length > 0) {
      for (const b of onlooker) {
        const idx = rouletteWheelSelect(prob);
        const sumber = employed[idx];

        b.jalur = [...sumber.jalur];
        b.fitness = sumber.fitness;
        b.trial = sumber.trial;
        // posIndex sengaja tidak direset ke 0 → tetap mengalir
        if (b.jalur.length > 0) {
          b.posIndex = b.posIndex % b.jalur.length;
        } else {
          b.posIndex = 0;
        }

        b.cariTetanggaDanUpdate();
      }
    }

    // 3. Scout bees
    for (const b of lebah) {
      if (b.trial > LIMIT_TRIAL) {
        b.bangunJalurAwal();
      }
    }
  }
}

/* ====================================================================== */
/*                            Gambar di kanvas                            */
/* ====================================================================== */

function gambarJalurTerbaik() {
  if (!jalurTerbaik || jalurTerbaik.length === 0) return;

  stroke(0, 150, 255, 220);
  strokeWeight(4);
  noFill();

  beginShape();
  for (const sel of jalurTerbaik) {
    const cx = sel.i * UKURAN_SEL + UKURAN_SEL / 2;
    const cy = sel.j * UKURAN_SEL + UKURAN_SEL / 2;
    vertex(cx, cy);
  }
  endShape();
}

function gambarBlokir() {
  noStroke();
  fill(220, 50, 50, 180);
  for (const sel of grid) {
    if (sel.terblokir) {
      const x = sel.i * UKURAN_SEL;
      const y = sel.j * UKURAN_SEL;
      rect(x, y, UKURAN_SEL, UKURAN_SEL);
    }
  }
}

function gambarTitikAwalAkhir() {
  if (akhir) {
    noStroke();
    fill(0, 150, 255);
    rect(akhir.i * UKURAN_SEL, akhir.j * UKURAN_SEL, UKURAN_SEL, UKURAN_SEL);
  }
  if (mulai) {
    noStroke();
    fill(0, 255, 150);
    rect(mulai.i * UKURAN_SEL, mulai.j * UKURAN_SEL, UKURAN_SEL, UKURAN_SEL);
  }
}

/* Visualisasi lebah: titik bergerak + jejak jalur sampai posisinya */
function gambarLebah() {
  if (!lebah || lebah.length === 0) return;

  for (let idx = 0; idx < lebah.length; idx++) {
    const b = lebah[idx];
    if (!b.jalur || b.jalur.length === 0) continue;

    // update posisi kontinu
    b.posIndex += KECEPATAN_LEBAH;
    if (b.posIndex >= b.jalur.length) {
      b.posIndex = 0;
    }

    const posInt = Math.floor(b.posIndex);

    /* ---------------------------------------------------------
       JEJAK (GARIS TIPIS)
       Employed → kuning, Onlooker → fuchsia
    --------------------------------------------------------- */
    strokeWeight(2);
    if (idx < jumlahEmployedTerakhir) {
      stroke(255, 255, 0, 160);     // 💛 kuning terang
    } else {
      stroke(255, 0, 255, 160);     // 💗 fuchsia terang
    }

    noFill();
    beginShape();
    for (let t = 0; t <= posInt; t++) {
      const s = b.jalur[t];
      const x = s.i * UKURAN_SEL + UKURAN_SEL / 2;
      const y = s.j * UKURAN_SEL + UKURAN_SEL / 2;
      vertex(x, y);
    }
    endShape();

    /* ---------------------------------------------------------
       TITIK LEBAH (BULAT)
       Employed → kuning tebal
       Onlooker → fuchsia tebal
    --------------------------------------------------------- */
    const sNow = b.jalur[posInt];
    const cx = sNow.i * UKURAN_SEL + UKURAN_SEL / 2;
    const cy = sNow.j * UKURAN_SEL + UKURAN_SEL / 2;

    noStroke();
    if (idx < jumlahEmployedTerakhir) {
      fill(255, 255, 0);    // 💛 kuning terang full
    } else {
      fill(255, 0, 255);    // 💗 fuchsia full
    }

    const r = UKURAN_SEL * 0.45;
    ellipse(cx, cy, r, r);
  }
}


/* ====================================================================== */
/*                                 UI                                     */
/* ====================================================================== */

function buatSlider(nama, min, max, nilaiDefault, step, parentDiv, liveCallback) {
  const container = createDiv();
  container.style('margin-bottom', '10px');

  const labelRow = createDiv();
  labelRow.style('display', 'flex');
  labelRow.style('justify-content', 'space-between');
  labelRow.style('margin-bottom', '5px');
  labelRow.style('font-size', '14px');

  const label = createSpan(nama + ': ');
  const valueLabel = createSpan(String(nilaiDefault));

  label.parent(labelRow);
  valueLabel.parent(labelRow);
  labelRow.parent(container);

  const slider = createSlider(min, max, nilaiDefault, step);
  slider.style('width', '100%');
  slider.parent(container);

  slider.input(() => {
    let val = slider.value();
    if (step < 1) val = Number(val).toFixed(2);
    valueLabel.html(val);
    if (liveCallback) liveCallback(slider.value());
  });

  container.parent(parentDiv);

  ui.sliders[nama] = slider;
  ui.labels[nama] = valueLabel;
}

function buatTombol(nama, parentDiv, callback) {
  const button = createButton(nama);
  button.style('width', '100%');
  button.style('padding', '10px');
  button.style('margin-top', '10px');
  button.style('background-color', '#007bff');
  button.style('color', '#fff');
  button.style('border', 'none');
  button.style('border-radius', '4px');
  button.style('cursor', 'pointer');
  button.style('font-size', '15px');
  button.style('font-weight', 'bold');
  button.parent(parentDiv);
  button.mousePressed(callback);
  return button;
}

/* ====================================================================== */
/*                      RESET Labirin + Koloni                            */
/* ====================================================================== */

function resetMazeAndColony() {
  KOLOM = Math.max(2, Math.floor(width / UKURAN_SEL));
  BARIS = Math.max(2, Math.floor(height / UKURAN_SEL));

  bufferLabirin = createGraphics(width, height);

  buatLabirinDanGraf();
  gambarLabirinKeBuffer();
  inisialisasiLebah();
}

/* ====================================================================== */
/*                            p5.js SETUP & DRAW                          */
/* ====================================================================== */

function setup() {
  // Atur body & panel hanya sekali
  if (!ui.menuPanel) {
    const body = select('body');
    if (body) {
      body.style('display', 'flex');
      body.style('margin', '0');
      body.style('padding', '0');
      body.style('overflow', 'hidden');
    }

    ui.menuPanel = createDiv();
    ui.menuPanel.style('width', LEBAR_MENU + 'px');
    ui.menuPanel.style('height', '100vh');
    ui.menuPanel.style('background', '#111');
    ui.menuPanel.style('color', '#eee');
    ui.menuPanel.style('padding', '15px');
    ui.menuPanel.style('box-sizing', 'border-box');
    ui.menuPanel.style('overflow-y', 'auto');
    ui.menuPanel.style('font-family', 'sans-serif');

    ui.mazePanel = createDiv();
    ui.mazePanel.style('flex', '1');
    ui.mazePanel.style('height', '100vh');
    ui.mazePanel.style('position', 'relative');
    ui.mazePanel.style('background', '#000');

    const judul = createElement('h3', 'Kontrol ABC (Bee Colony)');
    judul.style('margin-top', '0');
    judul.style('border-bottom', '1px solid #444');
    judul.style('padding-bottom', '5px');
    judul.parent(ui.menuPanel);

    const deskripsi = createP(
      'Lebah mencari jalur terpendek dari start (hijau) ke goal (biru) di dalam labirin. ' +
      'Employed = kuning, onlooker = oranye. Jejak tipis menunjukkan jalur yang sedang dieksplorasi.'
    );
    deskripsi.style('font-size', '13px');
    deskripsi.style('line-height', '1.4');
    deskripsi.parent(ui.menuPanel);

    // Slider jumlah lebah
    buatSlider('NLebah', 5, 80, JUMLAH_LEBAH, 1, ui.menuPanel, (val) => {
      JUMLAH_LEBAH = int(val);
      inisialisasiLebah();
    });

    // Slider proporsi employed
    buatSlider('PropEmployed', 0, 1, PROP_EMPLOYED, 0.05, ui.menuPanel, (val) => {
      PROP_EMPLOYED = float(val);
    });

    // Slider limit trial
    buatSlider('LimitTrial', 5, 200, LIMIT_TRIAL, 1, ui.menuPanel, (val) => {
      LIMIT_TRIAL = int(val);
    });

    const restartTitle = createElement('h4', 'Generate Maze Baru');
    restartTitle.style('margin-top', '30px');
    restartTitle.style('margin-bottom', '10px');
    restartTitle.style('border-bottom', '1px solid #444');
    restartTitle.style('padding-bottom', '5px');
    restartTitle.parent(ui.menuPanel);

    // Slider peluang loop
    buatSlider('PLoop', 0, 0.5, PELUANG_BUAT_LOOP, 0.01, ui.menuPanel, (val) => {
      PELUANG_BUAT_LOOP = float(val);
    });

    ui.button = buatTombol('Buat Ulang Labirin', ui.menuPanel, resetMazeAndColony);
  }

  // Kanvas utama
  const canvasW = windowWidth - LEBAR_MENU;
  const canvasH = windowHeight;
  const c = createCanvas(canvasW, canvasH);
  c.parent(ui.mazePanel);

  // Generate pertama
  resetMazeAndColony();
}

function draw() {
  // Gambar labirin statis
  if (bufferLabirin) {
    image(bufferLabirin, 0, 0);
  } else {
    background(30);
  }

  // Blokir user
  gambarBlokir();

  // Jalankan iterasi ABC lebih jarang (tiap FREKUENSI_ABC frame)
  if (frameCount % FREKUENSI_ABC === 0) {
    jalankanSiklusLebah(1);
  }

  // Jalur terbaik global
  gambarJalurTerbaik();

  // Visualisasi lebah + jejak
  gambarLebah();

  // Start dan goal
  gambarTitikAwalAkhir();
}

/* ====================================================================== */
/*                         Interaksi mouse                                */
/* ====================================================================== */

function mousePressed() {
  // Pastikan klik di dalam kanvas (bukan di panel kiri)
  if (mouseX < 0 || mouseX >= width || mouseY < 0 || mouseY >= height) return;

  const i = Math.floor(mouseX / UKURAN_SEL);
  const j = Math.floor(mouseY / UKURAN_SEL);
  const sel = ambilSel(i, j);
  if (!sel) return;

  // Jangan blokir start / goal
  if (sel === mulai || sel === akhir) return;

  sel.terblokir = !sel.terblokir;

  // Konfigurasi blokir berubah → reset koloni
  inisialisasiLebah();
}
