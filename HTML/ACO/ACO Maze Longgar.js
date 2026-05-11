/* === VARIABEL GLOBAL === */
let grid = [];
let paraSemut = [];
let mulai, akhir;
let tumpukan = [];
let bufferLabirin; 

// --- Variabel Parameter Awal (Default) ---
let DEF_JUMLAH_SEMUT = 15; 
let DEF_PELUANG_LOOP = 0.05;
let DEF_ALFA = 2.5; 
let DEF_BETA = 0.5;
let DEF_TINGKAT_PENGUAPAN = 0.01; 
let DEF_DEPOSIT_FEROMON = 500.0; 
let DEF_FEROMON_MIN = 0.01; // Tetap ada sebagai nilai default

// --- Variabel Parameter LIVE (akan di-update dari slider) ---
let KOLOM, BARIS;
let UKURAN_SEL = 25; 
let JUMLAH_SEMUT = DEF_JUMLAH_SEMUT; 
let PELUANG_BUAT_LOOP = DEF_PELUANG_LOOP;
let ALFA = DEF_ALFA; 
let BETA = DEF_BETA;
let TINGKAT_PENGUAPAN = DEF_TINGKAT_PENGUAPAN; 
let DEPOSIT_FEROMON = DEF_DEPOSIT_FEROMON; 
let FEROMON_MIN = DEF_FEROMON_MIN; // Gunakan nilai default

// === KODE BARU: Objek untuk UI & Layout ===
let LEBAR_MENU = 300; // Lebar panel menu di kiri (dalam pixel)
let ui = {
    sliders: {},
    labels: {},
    button: null,
    menuPanel: null, // Div panel kiri
    mazePanel: null  // Div panel kanan (untuk kanvas)
};
/* ====================================================================== */
/* === KELAS SEL (SIMPUL GRAF) === */
/* ====================================================================== */
class Sel {
    constructor(i, j) {
        this.i = i; 
        this.j = j; 
        
        // --- Bagian Labirin ---
        this.dinding = { atas: true, kanan: true, bawah: true, kiri: true };
        this.sudahDikunjungi = false; 

        // --- Bagian GRAF (INI KUNCINYA) ---
        this.tetangga = []; 
        
        // --- Bagian ACO ---
        this.feromon = FEROMON_MIN; 
        this.jarakKeAkhir = 0; 
        
        // --- Bagian Blokir ---
        this.terblokir = false;
    }

    // Gambar dinding labirin (ke buffer off-screen)
    tampilkanDinding(buffer) {
        let x = this.i * UKURAN_SEL;
        let y = this.j * UKURAN_SEL;
        buffer.stroke(255); 
        buffer.strokeWeight(2);
        buffer.strokeCap(PROJECT); 

        if (this.dinding.atas) buffer.line(x, y, x + UKURAN_SEL, y);
        if (this.dinding.kanan) buffer.line(x + UKURAN_SEL, y, x + UKURAN_SEL, y + UKURAN_SEL);
        if (this.dinding.bawah) buffer.line(x, y + UKURAN_SEL, x + UKURAN_SEL, y + UKURAN_SEL);
        if (this.dinding.kiri) buffer.line(x, y, x, y + UKURAN_SEL);
    }

    // Gambar feromon (ke kanvas utama)
    tampilkanFeromon() {
        if (this.feromon > FEROMON_MIN) { 
            let x = this.i * UKURAN_SEL;
            let y = this.j * UKURAN_SEL;
            
            // Logika warna (Hijau dengan transparansi)
            let r = 0; 
            let g = 255; 
            let b = 0; 
            let alpha = map(this.feromon, FEROMON_MIN, 100, 10, 220);
            alpha = constrain(alpha, 10, 220);
            fill(r, g, b, alpha); 
            
            noStroke();
            rect(x, y, UKURAN_SEL, UKURAN_SEL);
        }
    }

