/* === VARIABEL GLOBAL & KONFIGURASI === */

let grid = []; 
let paraSemut = [];
let mulai; 
let ui = { sliders: {}, labels: {} }; 

// --- Variabel Fitur ---
let nodeYangDitekan = null; // Drag & Drop
let modeGempa = false;      // Gempa Bumi
let MODE_KOMPLIT = false;   // Checkbox Graf Komplit
let historyStatistik = [];  // Data Grafik

// --- Solusi Terbaik ---
let jalurTerbaik = []; 
let panjangTerbaik = Infinity; 
let loopTerbaik = false; 

// --- Parameter Graf ---
let JUMLAH_SIMPUL = 20; // Default diturunkan sedikit agar Graf Komplit tidak terlalu berat
let MAX_JARAK_KONEKSI = 600; 

// --- Parameter ACO ---
let DEF_JUMLAH_SEMUT = 40; 
let DEF_ALFA = 2.5; 
let DEF_BETA = 2.0; 
let DEF_TINGKAT_PENGUAPAN = 0.90; 
let DEF_DEPOSIT_FEROMON = 3000.0; 
let DEF_FEROMON_MIN = 1.0; 

// --- Live Variables ---
let JUMLAH_SEMUT = DEF_JUMLAH_SEMUT; 
let ALFA = DEF_ALFA; 
let BETA = DEF_BETA;
let TINGKAT_PENGUAPAN = DEF_TINGKAT_PENGUAPAN; 
let DEPOSIT_FEROMON = DEF_DEPOSIT_FEROMON; 


/* ====================================================================== */
/* === KELAS SEL (SIMPUL) === */
/* ====================================================================== */
class Sel {
    constructor(id, x, y) {
        this.id = id;
        this.x = x; 
        this.y = y; 
        this.koneksi = []; 
        this.dihapus = false;
    }

    tampilkanSimpul() {
        if (this.dihapus) return; 

        let ukuran = 12; 
        
        if (this === mulai) {
            fill(0, 255, 150); 
            stroke(255);
            strokeWeight(2);
        } else if (this === nodeYangDitekan) {
            fill(255, 200, 0); 
            stroke(255);
            strokeWeight(2);
            ukuran = 15;
        } else {
            fill(255); 
            stroke(0);
            strokeWeight(1.5);
        }
        
        ellipse(this.x, this.y, ukuran);
    }
    
    tampilkanTepi() {
        if (this.dihapus) return; 

        for (let koneksi of this.koneksi) {
            let tetangga = koneksi.simpul;
            if (tetangga.dihapus) continue;
            
            if (this.id < tetangga.id) {
                let feromon = koneksi.feromon;
                
                // Visualisasi: Jika Mode Komplit, garis tipis dibuat lebih transparan
                // agar tidak menutupi layar
                let minAlpha = MODE_KOMPLIT ? 10 : 40; 

                let level = map(Math.log(feromon), Math.log(DEF_FEROMON_MIN), Math.log(5000), 0, 1);
                level = constrain(level, 0, 1);

                let alpha = map(level, 0, 1, minAlpha, 255); 
                let bobotGaris = map(level, 0, 1, 1, 5); 
                
                stroke(0, 200, 0, alpha); 
                strokeWeight(bobotGaris);
                
                line(this.x, this.y, tetangga.x, tetangga.y);
            }
        }
    }

    ambilTetanggaValid(sudahDikunjungi) {
        return this.koneksi
            .map(k => k.simpul)
            .filter(n => !n.dihapus && !sudahDikunjungi.has(n));
    }
    
    ambilKoneksiKe(tetanggaSel) {
        return this.koneksi.find(k => k.simpul === tetanggaSel);
    }

    ambilBobotKe(tetanggaSel) {
        let koneksi = this.ambilKoneksiKe(tetanggaSel);
        return koneksi ? koneksi.bobot : Infinity;
    }
}


/* ====================================================================== */
/* === KELAS SEMUT === */
/* ====================================================================== */
class Semut {
    constructor() {
        this.aturUlang();
    }

