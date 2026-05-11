/* === KONFIGURASI === */
let KOLOM, BARIS;
let UKURAN_SEL = 25; 
let JUMLAH_SEMUT = 500; 

// --- Parameter Inti ACO ---
let ALFA = 2.5; // Bobot Feromon (seberapa penting jejak)
let BETA = 0.5;  // Bobot Heuristik (seberapa penting jarak ke 'selesai')
let TINGKAT_PENGUAPAN = 0.99; // Tingkat penguapan (0.99 = CUKUP LAMBAT)
let DEPOSIT_FEROMON = 500.0; // Jumlah total feromon per rute sukses
let FEROMON_MIN = 0.01; // Feromon minimum (agar semut tetap menjelajah)

/* === Variabel Global === */
let grid = [];
let paraSemut = [];
let mulai, selesai;
let tumpukan = [];
let bufferLabirin; 

/* ====================================================================== */
/* === KELAS SEL (NODE GRAF) === */
/* ====================================================================== */
class Sel {
  constructor(i, j) {
    this.i = i; // Kolom (x)
    this.j = j; // Baris (y)
    
    // --- Bagian Labirin ---
    this.dinding = { atas: true, kanan: true, bawah: true, kiri: true };
    this.sudahDikunjungi = false; // Untuk generator labirin

    // --- Bagian GRAF (INI KUNCINYA) ---
    this.tetangga = []; // Daftar tetangga yang terhubung (edge)
    
    // --- Bagian ACO ---
    this.feromon = FEROMON_MIN; // Mulai dengan feromon minimum
    this.jarakKeSelesai = 0; // Heuristik: Jarak ke 'selesai' (dihitung 1x di setup)
    
    // --- Bagian Blokir ---
    this.terblokir = false; // <-- BARU: State untuk menandai blokir
  }

  // Gambar dinding labirin (ke buffer off-screen)
  tampilkanDinding(buffer) {
    let x = this.i * UKURAN_SEL;
    let y = this.j * UKURAN_SEL;
    buffer.stroke(255); // Dinding warna putih
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
      
      // === LOGIKA WARNA (HIJAU + ALPHA) ===
      let r = 0;   
      let g = 255; 
      let b = 0;   
      let alpha = map(this.feromon, FEROMON_MIN, 100, 10, 220);
      alpha = constrain(alpha, 10, 220);
      fill(r, g, b, alpha); // <-- MODIFIKASI: Menggunakan logika hijau saja
      
      noStroke();
      rect(x, y, UKURAN_SEL, UKURAN_SEL);
    }
  }

  // Untuk generator labirin: Dapatkan tetangga yang belum dikunjungi
  cekTetangga() {
    let tetangga = [];
    let atas = ambilSel(this.i, this.j - 1);
    let kanan = ambilSel(this.i + 1, this.j);
    let bawah = ambilSel(this.i, this.j + 1);
    let kiri = ambilSel(this.i - 1, this.j);

    if (atas && !atas.sudahDikunjungi) tetangga.push(atas);
    if (kanan && !kanan.sudahDikunjungi) tetangga.push(kanan);
    if (bawah && !bawah.sudahDikunjungi) tetangga.push(bawah);
    if (kiri && !kiri.sudahDikunjungi) tetangga.push(kiri);

    if (tetangga.length > 0) {
      return random(tetangga); // Pilih satu secara acak
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
    this.sel = mulai; // 'sel' adalah NODE GRAF saat ini
    this.jejak = [mulai]; // Jejak yang ditempuh

    // "Ingatan Jangka Pendek": Melacak node yang dikunjungi HANYA di perjalanan ini
    this.dikunjungiDiPerjalananIni = new Set();
    this.dikunjungiDiPerjalananIni.add(mulai);
  }

  // perbarui() akan dipanggil BEBERAPA KALI per frame
  perbarui() {
    this.jelajahi();
  }

  // LOGIKA INTI ACO: Menjelajah (Dengan logika backtrack yang benar)
  jelajahi() {
    if (!this.sel) { // Pengecekan keamanan jika semut crash
      this.aturUlang();
      return;
    }
    
    // === "PERHITUNGAN ULANG" ADA DI SINI ===
    // Filter tetangga yang sudah dikunjungi ATAU yang diblokir
    let langkahMungkin = this.sel.tetangga.filter(
      (n) => !this.dikunjungiDiPerjalananIni.has(n) && !n.terblokir // <-- MODIFIKASI
    );

    // === KONDISI A: ADA JALAN MAJU (Normal) ===
    if (langkahMungkin.length > 0) {
      
      let probabilitas = [];
      let totalDayaTarik = 0;

      for (let langkah of langkahMungkin) {
        let jarakKeSelesai = langkah.jarakKeSelesai; 
        let heuristik = pow(1.0 / (jarakKeSelesai + 1), BETA);
        let feromon = pow(langkah.feromon, ALFA);
        let dayaTarik = feromon * heuristik;
        
        probabilitas.push({ sel: langkah, value: dayaTarik });
        totalDayaTarik += dayaTarik;
      }

      let pilihanAcak = random(totalDayaTarik);
      let kumulatif = 0;
      let selBerikutnya = langkahMungkin[langkahMungkin.length - 1]; // Fallback

      for (let p of probabilitas) {
        kumulatif += p.value;
        if (pilihanAcak <= kumulatif) {
          selBerikutnya = p.sel;
          break;
        }
      }
      
      this.sel = selBerikutnya;
      this.jejak.push(this.sel); 
      this.dikunjungiDiPerjalananIni.add(this.sel); 
      
    // === KONDISI B: JALAN BUNTU (Harus Mundur/Backtrack) ===
    // NOTE: Jika semut ada di sel yang baru diblokir,
    // langkahMungkin.length akan 0, dan kode ini akan otomatis dijalankan!
    } else {
      // Hapus sel buntu dari jejak
      this.jejak.pop(); 
      
      // Mundur ke sel sebelumnya
      if (this.jejak.length > 0) {
          this.sel = this.jejak[this.jejak.length - 1]; 
      } else {
          // Fallback jika semut terjebak di start
          this.aturUlang(); 
      }
    }

    // CEK APAKAH SUDAH SAMPAI DI AKHIR
    if (this.sel === selesai) {
      this.depositFeromon(); // Sukses! Jatuhkan feromon
      this.aturUlang(); // Mulai lagi dari awal
    }
  }

  // LOGIKA FEROMON YANG BENAR: Jatuhkan setelah sukses
  depositFeromon() {
    let jumlah = DEPOSIT_FEROMON / this.jejak.length;
    for (let sel of this.jejak) {
      sel.feromon = min(sel.feromon + jumlah, 500);
    }
  }

  // Gambar semut (lingkaran merah kecil)
  tampilkan() {
    // <-- MODIFIKASI: Ambil posisi dari 'this.sel' (lebih aman)
    if (!this.sel) return; // Pengecekan keamanan jika semut crash
    let x = this.sel.i * UKURAN_SEL + UKURAN_SEL / 2;
    let y = this.sel.j * UKURAN_SEL + UKURAN_SEL / 2;
    fill(255, 0, 0, 220); // Merah terang
    noStroke();
    ellipse(x, y, UKURAN_SEL * 0.5);
  }
}