    // Untuk generator labirin: Cari tetangga yang belum dikunjungi
    cekTetangga() {
        let daftarTetangga = [];
        let atas = ambilSel(this.i, this.j - 1);
        let kanan = ambilSel(this.i + 1, this.j);
        let bawah = ambilSel(this.i, this.j + 1); // <<< INI SUDAH DIPERBAIKI
        let kiri = ambilSel(this.i - 1, this.j);

        if (atas && !atas.sudahDikunjungi) daftarTetangga.push(atas);
        if (kanan && !kanan.sudahDikunjungi) daftarTetangga.push(kanan);
        if (bawah && !bawah.sudahDikunjungi) daftarTetangga.push(bawah);
        if (kiri && !kiri.sudahDikunjungi) daftarTetangga.push(kiri);

        if (daftarTetangga.length > 0) {
            return random(daftarTetangga); 
        } else {
            return undefined;
        }
    }
    
    // Helper untuk buatLoop(): Dapatkan tetangga YANG MASIH BERDINDING
    cekTetanggaBerdinding() { 
        let daftarTetangga = [];
        let atas = ambilSel(this.i, this.j - 1);
        let kanan = ambilSel(this.i + 1, this.j);
        let bawah = ambilSel(this.i, this.j + 1);
        let kiri = ambilSel(this.i - 1, this.j);

        if (atas && this.dinding.atas) daftarTetangga.push(atas);
        if (kanan && this.dinding.kanan) daftarTetangga.push(kanan);
        if (bawah && this.dinding.bawah) daftarTetangga.push(bawah);
        if (kiri && this.dinding.kiri) daftarTetangga.push(kiri);

        if (daftarTetangga.length > 0) {
            return random(daftarTetangga);
        } else {
            return undefined;
        }
    }
}

/* ====================================================================== */
/* === KELAS SEMUT (AGEN ACO) === */
/* ====================================================================== */
class Semut {
    constructor() {
        this.aturUlang();
    }

    // Kembalikan semut ke titik awal
    aturUlang() {
        this.selSaatIni = mulai; 
        this.jalur = [mulai]; 
        this.sudahDikunjungiDiPerjalananIni = new Set();
        this.sudahDikunjungiDiPerjalananIni.add(mulai);
    }

    // perbarui() akan dipanggil BEBERAPA KALI per frame
    perbarui() {
        this.jelajahi();
    }

    // LOGIKA INTI ACO: Menjelajah (Dengan logika mundur/backtrack)
    jelajahi() {
        if (!this.selSaatIni) { 
            this.aturUlang();
            return;
        }
        
        // Saring tetangga yang sudah dikunjungi ATAU yang diblokir
        let gerakanMungkin = this.selSaatIni.tetangga.filter(
            (n) => !this.sudahDikunjungiDiPerjalananIni.has(n) && !n.terblokir 
        );

        // === KONDISI A: ADA JALAN MAJU (Normal) ===
        if (gerakanMungkin.length > 0) {
            
            let probabilitas = [];
            let totalDayaTarik = 0; 

            for (let gerakan of gerakanMungkin) {
                let jarakKeAkhir = gerakan.jarakKeAkhir; 
                let heuristik = pow(1.0 / (jarakKeAkhir + 1), BETA); // <-- Gunakan var LIVE
                let feromon = pow(gerakan.feromon, ALFA); // <-- Gunakan var LIVE
                let dayaTarik = feromon * heuristik;
                
                probabilitas.push({ sel: gerakan, value: dayaTarik });
                totalDayaTarik += dayaTarik;
            }

            let pilihanAcak = random(totalDayaTarik);
            let kumulatif = 0;
            let selBerikutnya = gerakanMungkin[gerakanMungkin.length - 1]; 

            for (let p of probabilitas) {
                kumulatif += p.value;
                if (pilihanAcak <= kumulatif) {
                    selBerikutnya = p.sel;
                    break;
                }
            }
            
            this.selSaatIni = selBerikutnya;
            this.jalur.push(this.selSaatIni); 
            this.sudahDikunjungiDiPerjalananIni.add(this.selSaatIni); 
            
        // === KONDISI B: JALAN BUNTU (Harus Mundur/Backtrack) ===
        } else {
            this.jalur.pop(); 
            if (this.jalur.length > 0) {
                this.selSaatIni = this.jalur[this.jalur.length - 1]; 
            } else {
                this.aturUlang(); 
            }
        }

        // CEK APAKAH SUDAH SAMPAI DI AKHIR
        if (this.selSaatIni === akhir) {
            this.depositFeromon(); 
            this.aturUlang(); 
        }
    }

