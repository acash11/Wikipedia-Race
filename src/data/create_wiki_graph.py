# Facilitate a breadth first search through wikipedia web pages
# Uses a queue data structure
# Keep track of visited pages and directed edges via a SQLite database

from wiki_interface import get_wiki_data
from sqlite_interface import GraphInterface

enter_page = input("URL of Wikipedia page to enter into queue (Enter nothing to continue working on current queue): ")

# Push this to queue
# While queue is not empty (or count to 100 or something)
# dequeue to get page url
# create a node for this page, get categories
# get child links, create an edge for each
# attempt to queue each child link

g = GraphInterface("test.db")
g.create_tables()

if enter_page != "": g.check_if_visited_then_enqueue(enter_page)

count = 0

# Current page will be a page url
while count < 500:
    current_page = g.dequeue_and_mark_visited()
    curr_page_data = get_wiki_data(current_page)
    curr_page_name = current_page.split('/')[-1]

    print(f"{count}. Currently working on: {curr_page_name}")

    g.add_node(current_page.split('/')[-1], curr_page_data['cats'])
    for link in curr_page_data['links']:
        g.add_edge(from_page_name=curr_page_name, to_page_name=link.split('/')[-1])
        g.check_if_visited_then_enqueue(link)

    count += 1


g.export_to_csv()