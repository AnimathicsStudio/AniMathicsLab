const nodeCount = 10;
const tableBody = document.querySelector("#link-table tbody");

// Buat isi tabel: semua pasangan v1-v10
for (let i = 1; i <= nodeCount; i++) {
  for (let j = i + 1; j <= nodeCount; j++) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>v${i}</td>
      <td>v${j}</td>
      <td><input type="checkbox" onchange="updateGraph()"></td>
    `;
    tableBody.appendChild(row);
  }
}

// Buat simpul dan graf kosong
const nodes = new vis.DataSet(
  Array.from({ length: nodeCount }, (_, i) => ({
    id: `v${i + 1}`,
    label: `v${i + 1}`
  }))
);

const edges = new vis.DataSet([]);

const network = new vis.Network(document.getElementById("graph"), { nodes, edges }, {
  nodes: {
    shape: "circle",
    color: {
      background: "#4dabf7",
      border: "#1c7ed6"
    },
    font: {
      color: "#fff"
    }
  },
  edges: {
    color: { color: "#aaa" },
    smooth: true
  },
  physics: true
});

// Fungsi utama untuk perbarui graf dari checkbox
function updateGraph() {
  edges.clear();
  document.querySelectorAll("#link-table tbody tr").forEach(row => {
    const a = row.cells[0].innerText;
    const b = row.cells[1].innerText;
    const checked = row.cells[2].querySelector("input").checked;
    if (checked) {
      edges.add({ from: a, to: b });
    }
  });
}

// Acak koneksi dengan probabilitas default 30%
function randomizeGraph(prob = 0.3) {
  document.querySelectorAll("#link-table tbody input[type='checkbox']").forEach(cb => {
    cb.checked = Math.random() < prob;
  });
  updateGraph();
}

// Centang semua koneksi
function checkAll() {
  document.querySelectorAll("#link-table tbody input[type='checkbox']").forEach(cb => {
    cb.checked = true;
  });
  updateGraph();
}

// Hapus semua centang
function clearAll() {
  document.querySelectorAll("#link-table tbody input[type='checkbox']").forEach(cb => {
    cb.checked = false;
  });
  updateGraph();
}

function randomizeGraphFromInput() {
  const prob = parseFloat(document.getElementById("prob-input").value) || 0;
  randomizeGraph(prob);
}