    // LOGIKA FEROMON: Jatuhkan setelah sukses
    depositFeromon() {
        let jumlah = DEPOSIT_FEROMON / this.jalur.length; // <-- Gunakan var LIVE
        for (let sel of this.jalur) {
            sel.feromon = min(sel.feromon + jumlah, 500);
        }
    }

    // Gambar semut (lingkaran merah kecil)
    tampilkan() {
        if (!this.selSaatIni) return; 
        let x = this.selSaatIni.i * UKURAN_SEL + UKURAN_SEL / 2;
        let y = this.selSaatIni.j * UKURAN_SEL + UKURAN_SEL / 2;
        fill(255, 0, 0, 220); 
        noStroke();
        ellipse(x, y, UKURAN_SEL * 0.5);
    }
}

/* ====================================================================== */
/* === FUNGSI BANTU LIVE UPDATE (KODE BARU) === */
/* ====================================================================== */

// Fungsi ini menangani penambahan/pengurangan semut secara 'live'
function aturJumlahSemut(jumlahBaru) {
    let jumlahLama = paraSemut.length;
    jumlahBaru = int(jumlahBaru); // Pastikan nilainya integer

    if (jumlahBaru > jumlahLama) {
        // Jika jumlah baru lebih banyak, tambahkan semut baru
        for (let i = 0; i < (jumlahBaru - jumlahLama); i++) {
            paraSemut.push(new Semut());
        }
    } else if (jumlahBaru < jumlahLama) {
        // Jika jumlah baru lebih sedikit, hapus semut dari array
        for (let i = 0; i < (jumlahLama - jumlahBaru); i++) {
            paraSemut.pop(); // Hapus semut terakhir
        }
    }
    // Update variabel global agar konsisten
    JUMLAH_SEMUT = jumlahBaru;
}

/* ====================================================================== */
/* === FUNGSI BANTU UI === */
/* ====================================================================== */

// buat slider
function buatSlider(nama, min, max, nilaiDefault, step, parentDiv, liveCallback) {
    // --- Kontainer untuk item menu ---
    let container = createDiv();
    container.style('margin-bottom', '10px');
    
    // --- Kontainer untuk label (Nama: Nilai) ---
    let labelContainer = createDiv();
    labelContainer.style('display', 'flex');
    labelContainer.style('justify-content', 'space-between');
    labelContainer.style('margin-bottom', '5px');
    labelContainer.style('font-size', '14px');
    
    let label = createSpan(nama + ': ');
    let valueLabel = createSpan(nilaiDefault); // Label untuk nilai
    
    label.parent(labelContainer);
    valueLabel.parent(labelContainer);
    labelContainer.parent(container);

    // --- Slider ---
    let slider = createSlider(min, max, nilaiDefault, step);
    slider.style('width', '100%'); // Slider mengisi lebar panel
    slider.parent(container);

    // Saat slider digerakkan...
    slider.input(() => {
        let val = slider.value(); // Ambil nilai
        valueLabel.html(val);     // 1. Update label
        
        // 2. Jika ada 'liveCallback', panggil callback itu
        if (liveCallback) {
            liveCallback(val);
        }
    });

    container.parent(parentDiv); // Masukkan ke panel menu
    
    ui.sliders[nama] = slider; // Simpan referensi slider
    ui.labels[nama] = valueLabel; // Simpan referensi label nilai
}

// Fungsi untuk membuat tombol
function buatTombol(nama, parentDiv, callback) {
    let button = createButton(nama);
    button.style('width', '100%');
    button.style('padding', '10px');
    button.style('margin-top', '10px');
    button.style('background-color', '#007bff');
    button.style('color', 'white');
    button.style('border', 'none');
    button.style('border-radius', '4px');
    button.style('cursor', 'pointer');
    button.style('font-size', '15px');
    button.style('font-weight', 'bold');
    
    button.parent(parentDiv);
    button.mousePressed(callback); // Tautkan fungsi callback
    
    return button;
}