    aturUlang() {
        let startNode = (!mulai || mulai.dihapus) ? grid.find(s => !s.dihapus) : mulai;

        if (startNode) {
            this.selSaatIni = startNode; 
            this.jalur = [startNode]; 
            this.sudahDikunjungi = new Set();
            this.sudahDikunjungi.add(startNode);
            this.gagal = false; 
        } else {
            this.gagal = true; 
        }
    }

    perbarui() {
        if (!this.selSaatIni || this.gagal) {
            this.aturUlang();
            return;
        }
        this.jelajahi();
    }

    jelajahi() {
        const simpulAktifCount = grid.filter(s => !s.dihapus).length; 
        
        if (this.sudahDikunjungi.size >= simpulAktifCount) {
            let koneksiKeAwal = this.selSaatIni.ambilKoneksiKe(this.jalur[0]);
            if (koneksiKeAwal) {
                this.jalur.push(this.jalur[0]); 
                this.depositFeromon(true); 
                this.aturUlang(); 
            } else {
                this.aturUlang();
            }
            return;
        }

        let gerakanMungkin = this.selSaatIni.ambilTetanggaValid(this.sudahDikunjungi);

        if (gerakanMungkin.length > 0) {
            let probabilitas = [];
            let totalDayaTarik = 0; 
            
            for (const gerakan of gerakanMungkin) {
                const bobotTepi = this.selSaatIni.ambilBobotKe(gerakan); 
                const heuristik = pow(1.0 / bobotTepi, BETA); 
                const koneksi = this.selSaatIni.ambilKoneksiKe(gerakan);
                const feromon = pow(koneksi.feromon, ALFA); 
                
                const dayaTarik = feromon * heuristik;
                probabilitas.push({ sel: gerakan, value: dayaTarik });
                totalDayaTarik += dayaTarik;
            }

            let pilihan = null;
            let r = random(totalDayaTarik);
            let kumulatif = 0;

            for (const p of probabilitas) {
                kumulatif += p.value;
                if (r <= kumulatif) {
                    pilihan = p.sel;
                    break;
                }
            }
            
            if (!pilihan) pilihan = random(gerakanMungkin);

            this.selSaatIni = pilihan;
            this.jalur.push(this.selSaatIni); 
            this.sudahDikunjungi.add(this.selSaatIni); 

        } else {
            this.aturUlang(); 
        }
    }

    depositFeromon(sukses) {
        if (!sukses) return; 
        
        let totalPanjangJalur = 0;
        for(let k = 0; k < this.jalur.length - 1; k++) {
            totalPanjangJalur += this.jalur[k].ambilBobotKe(this.jalur[k+1]); 
        }

        if (totalPanjangJalur < panjangTerbaik) {
            panjangTerbaik = totalPanjangJalur;
            jalurTerbaik = [...this.jalur]; 
            loopTerbaik = true;
        }
        
        const jumlah = DEPOSIT_FEROMON / totalPanjangJalur; 
        
        for(let k = 0; k < this.jalur.length - 1; k++) {
            const simpulA = this.jalur[k];
            const simpulB = this.jalur[k+1];
            
            const koneksiAB = simpulA.ambilKoneksiKe(simpulB);
            const koneksiBA = simpulB.ambilKoneksiKe(simpulA);

            if (koneksiAB) koneksiAB.feromon = min(koneksiAB.feromon + jumlah, 10000);
            if (koneksiBA) koneksiBA.feromon = min(koneksiBA.feromon + jumlah, 10000);
        }
    }

    tampilkan() {
        if (!this.selSaatIni || this.gagal) return; 
        const ukuran = 8;
        fill(255, 50, 50, 200); 
        noStroke();
        ellipse(this.selSaatIni.x, this.selSaatIni.y, ukuran);
    }
}

