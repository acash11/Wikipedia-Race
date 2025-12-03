import csv
import heapq

def read_edge_list(csv_file, weighted=False):

    graph = {}

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = row["Source"]
            v = row["Target"]
            w = float(row["Weight"]) if weighted and "Weight" in row else 1.0

            graph.setdefault(u, []).append((v, w))
            # graph.setdefault(v, []).append((u, w))  # remove this if graph is directed

    return graph


def shortest_path(graph, start, goal, heuristic=None):

    pq = [(0, start)]  # (priority, node)
    dist = {start: 0}
    parent = {start: None}

    while pq:
        current_dist, node = heapq.heappop(pq)

        if node == goal:
            break

        if current_dist > dist.get(node, float("inf")):
            continue

        for neighbor, weight in graph.get(node, []):
            g_cost = current_dist + weight
            f_cost = g_cost + (heuristic(neighbor) if heuristic else 0)

            if g_cost < dist.get(neighbor, float("inf")):
                dist[neighbor] = g_cost
                parent[neighbor] = node
                heapq.heappush(pq, (f_cost, neighbor))

    # reconstruct path
    if goal not in parent:
        return float("inf"), []

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()

    return dist[goal], path

def find_shortest_path(path, target1, target2):
    graph = read_edge_list(path)
    distance, path = shortest_path(graph, target1, target2)

    return path

if __name__ == '__main__':
    print(find_shortest_path("Minecraft_to_Five_Nights_at_Freddy%27s\WikiGraph_edges.csv", "Minecraft", "Five_Nights_at_Freddy%27s"))