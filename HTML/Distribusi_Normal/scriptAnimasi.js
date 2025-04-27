let scaleFactor = 0.5;
let p = [];
let pStop = [];
let size = 600 * scaleFactor;
let dots = [];
let colDots = [];
let cols;
let gapW = 40 * scaleFactor;
let gapH = 30 * scaleFactor;
let dotsBox;
let setBox;
let setBoxs = [];
let ballsize = 15 * scaleFactor;
let ballCount = 0;
let ballMax = 200;
let startH = 50 * scaleFactor;
let running = true;
let speedMultiplier = 1;

function setup() {
  let canvas = createCanvas(size, size * 2);
  canvas.parent('canvas-container');

  cols = int(size / gapW);

  let _h = startH + gapH;
  for (let i = 0; i < cols; i++) {
    for (let j = 0; j < cols; j++) {
      let shift = (i % 2 === 0) ? 0 : gapW / 2;
      dots.push(new Dot(j * gapW + gapW / 2 + shift, _h + i * gapH, 10 * scaleFactor));
    }
  }
  dotsBox = new Box(0, _h - gapH * 2, size, (cols + 2) * gapH);

  _h = _h + (cols + 1) * gapH;

  for (let i = 0; i <= cols; i++) {
    colDots.push(new Dot(size / 2 + (i - cols / 2) * gapW, _h, 10 * scaleFactor));
    let _w = 5 * scaleFactor;
    setBoxs.push(new Box(gapW * i + _w, _h, gapW - 2 * _w, height - _h));
  }
  setBox = new Box(0, _h - gapH * 2, size, height - _h + gapH * 2);
}

function draw() {
  if (!running) return;

  background(0);

  if (frameCount % 15 == 0 && ballCount < ballMax) {
    let _p = new Particles(new Dot(size / 2, startH - gapH, ballsize));
    _p.v = createVector(random(-0.5, 0.5), 0);
    _p.c = color(random(255), random(255), random(255));
    p.push(_p);
    ballCount++;
  }

  stroke(0);
  strokeWeight(5);
  setBoxs.forEach((e) => e.walls());
  noStroke();
  dotsBox.render();
  setBoxs.forEach((e) => e.render());

  dots.forEach(dot => dot.render());
  colDots.forEach(dot => dot.render());

  for (let s = 0; s < speedMultiplier; s++) {
    updateAndRenderParticles();
  }

  fill(0,255,255);
  text("masih jalan: " + p.length, 5, 20);
  text("berhenti: " + pStop.length, 5, 30);
}

function updateAndRenderParticles() {
  for (let i = p.length - 1; i >= 0; i--) {
    let sliced = false;

    if (dotsBox.overlap(p[i].dot)) {
      dots.forEach(dt => calculateOverlap(p[i], dt));
    } else if (setBox.overlap(p[i].dot)) {
      for (let j = 0; j < colDots.length; j++) {
        if (calculateOverlap(p[i], colDots[j])) break;
      }
      for (let j = 0; j < setBoxs.length; j++) {
        if (setBoxs[j].overlap(p[i].dot)) {
          p[i].dot.pos.x = lerp(p[i].dot.pos.x, setBoxs[j].x + setBoxs[j].w / 2, 0.5);
          p[i].v.x = 0;
          p[i].floorH = height - ballsize * setBoxs[j].count;
          if (!p[i].move) {
            setBoxs[j].count++;
            sliced = true;
          }
          break;
        }
      }
    } else {
      p[i].v.y = abs(p[i].v.y);
    }

    p[i].wall();
    p[i].gravity(false);
    p[i].resistant();
    p[i].update();
    p[i].render();

    if (sliced) {
      pStop.push(p[i]);
      p.splice(i, 1);
    }
  }

  pStop.forEach(ps => ps.render());
}

function mousePressed() {
  let _p = new Particles(new Dot(mouseX, mouseY, ballsize));
  _p.v = createVector(random(-0.5, 0.5), 0);
  _p.c = 255;
  p.push(_p);
}

