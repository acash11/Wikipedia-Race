import networkx as nx
import matplotlib.pyplot as plt
import csv
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "src", "data"))

def open_csv(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
            return data.decode("cp1252").splitlines()
    except Exception as e:
        raise RuntimeError(f"Failed to open {path}: {e}")


def load_graph(dataset):
    folder = os.path.abspath(os.path.join(DATA_DIR, dataset))
    edges_path = os.path.join(folder, "WikiGraph_edges.csv")

    if not os.path.isfile(edges_path):
        raise FileNotFoundError(f"Couldn't find edges.csv in '{folder}'")

    G = nx.DiGraph()
    edge_reader = csv.DictReader(open_csv(edges_path))

    for row in edge_reader:
        G.add_edge(row["Source"], row["Target"])

    return G


def clean_graph(G):
    dangling = [n for n in G.nodes() if G.out_degree(n) == 0]
    if dangling:
        G.remove_nodes_from(dangling)
    return G


def main():
    dataset = input("Enter folder name containing WikiGraph CSVs: ").strip()
    folder = os.path.join(DATA_DIR, dataset)

    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        return
    print(f"\nLoading graph from folder: {folder}\n")

    G = load_graph(dataset)

    nodes = G.number_of_nodes()
    edges = G.number_of_edges()
    dens = nx.density(G)

    # degree centrality with the top node
    deg = nx.degree_centrality(G)
    top_deg_node = max(deg, key=deg.get)
    top_deg_value = deg[top_deg_node]

    G_pr = clean_graph(G.copy())
    # page rank with highest pr
    pr = nx.pagerank(G_pr, alpha=0.85, max_iter=200)
    top_pr_node = max(pr, key=pr.get)
    top_pr_value = pr[top_pr_node]

    avg_degree = G.number_of_edges() / G.number_of_nodes()

    UG = G.to_undirected()
    avg_clust = nx.average_clustering(UG)
    diameter = nx.diameter(UG)
  
    # modularity using greedy communities, idk look it up
    from networkx.algorithms.community import greedy_modularity_communities, modularity

    communities = greedy_modularity_communities(UG)
    mod_score = modularity(UG, communities)


    print(
        f"The {dataset} folder has a total of {nodes} nodes and {edges} edges. "
        f"This graph has a density of {dens:.6f}. " 
        f"The node with the highest degree centrality is {top_deg_node}, with a score of "
        f"{top_deg_value:.4f}. This indicates that {top_deg_node.replace('_',' ')} has direct connections "
        f"to many nodes in the graph. "
        f"The PageRank values show that {top_pr_node} is highest with a score of {top_pr_value:.6f}. "
        f"This means that {top_pr_node.replace('_',' ')} has many links from nodes that are well-connected. "
        f"The average degree of {avg_degree:.4f} indicates that, on average, each node connects to about "
        f"{avg_degree:.2f} other nodes. "
        f"The average clustering coefficient is {avg_clust:.4f}, meaning roughly "
        f"{avg_clust*100:.1f}% of a node's neighbors are also connected to each other. "
        f"The network diameter of {diameter} shows that the longest shortest path between any two nodes "
        f"in the main component spans only {diameter} steps. The modularity score is {mod_score:.4f} "
        f"and there are {len(communities)} communities." 
    )

if __name__ == "__main__":
    main()
