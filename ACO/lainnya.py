import pygame
import random
import math
import time

# Inisialisasi PyGame
pygame.init()

# Ukuran Layar
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Ant Colony Optimization Simulation")

# Warna
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Node dan Edge
nodes = [(100, 100), (200, 200), (300, 100), (400, 300), (500, 150)]
edges = [
    (0, 1), (0, 2), (0, 3), (0, 4),
    (1, 2), (1, 3), (1, 4),
    (2, 3), (2, 4),
    (3, 4)
]

# Jumlah Semut dan Iterasi
num_ants = 10
num_iterations = 100
pheromone_map = {}  # Feromon antara node

# Fungsi untuk menghitung jarak antar node
def distance(node1, node2):
    return math.sqrt((node1[0] - node2[0]) ** 2 + (node1[1] - node2[1]) ** 2)

# Menginisialisasi feromon (setiap edge memiliki feromon awal)
for edge in edges:
    pheromone_map[edge] = 1

# Fungsi untuk menggambar graf
def draw_graph():
    # Membersihkan layar (tanpa menggambar ulang latar belakang)
    screen.fill(BLACK)

    # Gambar edges
    for edge in edges:
        start, end = edge
        pygame.draw.line(screen, WHITE, nodes[start], nodes[end], 2)

    # Gambar nodes
    for node in nodes:
        pygame.draw.circle(screen, WHITE, node, 10)

    # Gambar jalur yang memiliki feromon
    for edge, pheromone in pheromone_map.items():
        start, end = edge
        thickness = pheromone * 5  # Tebal garis berdasarkan feromon
        pygame.draw.line(screen, BLUE, nodes[start], nodes[end], max(1, int(thickness)))

# Fungsi untuk memperbarui posisi semut
def move_ant(ant_pos, path):
    for step in path:
        x, y = nodes[step]
        dx, dy = x - ant_pos[0], y - ant_pos[1]
        dist = math.sqrt(dx**2 + dy**2)
        speed = 2
        dx, dy = dx / dist * speed, dy / dist * speed
        ant_pos[0] += dx
        ant_pos[1] += dy
    return ant_pos

# Fungsi untuk mencari jalur semut berdasarkan probabilitas feromon
def select_path(ant_pos, visited):
    # Pilih jalur berdasarkan feromon dan jarak
    choices = []
    for i, node in enumerate(nodes):
        if i not in visited:
            pheromone = 1  # Asumsi feromon bernilai tetap
            dist = distance(ant_pos, node)+1
            probability = pheromone / dist  # Probabilitas memilih jalur
            choices.append((i, probability))
    
    total_prob = sum(prob for _, prob in choices)
    normalized_choices = [(i, prob / total_prob) for i, prob in choices]
    
    # Pilih jalur berdasarkan probabilitas
    r = random.random()
    cum_prob = 0
    for i, prob in normalized_choices:
        cum_prob += prob
        if r < cum_prob:
            return [i]
    return []

# Fungsi utama untuk menjalankan simulasi
def run_simulation():
    global pheromone_map
    ant_paths = []
    for _ in range(num_ants):
        ant_pos = list(random.choice(nodes))
        visited = []
        path = []
        for _ in range(num_iterations):
            next_node = select_path(ant_pos, visited)
            if not next_node:
                break
            visited.append(next_node[0])
            path.append(next_node[0])
            ant_pos = nodes[next_node[0]]  # Update posisi semut
        ant_paths.append(path)

        # Update feromon berdasarkan jalur yang dilalui semut
        for step in path:
            pheromone_map[tuple(sorted([visited[step], visited[step + 1]]))] += 0.1
    
    draw_graph()
    pygame.display.update()  # Update tampilan PyGame

# Simulasi pergerakan semut
def simulation_loop():
    clock = pygame.time.Clock()  # Inisialisasi clock untuk kontrol FPS
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        run_simulation()  # Jalankan simulasi setiap frame
        clock.tick(30)  # Atur kecepatan frame (FPS)

    pygame.quit()

# Main loop PyGame
simulation_loop()