/* ====================================================================== */
/* === FUNGSI UTAMA P5.JS === */
/* ====================================================================== */

// Inisialisasi
function setup() {
    
    // === MULAI KODE BARU: Setup Layout & UI ===
    // Cek jika panel belum dibuat biar UI tidak dibuat ulang
    // setiap kali 'setup()' dipanggil oleh tombol restart.
    if (!ui.menuPanel) {
        // 1. Atur 'body' untuk menggunakan Flexbox
        select('body').style('display', 'flex');
        select('body').style('margin', '0');
        select('body').style('padding', '0');
        select('body').style('overflow', 'hidden'); // Sembunyikan scrollbar
        
        // 2. Buat Panel Menu (Kiri)
        ui.menuPanel = createDiv();
        ui.menuPanel.style('width', LEBAR_MENU + 'px');
        ui.menuPanel.style('height', '100vh'); // Setinggi layar
        ui.menuPanel.style('background', '#1c1c1c');
        ui.menuPanel.style('color', 'white');
        ui.menuPanel.style('padding', '15px');
        ui.menuPanel.style('box-sizing', 'border-box'); // Agar padding tidak menambah lebar
        ui.menuPanel.style('overflow-y', 'auto'); // Bisa di-scroll jika menu panjang
        ui.menuPanel.style('font-family', 'sans-serif');

        // 3. Buat Panel Labirin (Kanan)
        ui.mazePanel = createDiv();
        ui.mazePanel.style('flex', '1'); // Mengisi sisa ruang
        ui.mazePanel.style('height', '100vh');
        ui.mazePanel.style('position', 'relative');

        // 4. Buat Judul di Panel Menu
        let judul = createElement('h3', 'Kontrol ACO');
        judul.style('margin-top', '0');
        judul.style('border-bottom', '1px solid #444');
        judul.style('padding-bottom', '10px');
        judul.parent(ui.menuPanel);

        // --- SLIDER LIVE ---
        buatSlider('NSemut', 1, 100, DEF_JUMLAH_SEMUT, 1, ui.menuPanel, (val) => {
            aturJumlahSemut(val);
        });
        
        buatSlider('Alfa', 0.1, 5, DEF_ALFA, 0.1, ui.menuPanel, (val) => {
            ALFA = val;
        });
        
        buatSlider('Beta', 0.1, 5, DEF_BETA, 0.1, ui.menuPanel, (val) => {
            BETA = val;
        });
        
        buatSlider('Penguapan', 0, 0.2, DEF_TINGKAT_PENGUAPAN, 0.001, ui.menuPanel, (val) => {
            TINGKAT_PENGUAPAN = val;
        });

        buatSlider('Deposit', 100, 2000, DEF_DEPOSIT_FEROMON, 50, ui.menuPanel, (val) => {
            DEPOSIT_FEROMON = val;
        });


        // === MULAI SEKSI BARU: Generate Maze ===
        let restartTitle = createElement('h4', 'Generate Maze Baru');
        restartTitle.style('margin-top', '30px'); // Beri jarak lebih besar
        restartTitle.style('margin-bottom', '10px');
        restartTitle.style('border-bottom', '1px solid #444');
        restartTitle.style('padding-bottom', '5px');
        restartTitle.parent(ui.menuPanel);

        // --- SLIDER RESTART (Tanpa Callback dan NAMA BARU) ---
        buatSlider('PLoop', 0, 0.5, DEF_PELUANG_LOOP, 0.01, ui.menuPanel, null); 

        // --- Tombol Restart ---
        ui.button = buatTombol('Buat Ulang Labirin', ui.menuPanel, setup);
    }
    
    // === MULAI KODE BARU: Baca Nilai dari UI ===
    // Ambil nilai TERBARU dari slider dan masukkan ke variabel global.
    // Ini penting untuk 'setup()' pertama kali DAN saat 'restart'.
    JUMLAH_SEMUT = ui.sliders['NSemut'].value();
    PELUANG_BUAT_LOOP = ui.sliders['PLoop'].value();
    ALFA = ui.sliders['Alfa'].value();
    BETA = ui.sliders['Beta'].value();
    TINGKAT_PENGUAPAN = ui.sliders['Penguapan'].value();
    DEPOSIT_FEROMON = ui.sliders['Deposit'].value();
    FEROMON_MIN = DEF_FEROMON_MIN; // <-- Ambil dari default, karena slider dihapus
    

    // === Hitung Ukuran Kanvas ===
    // Lebar dan tinggi kanvas sekarang didasarkan pada panel kanan
    let canvasW = windowWidth - LEBAR_MENU;
    let canvasH = windowHeight;
    
    // Buat kanvas dan tempatkan di panel kanan (mazePanel)
    let canvas = createCanvas(canvasW, canvasH);
    canvas.parent(ui.mazePanel); 
    // === AKHIR MODIFIKASI ===
    
    // 'width' dan 'height' sekarang merujuk ke 'canvasW' dan 'canvasH'
    KOLOM = max(2, floor(width / UKURAN_SEL));
    BARIS = max(2, floor(height / UKURAN_SEL));

    bufferLabirin = createGraphics(width, height);
    bufferLabirin.background(30, 30, 30); 

    grid = [];
    for (let j = 0; j < BARIS; j++) {
        for (let i = 0; i < KOLOM; i++) {
            grid.push(new Sel(i, j));
        }
    }

    // Pastikan titik akhir tidak keluar grid
    mulai = ambilSel(0, 0);
    akhir = ambilSel(KOLOM - 1, BARIS - 1);
    
    // Pastikan 'akhir' valid jika ukuran grid sangat kecil
    if (!akhir) {
        akhir = ambilSel(0, 0);
    }

    // 1. Buat labirin sempurna (1 solusi)
    buatLabirinDanGraf();
    
    // 2. Jebol dinding acak untuk buat loop (banyak solusi)
    //    Menggunakan nilai 'PELUANG_BUAT_LOOP' dari slider
    buatLoop(); 
    
    for (let sel of grid) {
        sel.jarakKeAkhir = dist(sel.i, sel.j, akhir.i, akhir.j);
    }
    
    // 3. Gambar dinding (YANG SUDAH DIJEBOL) ke buffer
    bufferLabirin.background(30, 30, 30); // Reset buffer
    for (let sel of grid) { 
        sel.tampilkanDinding(bufferLabirin);
    }

    paraSemut = [];
    for (let i = 0; i < JUMLAH_SEMUT; i++) {
        paraSemut.push(new Semut());
    }
}

