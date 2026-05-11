let nodes = [];
let edges = [];
let startNode, endNode;
let currentNode;
let visited = [];
let unvisited = [];

function initializeGraph() {
  // Membuat 50 node acak di canvas
  for (let i = 0; i < 50; i++) {
    nodes.push(new Node(random(width), random(height), String.fromCharCode(65 + i)));
  }

  // Membuat edges acak antara node
  for (let i = 0; i < 100; i++) {  // Membuat 100 edges acak
    let node1 = random(nodes);
    let node2 = random(nodes);
    if (node1 !== node2) {
      let weight = int(random(5, 20));
      edges.push(new Edge(node1, node2, weight));
    }
  }

  // Menetapkan node awal dan akhir
  startNode = nodes[0];
  endNode = nodes[nodes.length - 1];

  // Inisialisasi Dijkstra
  for (let node of nodes) {
    node.distance = Infinity;
    node.previous = null;
    unvisited.push(node);
  }
  startNode.distance = 0;
  currentNode = startNode;
}

function drawGraph() {
  // Gambar edges
  for (let edge of edges) {
    edge.show();
  }

  // Gambar nodes
  for (let node of nodes) {
    node.show();
  }

  // Menampilkan status Dijkstra
  fill(0);
  textSize(16);
  text('Start Node: ' + startNode.label, 10, height - 50);
  text('End Node: ' + endNode.label, 10, height - 30);
}

// Langkah-langkah Dijkstra
function dijkstraStep() {
  if (unvisited.length > 0) {
    // Menandai node yang sedang diproses
    currentNode.visited = true;
    visited.push(currentNode);
    unvisited = unvisited.filter(node => node !== currentNode);

    // Memperbarui jarak ke tetangga
    for (let edge of currentNode.edges) {
      let neighbor = edge.getOtherNode(currentNode);
      if (!neighbor.visited) {
        let tentativeDistance = currentNode.distance + edge.weight;
        if (tentativeDistance < neighbor.distance) {
          neighbor.distance = tentativeDistance;
          neighbor.previous = currentNode;
        }
      }
    }

    // Menemukan node dengan jarak terkecil dari node yang belum dikunjungi
    let minDistance = Infinity;
    for (let node of unvisited) {
      if (node.distance < minDistance) {
        minDistance = node.distance;
        currentNode = node;
      }
    }
  } else {
    showPath();
  }
}

// Menampilkan jalur terpendek setelah Dijkstra selesai
function showPath() {
  let path = [];
  let tempNode = endNode;
  while (tempNode !== null) {
    path.push(tempNode);
    tempNode = tempNode.previous;
  }

  // Menandai jalur terpendek
  stroke(255, 0, 0);
  strokeWeight(5);
  for (let i = path.length - 1; i > 0; i--) {
    line(path[i].x, path[i].y, path[i-1].x, path[i-1].y);
  }
}

// Kelas untuk Node
class Node {
  constructor(x, y, label) {
    this.x = x;
    this.y = y;
    this.label = label;
    this.edges = [];
    this.visited = false;
    this.distance = Infinity;
    this.previous = null;
  }

  show() {
    fill(this.visited ? 'green' : 'white');
    stroke(0);
    ellipse(this.x, this.y, 40, 40);
    fill(0);
    textAlign(CENTER, CENTER);
    textSize(16);
    text(this.label, this.x, this.y);

    // Menampilkan edges
    for (let edge of this.edges) {
      edge.show();
    }
  }

  addEdge(edge) {
    this.edges.push(edge);
  }
}

// Kelas untuk Edge
class Edge {
  constructor(node1, node2, weight) {
    this.node1 = node1;
    this.node2 = node2;
    this.weight = weight;

    // Menambahkan edges ke node
    this.node1.addEdge(this);
    this.node2.addEdge(this);
  }

  show() {
    stroke(0);
    line(this.node1.x, this.node1.y, this.node2.x, this.node2.y);

    // Menampilkan bobot (weight)
    let midX = (this.node1.x + this.node2.x) / 2;
    let midY = (this.node1.y + this.node2.y) / 2;
    fill(0);
    textSize(12);
    text(this.weight, midX, midY);
  }

  getOtherNode(node) {
    return node === this.node1 ? this.node2 : this.node1;
  }
}