function calculateOverlap(p, dt) {
  let d = dt.overlap(p.dot);
  if (d > 0) {
    p.bounceOff(p.getNormal(dt));
    if (abs(p.v.x) < 0.5) p.v.x = random([-0.5, 0.5]);
    return true;
  }
  return false;
}

class Dot {
  constructor(x, y, size) {
    this.pos = createVector(x, y);
    this.r = size;
  }
  overlap(dt) {
    let d = this.pos.dist(dt.pos);
    return d < (this.r + dt.r) / 2 ? d : 0;
  }
  render() {
    fill(255);
    ellipse(this.pos.x, this.pos.y, this.r, this.r);
  }
}

class Box {
  constructor(x, y, w, h) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;
    this.count = 0;
  }
  overlap(dt) {
    return (dt.pos.x > this.x && dt.pos.x < this.x + this.w && dt.pos.y > this.y && dt.pos.y < this.y + this.h);
  }
  render() {
    fill(0);
    rect(this.x, this.y, this.w, this.h);
  }
  walls() {
    line(this.x, this.y, this.x, this.y + this.h);
    line(this.x + this.w, this.y, this.x + this.w, this.y + this.h);
  }
}

class Particles {
  constructor(dt) {
    this.dot = dt;
    this.maxV = 9;
    this.v = createVector(0, 0);
    this.a = createVector(0, 0);
    this.bounce = false;
    this.bouncy = 0.2;
    this.c = 0;
    this.floorH = height;
    this.move = true;
  }
  wall() {
    if (this.dot.pos.x - this.dot.r < 0 || this.dot.pos.x + this.dot.r > width) {
      this.v.x *= -0.9;
    }
  }
  gravity(bounce) {
    this.a.add(createVector(0, 0.5));
    if (bounce) this.bounce = bounce;
  }
  resistant() {
    let r = this.v.copy().mult(-0.001);
    this.a.add(r);
  }
  addForce(x, y, n) {
    let f = createVector(x, y);
    f.setMag(this.v.mag() * n);
    this.a.add(f);
  }
  floor() {
    let h = this.dot.pos.y + this.dot.r / 2;
    return (this.floorH - h < 0 && this.v.y > 0);
  }
  getNormal(dt) {
    return p5.Vector.sub(this.dot.pos, dt.pos);
  }
  bounceOff(n, r = 1) {
    let _r = n;
    _r *= 2 * n.dot(this.v, n);
    _r = p5.Vector.sub(this.v, n);
    this.v = _r.mult(-this.bouncy * r);
  }
  update() {
    if (!this.move) return;
    this.v.add(this.a);
    if (this.floor()) {
      this.dot.pos.y = this.floorH - this.dot.r / 2;
      if (this.bounce) this.v.y *= -this.bouncy;
      else {
        this.move = false;
        this.v.y = 0;
        this.a.y = 0;
      }
    }
    if (this.v.mag() > this.maxV) this.v.setMag(this.maxV);
    this.dot.pos.add(this.v);
    this.a = createVector(0, 0);
  }
  render() {
    noStroke();
    fill(this.c);
    ellipse(this.dot.pos.x, this.dot.pos.y, this.dot.r, this.dot.r);
  }
}

function resetBalls() {
  p = [];
  pStop = [];
  ballCount = 0;
  ballMax = 200;
  setBoxs.forEach(box => box.count = 0); // Reset semua kolom ke kosong!
}


function clearBallsAndStop() {
  p = [];
  pStop = [];
  ballCount = 0;
  ballMax = 0;
  setBoxs.forEach(box => box.count = 0); // Reset semua kolom ke kosong!
}


function addBall() {
  let _p = new Particles(new Dot(size / 2, startH - gapH, ballsize));
  _p.v = createVector(random(-0.5, 0.5), 0);
  _p.c = color(random(255), random(255), random(255));
  p.push(_p);
}

function pauseResume() {
  running = !running;
}

function setSpeed(multiplier) {
  speedMultiplier = multiplier;
}