// Loop Animasi Utama (berjalan 60x per detik)
function draw() {
    // 1. Gambar labirin statis (dari buffer, sangat cepat)
    image(bufferLabirin, 0, 0);
    
    // 2. Update & Gambar Feromon
    perbaruiFeromon(); 
    gambarFeromon();   

    // 3. Tandai Titik Awal dan Akhir
    if (akhir) {
        fill(0, 150, 255); 
        noStroke();
        rect(akhir.i * UKURAN_SEL, akhir.j * UKURAN_SEL, UKURAN_SEL, UKURAN_SEL);
    }
    if (mulai) {
        fill(0, 255, 150); 
        noStroke();
        rect(mulai.i * UKURAN_SEL, mulai.j * UKURAN_SEL, UKURAN_SEL, UKURAN_SEL);
    }

    // 4. GAMBAR BLOKIRAN PENGGUNA
    gambarBlokir(); 

    // 5. Update & Gambar Semut
    let siklusPerbarui = 5; 
    for (let i = 0; i < siklusPerbarui; i++) {
        // 'paraSemut.length' akan berubah secara live
        for (let semut of paraSemut) { 
            semut.perbarui();
        }
    }
    
    for (let semut of paraSemut) {
        semut.tampilkan();
    }
}

/* ====================================================================== */
/* === FUNGSI HELPER === */
/* ====================================================================== */

// Menguapkan semua feromon sedikit demi sedikit
function perbaruiFeromon() {
    for (let sel of grid) {
        sel.feromon = max(FEROMON_MIN, sel.feromon * (1-TINGKAT_PENGUAPAN)); 
    }
}