/* ====================================================================== */
/* === FUNGSI UTAMA P5.JS === */
/* ====================================================================== */

// Inisialisasi
function setup() {
  createCanvas(windowWidth, windowHeight);
  
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

  mulai = ambilSel(0, 0);
  selesai = ambilSel(KOLOM - 1, BARIS - 1);

  buatLabirinDanGraf();
  
  for (let sel of grid) {
      sel.jarakKeSelesai = dist(sel.i, sel.j, selesai.i, selesai.j);
  }
  
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
  fill(0, 150, 255); // Biru (Tujuan)
  noStroke();
  rect(selesai.i * UKURAN_SEL, selesai.j * UKURAN_SEL, UKURAN_SEL, UKURAN_SEL);
  fill(0, 255, 150); // Hijau (Mulai)
  rect(mulai.i * UKURAN_SEL, mulai.j * UKURAN_SEL, UKURAN_SEL, UKURAN_SEL);

  
  // 4. GAMBAR BLOKIRAN PENGGUNA (BARU)
  gambarBlokir(); // <-- BARU

  
  // 5. Update & Gambar Semut (sebelumnya 4)
  let siklusPerbarui = 5; 
  for (let i = 0; i < siklusPerbarui; i++) {
    for (let semut of paraSemut) {
      semut.perbarui();
    }
  }
  
  // Gambar semut (hanya sekali per frame)
  for (let semut of paraSemut) {
    semut.tampilkan();
  }
}

/* ====================================================================== */
/* === FUNGSI HELPER (Pembantu) === */
/* ====================================================================== */

// Menguapkan semua feromon sedikit demi sedikit
function perbaruiFeromon() {
  for (let sel of grid) {
    sel.feromon = max(FEROMON_MIN, sel.feromon * TINGKAT_PENGUAPAN);
  }
}

// Menggambar semua feromon
function gambarFeromon() {
  for (let sel of grid) {
    sel.tampilkanFeromon();
  }
}

// === FUNGSI BARU UNTUK MENGGAMBAR BLOK ===
function gambarBlokir() { // <-- BARU
  for (let sel of grid) {
    if (sel.terblokir) {
      let x = sel.i * UKURAN_SEL;
      let y = sel.j * UKURAN_SEL;
      fill(80, 80, 80, 200); // Warna abu-abu gelap untuk blok
      stroke(0);
      strokeWeight(1);
      rect(x, y, UKURAN_SEL, UKURAN_SEL);
    }
  }
}

// Dapatkan objek sel dari koordinat (i, j)
function ambilSel(i, j) {
  if (i < 0 || j < 0 || i > KOLOM - 1 || j > BARIS - 1) {
    return undefined;
  }
  return grid[i + j * KOLOM];
}

// GENERATOR LABIRIN (Iterative Recursive Backtracker)
function buatLabirinDanGraf() {
  let saatIni = mulai;
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
  
  a.tetangga.push(b);
  b.tetangga.push(a);
}

// === FUNGSI BARU UNTUK MENDETEKSI KLIK ===
function mousePressed() { // <-- BARU
  // Hitung sel mana yang diklik
  let i = floor(mouseX / UKURAN_SEL);
  let j = floor(mouseY / UKURAN_SEL);
  
  let selDiKlik = ambilSel(i, j);

  // Cek apakah kliknya valid (di dalam grid, bukan start, bukan end)
  if (selDiKlik && selDiKlik !== mulai && selDiKlik !== selesai) {
    // Toggle (bisa diblokir, bisa di-unblokir)
    selDiKlik.terblokir = !selDiKlik.terblokir; 
  }
}

// Jika jendela di-resize, buat ulang semua
function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
  setup(); 
}