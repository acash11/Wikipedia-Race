"""
Will have four tables - the idea is that these tables will be persistent.
The scraping script will write to and read from these tables.
The scraping script can pick back up at any time by referencing the contents of these tables.

A queue table to keep track of the order of wikipedia queries:
    CREATE TABLE IF NOT EXISTS queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        priority_rank FLOAT NOT NULL
    )

A sorted list table to keep if pages have already been visited:
    CREATE TABLE IF NOT EXISTS visited (
        url TEXT PRIMARY KEY,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )

A table to store node data:
    CREATE TABLE IF NOT EXISTS nodes(
        page_title TEXT PRIMARY KEY
        page_cats  TEXT
    )

A table to keep track of directed connections:
    CREATE TABLE IF NOT EXISTS edge_list(
        edge_id         INT    PRIMARY KEY
        origin_page     TEXT   FOREIGN KEY nodes.page_title
        referenced_page TEXT
    )

If we want to create a csv for analysis in Gephi, then we should be able to export the edge_list table.

"""

import sqlite3 as sql
import os
import csv

class GraphInterface:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sql.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close_conn(self):
        self.conn.close()

    def create_tables(self):

        # Queue table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            priority_rank FLOAT NOT NULL
        )
        """)

        # Visited pages
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS visited (
            url TEXT PRIMARY KEY,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Node data
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            page_title TEXT PRIMARY KEY,
            page_cats  TEXT
        )
        """)

        # Directed connections
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS edge_list (
            edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_page TEXT,
            referenced_page TEXT,
            FOREIGN KEY (origin_page) REFERENCES nodes(page_title)
        )
        """)

        self.conn.commit()

    # URL will eventually be scraped, add to queue if it isn't already in visited list
    def check_if_visited_then_enqueue(self, url: str, priority_rank: float = 0) -> bool:

        # Check if url has been visited, return if it has been
        self.cursor.execute("SELECT 1 FROM visited WHERE url = ? LIMIT 1", (url,))
        exists = self.cursor.fetchone() is not None
        if exists: return False

        try:
            self.cursor.execute("""
                INSERT INTO queue (url,priority_rank) 
                VALUES (?,?)
            """, (url,priority_rank,))
            self.conn.commit()
            success = True
        except sql.IntegrityError:
            # URL already exists in the queue
            success = False

        return success

    # We are about to scrape, remove from queue and add to visited list
    def dequeue_and_mark_visited(self) -> str:

        # Fetch the most recent entry
        # Previous: ORDER BY added_at ASC

        # PRIORITY QUEUE W/ RANKING
        # self.cursor.execute("""
        #     SELECT id, url FROM queue
        #     ORDER BY priority_rank ASC, added_at DESC
        #     LIMIT 1
        # """)

        # BREADTH FIRST SEARCH
        self.cursor.execute("""
            SELECT id, url FROM queue
            ORDER BY id ASC, added_at DESC
            LIMIT 1
        """)

        row = self.cursor.fetchone()

        if row is None:
            return None  # Queue is empty

        entry_id, url = row

        print("dequeued id and url: ", entry_id, url)

        # Remove it from the table
        self.cursor.execute("DELETE FROM queue WHERE id = ?", (entry_id,))
        # Add it to the visited list
        self.cursor.execute("INSERT INTO visited (url) VALUES (?)", (url,))

        self.conn.commit()

        return url
    
    def add_node(self, page_name: str, cats: set) -> bool:

        try:
            self.cursor.execute(
                "INSERT INTO nodes (page_title, page_cats) VALUES (?, ?)",
                (page_name, str(cats))
            )
            self.conn.commit()
            success = True
        except sql.IntegrityError:
            # Node already exists
            success = False

        return success
    
    def add_edge(self, from_page_name: str, to_page_name: str) -> bool:

        try:
            self.cursor.execute(
                """
                INSERT INTO edge_list (origin_page, referenced_page)
                VALUES (?, ?)
                """,
                (from_page_name, to_page_name)
            )
            self.conn.commit()
            success = True
        except sql.IntegrityError:
            # Could happen if origin_page or referenced_page doesn't exist
            success = False

        return success
    
    def get_all_nodes(self) -> list[tuple]:

        self.cursor.execute("SELECT page_title, page_cats FROM nodes ORDER BY page_title")
        nodes = self.cursor.fetchall()
        return nodes
    
    def get_all_edges(self) -> list[tuple]:

        self.cursor.execute("SELECT origin_page, referenced_page FROM edge_list ORDER BY origin_page, referenced_page")
        edges = self.cursor.fetchall()
        return edges

    def get_node_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM nodes")
        (count,) = self.cursor.fetchone()
        return count

    def get_edge_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM edge_list")
        (count,) = self.cursor.fetchone()
        return count

    def get_queue_size(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM queue")
        (count,) = self.cursor.fetchone()
        return count

    def get_visited_size(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM visited")
        (count,) = self.cursor.fetchone()
        return count
    
    def export_to_csv(self):
        output = self.db_path.split('.')[0]

        with open(output + "_nodes.csv", 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["page_name","categories"])
            for row in self.get_all_nodes():
                writer.writerow(row)

        with open(output + "_edges.csv", 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source","Target"])
            for row in self.get_all_edges():
                writer.writerow(row)
    
def test_graph_interface():
    print("Testing graph interface class...")

    # Delete db file if it exists
    if os.path.exists("test.db"):
        os.remove("test.db")

    g = GraphInterface("test.db")
    g.create_tables()

    # CHECK QUEUE AND DEQUEUE
    assert(g.check_if_visited_then_enqueue("a"))
    assert(g.dequeue_and_mark_visited() == "a")

    # Check if dequeue returns none if empty
    assert(g.dequeue_and_mark_visited() == None)

    assert(g.check_if_visited_then_enqueue("1234567890"))
    assert(g.check_if_visited_then_enqueue("qwertyuiop"))
    assert(g.check_if_visited_then_enqueue("c"))
    # Should return false if item is already in queue
    assert(not g.check_if_visited_then_enqueue("c"))
    assert(g.check_if_visited_then_enqueue("zxcvbnmasdfghjkl"))

    assert(g.dequeue_and_mark_visited() == "1234567890")
    assert(g.dequeue_and_mark_visited() == "qwertyuiop")
    assert(g.dequeue_and_mark_visited() == "c")
    assert(g.dequeue_and_mark_visited() == "zxcvbnmasdfghjkl")

    # Should return false if item has already been visited
    assert(not g.check_if_visited_then_enqueue("a"))
    assert(not g.check_if_visited_then_enqueue("1234567890"))
    assert(not g.check_if_visited_then_enqueue("qwertyuiop"))
    assert(not g.check_if_visited_then_enqueue("c"))
    assert(not g.check_if_visited_then_enqueue("zxcvbnmasdfghjkl"))

    # CHECK ADD NODE AND ADD EDGE

    assert(g.add_node('a', []))
    assert(g.add_node('b', []))
    assert(g.get_all_nodes() == [('a', '[]'),('b', '[]')])

    assert(g.add_edge('a', 'b'))
    assert(g.get_all_edges() == [('a', 'b')])

    # Should not be able to add duplicate nodes
    assert(not g.add_node('a', []))

    #Test export to csv
    #g.export_to_csv()

    g.close_conn()

    # Delete db file if it exists
    if os.path.exists("test.db"):
        os.remove("test.db")

if __name__ == '__main__':

    test_graph_interface()
    print("Tests passed good job!")