# Facilitate a breadth first search through wikipedia web pages
# Uses a queue data structure
# Keep track of visited pages and directed edges via a SQLite database

import os
import random
from typing import Callable, Optional

from wiki_interface import get_wiki_data
from sqlite_interface import GraphInterface

global_cancel_check = False


def get_and_remove_lowest_sim_score(data_list):
    """Temporary placeholder: pick and remove the lowest sim score entry."""
    if not data_list:
        return None

    lowest_score_dict = data_list[0]
    for item in data_list:
        if item["sim_score"] < lowest_score_dict["sim_score"]:
            lowest_score_dict = item

    data_list.remove(lowest_score_dict)
    return lowest_score_dict


def crawl(
    enter_page: str,
    nodes_to_search: int,
    progress_callback: Optional[Callable[[dict], None]] = None,
):

    #  Seed URL is queued
    #  Loop until node budget hit or queue empty
    #    - dequeue next page URL; mark visited in DB
    #    - fetch page, extract categories + outbound links
    #    - add a node record; add an edge for each outbound link
    #    - queue each child with priority score placeholder
    #  export nodes/edges to CSV and the DB
    """Run the crawl, optionally emitting per-page progress via callback."""
    search_topic_name = enter_page.split("/")[-1]
    os.makedirs(search_topic_name, exist_ok=True)

    g = GraphInterface(search_topic_name + "/WikiGraph.db")
    g.create_tables()

    if enter_page != "":
        g.check_if_visited_then_enqueue(enter_page)

    count = 0

    # TEMP FOR TESTING:
    # Will not work for resumed sessions, just to see if priority rankings are being pulled accurately
    similarity_dictionary = []

    # Current page will be a page url
    while count < nodes_to_search and global_cancel_check is False:
        current_page = g.dequeue_and_mark_visited()
        if not current_page:
            break

        curr_page_data = get_wiki_data(current_page)
        curr_page_name = current_page.split("/")[-1]

        g.add_node(curr_page_name, curr_page_data["cats"])
        edges_added = 0
        children_names = []
        for link in curr_page_data["links"]:
            child_name = link.split("/")[-1]
            g.add_edge(from_page_name=curr_page_name, to_page_name=child_name)
            children_names.append(child_name)

            # priority rank here
            random_score = random.random()
            similarity_dictionary.append({"url": link, "sim_score": random_score})

            g.check_if_visited_then_enqueue(link, random_score)
            edges_added += 1

        most_similar = get_and_remove_lowest_sim_score(similarity_dictionary)

        if progress_callback:
            progress_callback(
                {
                    "index": count,
                    "current_page": curr_page_name,
                    "categories": curr_page_data["cats"],
                    "children": children_names,
                    "edges_added": edges_added,
                    "queue_size": g.get_queue_size(),
                    "visited_size": g.get_visited_size(),
                    "node_count": g.get_node_count(),
                    "edge_count": g.get_edge_count(),
                    "most_similar": most_similar["url"].split("/")[-1]
                    if most_similar
                    else None,
                }
            )
        else:
            print(f"{count}. Currently working on: {curr_page_name}")
            print("Most similar: ", most_similar)

        count += 1

    g.export_to_csv()
    return {"search_topic_name": search_topic_name, "nodes_processed": count}


def main():
    enter_page = input(
        "URL of Wikipedia page to search (Previous page searches will pick up where they left off): "
    )
    nodes_to_search = int(
        input("How many nodes should be searched (1 node will take about 1-8 seconds): ")
    )
    result = crawl(enter_page, nodes_to_search)
    print(f"Finished. Processed {result['nodes_processed']} nodes into {result['search_topic_name']}.")


if __name__ == "__main__":
    main()