// Menggambar semua feromon
function gambarFeromon() {
    for (let sel of grid) {
        sel.tampilkanFeromon();
    }
}

// Menggambar blok yang dibuat pengguna
function gambarBlokir() { 
    for (let sel of grid) {
        if (sel.terblokir) {
            let x = sel.i * UKURAN_SEL;
            let y = sel.j * UKURAN_SEL;
            fill(80, 80, 80, 200); 
            stroke(0);
            strokeWeight(1);
            rect(x, y, UKURAN_SEL, UKURAN_SEL);
        }
    }
}

// Ambil objek sel dari koordinat (i, j)
function ambilSel(i, j) {
    if (i < 0 || j < 0 || i > KOLOM - 1 || j > BARIS - 1) {
        return undefined;
    }
    return grid[i + j * KOLOM];
}

// GENERATOR LABIRIN (Backtracker Rekursif Iteratif)
function buatLabirinDanGraf() {
    // Reset status 'sudahDikunjungi'
    for (let sel of grid) {
        sel.sudahDikunjungi = false;
    }
    
    let saatIni = mulai;
    if (!saatIni) return; // Pengaman jika 'mulai' tidak valid
    
    saatIni.sudahDikunjungi = true;
    tumpukan = [saatIni]; 

    while (tumpukan.length > 0) {
        saatIni = tumpukan.pop();
        let berikutnya = saatIni.cekTetangga();

        if (berikutnya) {
            tumpukan.push(saatIni);
            hapusDindingDanBangunGraf(saatIni, berikutnya);
            berikutnya.sudahDikunjungi = true;
            tumpukan.push(berikutnya);
        }
    }
}

// Fungsi untuk MENGHAPUS DINDING dan MEMBANGUN GRAF
function hapusDindingDanBangunGraf(a, b) {
    let x = a.i - b.i;
    if (x === 1) {
        a.dinding.kiri = false;
        b.dinding.kanan = false;
    } else if (x === -1) {
        a.dinding.kanan = false;
        b.dinding.kiri = false;
    }

    let y = a.j - b.j; 
    if (y === 1) {
        a.dinding.atas = false;
        b.dinding.bawah = false;
    } else if (y === -1) {
        a.dinding.bawah = false;
        b.dinding.atas = false;
    }
    
    // Hanya tambah tetangga jika belum ada
    if (!a.tetangga.includes(b)) {
        a.tetangga.push(b);
    }
    if (!b.tetangga.includes(a)) {
        b.tetangga.push(a);
    }
}

// === FUNGSI UNTUK MEMBUAT LABIRIN LEBIH LONGGAR ===
function buatLoop() {
    for (let sel of grid) {
        if (random() < PELUANG_BUAT_LOOP) {
            
            // 1. Cari tetangga yang masih terhalang dinding
            let tetanggaBerdinding = sel.cekTetanggaBerdinding();
            
            // 2. Jika ada, jebol dinding itu
            if (tetanggaBerdinding) {
                hapusDindingDanBangunGraf(sel, tetanggaBerdinding);
            }
        }
    }
}


// === FUNGSI BAWAAN P5.JS UNTUK MENDETEKSI KLIK ===
function mousePressed() {
    // Pastikan klik terjadi di dalam area kanvas (panel kanan),
    // bukan di panel menu.
    if (mouseX < 0 || mouseX > width || mouseY < 0 || mouseY > height) {
        return; // Abaikan klik jika di luar kanvas
    }

    // Hitung sel mana yang diklik
    let i = floor(mouseX / UKURAN_SEL);
    let j = floor(mouseY / UKURAN_SEL);
    
    let selYangDiklik = ambilSel(i, j); 

    // Cek apakah kliknya valid (di dalam grid, bukan 'mulai', bukan 'akhir')
    if (selYangDiklik && selYangDiklik !== mulai && selYangDiklik !== akhir) {
        selYangDiklik.terblokir = !selYangDiklik.terblokir; 
    }
}

// === FUNGSI BAWAAN P5.JS (DIMODIFIKASI) ===
function windowResized() {
    // Panggil setup() lagi untuk menghitung ulang ukuran
    // kanvas dan membangun ulang labirin.
    setup(); 
}