/* ====================================================================== */
/* === FUNGSI GENERATOR GRAF === */
/* ====================================================================== */
function buatGrafPlanar() {
    if (grid.length !== JUMLAH_SIMPUL || grid.length === 0) {
        grid = [];
        for (let i = 0; i < JUMLAH_SIMPUL; i++) {
            let x = random(50, width - 50);
            let y = random(50, height - 50);
            grid.push(new Sel(i, x, y));
        }
    }
    
    mulai = grid[0];
    jalurTerbaik = [];
    panjangTerbaik = Infinity;
    historyStatistik = []; 
    
    for (let s of grid) s.koneksi = [];

    // 1. Hubungkan berdasarkan radius ATAU Mode Komplit
    for (let i = 0; i < grid.length; i++) {
        let s1 = grid[i];
        if (s1.dihapus) continue;
        
        for (let j = i + 1; j < grid.length; j++) {
            let s2 = grid[j];
            if (s2.dihapus) continue;

            let d = dist(s1.x, s1.y, s2.x, s2.y);
            
            // === LOGIKA UTAMA CHECKBOX GRAF KOMPLIT ===
            // Jika MODE_KOMPLIT aktif, abaikan jarak. Jika tidak, pakai MAX_JARAK_KONEKSI
            if (MODE_KOMPLIT || d < MAX_JARAK_KONEKSI) {
                s1.koneksi.push({ simpul: s2, bobot: d, feromon: DEF_FEROMON_MIN });
                s2.koneksi.push({ simpul: s1, bobot: d, feromon: DEF_FEROMON_MIN });
            }
        }
    }

    // 2. JAMINAN KONEKTIVITAS (Hanya perlu jika TIDAK mode komplit)
    if (!MODE_KOMPLIT) {
        for (let i = 0; i < grid.length; i++) {
            let s1 = grid[i];
            if (s1.dihapus) continue;

            if (s1.koneksi.length < 2) {
                let kandidat = [];
                for (let j = 0; j < grid.length; j++) {
                    if (i === j || grid[j].dihapus) continue;
                    let d = dist(s1.x, s1.y, grid[j].x, grid[j].y);
                    kandidat.push({ s: grid[j], d: d });
                }
                kandidat.sort((a, b) => a.d - b.d);
                
                for (let k = 0; k < min(2, kandidat.length); k++) {
                    let target = kandidat[k].s;
                    let jarak = kandidat[k].d;
                    
                    if (!s1.ambilKoneksiKe(target)) {
                        s1.koneksi.push({ simpul: target, bobot: jarak, feromon: DEF_FEROMON_MIN });
                        target.koneksi.push({ simpul: s1, bobot: jarak, feromon: DEF_FEROMON_MIN });
                    }
                }
            }
        }
    }
    
    if (mulai && mulai.dihapus) mulai = grid.find(s => !s.dihapus);
}

/* ====================================================================== */
/* === UPDATE FEROMON & FITUR BARU === */
/* ====================================================================== */

function perbaruiFeromon() {
    for (let simpul of grid) {
        if (simpul.dihapus) continue;
        for (let koneksi of simpul.koneksi) {
            let feromonLama = koneksi.feromon;
            let feromonBaru = max(DEF_FEROMON_MIN, feromonLama * TINGKAT_PENGUAPAN); 
            koneksi.feromon = feromonBaru;
        }
    }
}

function updateDanGambarStatistik() {
    if (frameCount % 10 === 0 && panjangTerbaik !== Infinity) {
        historyStatistik.push(panjangTerbaik);
        if (historyStatistik.length > 200) historyStatistik.shift(); 
    }

    if (historyStatistik.length > 1) {
        let xPos = 10;
        let yPos = height - 10;
        let chartW = 200;
        let chartH = 100;

        fill(0, 0, 0, 150);
        noStroke();
        rect(xPos, yPos - chartH, chartW, chartH);

        noFill();
        stroke(0, 255, 255);
        strokeWeight(2);
        
        let maxVal = max(historyStatistik);
        let minVal = min(historyStatistik);
        
        beginShape();
        for (let i = 0; i < historyStatistik.length; i++) {
            let x = map(i, 0, historyStatistik.length - 1, xPos, xPos + chartW);
            // Cegah pembagian nol jika min == max
            let range = (maxVal - minVal) || 1; 
            let y = map(historyStatistik[i], minVal, maxVal, yPos - 10, yPos - chartH + 10);
            vertex(x, y);
        }
        endShape();

        fill(255);
        noStroke();
        textSize(10);
        textAlign(LEFT);
        text("Statistik Jarak Terbaik", xPos + 5, yPos - chartH - 5);
    }
}

