import numpy as np

class ACO:
    def __init__(self, G, distances, alpha=1.0, beta=2.0, rho=0.5, Q=5.0):
        self.G = G
        self.distances = distances
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q
        self.pheromones = {tuple(sorted(edge)): 1.0 for edge in G.edges()}

    def _probability(self, current, unvisited):
        probs = []
        for node in unvisited:
            edge = tuple(sorted((current, node)))
            tau = self.pheromones[edge] ** self.alpha
            eta = (1.0 / self.distances[(current, node)]) ** self.beta
            probs.append(tau * eta)
        total = sum(probs)
        return [p / total for p in probs]

    def _choose_next(self, current, unvisited):
        probs = self._probability(current, unvisited)
        return np.random.choice(unvisited, p=probs)

    def run_iteration(self, n_ants):
        all_paths = []
        nodes = list(self.G.nodes)
        for _ in range(n_ants):
            current = np.random.choice(nodes)
            path = [current]
            unvisited = list(set(nodes) - {current})
            while unvisited:
                next_node = self._choose_next(current, unvisited)
                path.append(next_node)
                unvisited.remove(next_node)
                current = next_node
            all_paths.append(path)

        self._evaporate()
        self._deposit_pheromones(all_paths)
        return all_paths

    def _evaporate(self):
        for edge in self.pheromones:
            self.pheromones[edge] *= (1 - self.rho)

    def _deposit_pheromones(self, paths):
        for path in paths:
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                edge = tuple(sorted((u, v)))
                self.pheromones[edge] += self.Q / self.distances[(u, v)]

    def get_pheromones(self):
        return self.pheromones