function efekGempaBumi() {
    if (modeGempa) {
        for (let s of grid) {
            s.x += random(-3, 3);
            s.y += random(-3, 3);
            s.x = constrain(s.x, 10, width-10);
            s.y = constrain(s.y, 10, height-10);
            
            for (let koneksi of s.koneksi) {
                let tetangga = koneksi.simpul;
                let d = dist(s.x, s.y, tetangga.x, tetangga.y);
                koneksi.bobot = d;
                let koneksiBalik = tetangga.ambilKoneksiKe(s);
                if (koneksiBalik) koneksiBalik.bobot = d;
            }
        }
        if (frameCount % 10 === 0) {
            panjangTerbaik = Infinity;
            jalurTerbaik = [];
        }
    }
}

function gambarJalurTerbaik() {
    if (jalurTerbaik.length < 2) return;
    
    stroke(255, 255, 0); 
    strokeWeight(4); 
    noFill();
    
    beginShape();
    for (let s of jalurTerbaik) vertex(s.x, s.y);
    endShape();
    
    fill(255);
    noStroke();
    textSize(16);
    textAlign(RIGHT, TOP);
    let teks = panjangTerbaik !== Infinity ? `Jarak: ${panjangTerbaik.toFixed(0)} px` : "Mencari...";
    text(teks, width - 10, 10);
}

function aturJumlahSemut(jumlahBaru) {
    let jumlahLama = paraSemut.length;
    jumlahBaru = int(jumlahBaru);
    if (jumlahBaru > jumlahLama) {
        for (let i = 0; i < (jumlahBaru - jumlahLama); i++) paraSemut.push(new Semut());
    } else if (jumlahBaru < jumlahLama) {
        paraSemut = paraSemut.slice(0, jumlahBaru);
    }
    JUMLAH_SEMUT = jumlahBaru;
}

/* ====================================================================== */
/* === UI SETUP === */
/* ====================================================================== */

function buatSlider(nama, min, max, nilaiDefault, step, liveCallback, parentId = 'ui-sliders') {
    let parentDiv = select('#' + parentId);
    if (!parentDiv) return;

    let container = createDiv().class('slider-container');
    let labelContainer = createDiv().class('label-container');
    
    let label = createSpan(nama + ': ');
    let valueLabel = createSpan(nilaiDefault); 
    
    label.parent(labelContainer);
    valueLabel.parent(labelContainer);
    labelContainer.parent(container);

    let slider = createSlider(min, max, nilaiDefault, step);
    slider.style('width', '100%');
    slider.parent(container);

    slider.input(() => {
        let val = slider.value();
        valueLabel.html(val);
        if (liveCallback) liveCallback(val);
    });

    container.parent(parentDiv);
    ui.sliders[nama] = slider;
}

function buatTombol(nama, callback, parentId = 'ui-sliders') {
    let parentDiv = select('#' + parentId);
    let button = createButton(nama);
    button.parent(parentDiv);
    button.mousePressed(callback);
    button.style('margin-top', '10px');
    button.style('width', '100%');
    return button;
}

// --- FUNGSI BARU: CHECKBOX ---
function buatCheckbox(label, valAwal, callback, parentId = 'ui-sliders') {
    let cb = createCheckbox(' ' + label, valAwal);
    cb.parent(parentId);
    cb.style('color', 'white');
    cb.style('margin-top', '10px');
    cb.style('display', 'block');
    cb.changed(() => {
        callback(cb.checked());
    });
    return cb;
}

function setup() {
    let canvasW = windowWidth - 300; 
    let canvasH = windowHeight;
    let canvas = createCanvas(canvasW, canvasH);
    canvas.parent('maze-panel'); 
    
    if (Object.keys(ui.sliders).length === 0) {
        buatSlider('NSemut', 1, 100, DEF_JUMLAH_SEMUT, 1, v => aturJumlahSemut(v));
        buatSlider('Alfa (Jejak)', 0.1, 5, DEF_ALFA, 0.1, v => ALFA = v);
        buatSlider('Beta (Jarak)', 0.1, 5, DEF_BETA, 0.1, v => BETA = v);
        buatSlider('Penguapan', 0.8, 1, DEF_TINGKAT_PENGUAPAN, 0.001, v => TINGKAT_PENGUAPAN = v);
        
        select('#ui-sliders').child(createElement('h4', 'Kontrol Graf').style('margin-top', '20px'));
        
        buatSlider('Jml Simpul', 5, 80, JUMLAH_SIMPUL, 1, v => {
            if (v !== grid.length) { JUMLAH_SIMPUL = v; grid = []; setup(); }
        });
        
        // Slider Jarak tetap ada, tapi tidak berpengaruh jika Checkbox aktif
        buatSlider('Jarak Koneksi', 50, 1000, MAX_JARAK_KONEKSI, 10, v => {
            MAX_JARAK_KONEKSI = v; 
            if (!MODE_KOMPLIT) buatGrafPlanar(); // Hanya update jika mode komplit mati
        });
        
        // --- CHECKBOX BARU ---
        buatCheckbox('Graf Komplit (All-to-All)', false, (val) => {
            MODE_KOMPLIT = val;
            buatGrafPlanar(); // Rebuild graf
            // Reset semut agar tidak error path
            paraSemut.forEach(s => s.aturUlang());
            jalurTerbaik = [];
            panjangTerbaik = Infinity;
        });

        // --- TOMBOL GEMPA ---
        let btnGempa = buatTombol('MODE GEMPA: MATI', function() {
            modeGempa = !modeGempa;
            this.html(modeGempa ? 'MODE GEMPA: AKTIF' : 'MODE GEMPA: MATI');
            if (modeGempa) this.style('background-color', '#e74c3c');
            else this.style('background-color', '#007bff');
        });
        
        buatTombol('Reset Graf', setup);
    }
    
    buatGrafPlanar();
    paraSemut = [];
    aturJumlahSemut(JUMLAH_SEMUT);
}

function draw() {
    background(30, 30, 30); 

    efekGempaBumi();

    for (let simpul of grid) simpul.tampilkanTepi();
    for (let simpul of grid) simpul.tampilkanSimpul();
    gambarJalurTerbaik();
    
    let steps = 10;
    for(let n=0; n<steps; n++) {
        for (let semut of paraSemut) semut.perbarui();
    }
    for (let semut of paraSemut) semut.tampilkan();
    
    perbaruiFeromon(); 
    
    updateDanGambarStatistik();
}

/* ====================================================================== */
/* === INTERAKSI MOUSE (DRAG & DROP) === */
/* ====================================================================== */

function mousePressed() {
    if (mouseX < 0 || mouseX > width || mouseY < 0 || mouseY > height) return;
    
    for (let i = grid.length - 1; i >= 0; i--) {
        let s = grid[i];
        if (dist(mouseX, mouseY, s.x, s.y) < 15) {
            nodeYangDitekan = s;
            return; 
        }
    }
}

function mouseDragged() {
    if (nodeYangDitekan) {
        nodeYangDitekan.x = constrain(mouseX, 10, width - 10);
        nodeYangDitekan.y = constrain(mouseY, 10, height - 10);
        
        for (let koneksi of nodeYangDitekan.koneksi) {
            let tetangga = koneksi.simpul;
            let d = dist(nodeYangDitekan.x, nodeYangDitekan.y, tetangga.x, tetangga.y);
            koneksi.bobot = d;
            let koneksiBalik = tetangga.ambilKoneksiKe(nodeYangDitekan);
            if (koneksiBalik) koneksiBalik.bobot = d;
        }
        
        if (frameCount % 5 === 0) { 
            panjangTerbaik = Infinity;
            jalurTerbaik = [];
        }
    }
}

function mouseReleased() {
    nodeYangDitekan = null;
}

function windowResized() {
    setup(); 
}