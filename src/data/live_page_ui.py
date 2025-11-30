"""
Graphical UI (Tkinter) for the WikiRace crawl.
Shows current page, queue/visited counts, and a nested relationships tree.
"""

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from queue import Queue, Empty

from create_wiki_graph import crawl
import create_wiki_graph


class LivePageUI:
    # Tkinter UI renders parent->children tree
    def __init__(self):
        self.events = Queue()
        self.running = False
        self.seen_edges = set()
        self.parent_children: dict[str, set[str]] = {}

        self.root = tk.Tk()
        self.root.title("WikiRace")
        self.root.geometry("640x520")

        self._build_inputs()
        self._build_status()
        self._build_relationships()

        self._poll_events()

    def _build_inputs(self):
        frame = ttk.LabelFrame(self.root, text="Run settings")
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Seed URL:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.seed_var = tk.StringVar(value="https://en.wikipedia.org/wiki/Video_game")
        ttk.Entry(frame, textvariable=self.seed_var, width=70).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Nodes to visit:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.nodes_var = tk.StringVar(value="25")
        ttk.Entry(frame, textvariable=self.nodes_var, width=15).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        self.start_btn = ttk.Button(frame, text="Start crawl", command=self.start_crawl)
        self.start_btn.grid(row=2, column=1, columnspan=2, pady=8,)

        self.cancel_btn = ttk.Button(frame, text="End crawl", command=self.cancel_crawl, state="disabled")
        self.cancel_btn.grid(row=3, column=1, columnspan=2, pady=8)

    def _build_status(self):
        frame = ttk.LabelFrame(self.root, text="Status")
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Current page:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.current_label = ttk.Label(frame, text="-", width=50)
        self.current_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(frame, text="Visited:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.visited_label = ttk.Label(frame, text="0")
        self.visited_label.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(frame, text="In queue:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.queue_label = ttk.Label(frame, text="0")
        self.queue_label.grid(row=2, column=1, sticky="w", padx=5, pady=5)


    def _build_relationships(self):
        frame = ttk.LabelFrame(self.root, text="Pages")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.relation_tree = ttk.Treeview(frame, show="tree", height=16)
        self.relation_tree.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Expand all", command=lambda: self._expand_collapse_all(expand=True)).pack(
            side="left", padx=4
        )
        ttk.Button(btn_frame, text="Collapse all", command=lambda: self._expand_collapse_all(expand=False)).pack(
            side="left", padx=4
        )

    def start_crawl(self):
        if self.running:
            return
        seed_url = self.seed_var.get().strip()
        try:
            nodes = int(self.nodes_var.get().strip())
            if nodes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Nodes to visit must be a positive integer.")
            return
        if not seed_url:
            messagebox.showerror("Invalid input", "Seed URL cannot be empty.")
            return

        self.running = True
        self.start_btn.config(state="disabled")

        # Reset cancel flag and enable button
        create_wiki_graph.global_cancel_check = False
        self.cancel_btn.config(state="normal")

        self._reset_view()

        thread = threading.Thread(
            target=self._run_crawl,
            args=(seed_url, nodes),
            daemon=True,
        )
        thread.start()

    def cancel_crawl(self):
        create_wiki_graph.global_cancel_check = True
        self.cancel_btn.config(state="disabled")   # Prevent double presses

    def _reset_view(self):
        self.current_label.config(text="-")
        self.visited_label.config(text="0")
        self.queue_label.config(text="0")
        self.seen_edges.clear()
        self.parent_children.clear()
        for item in self.relation_tree.get_children():
            self.relation_tree.delete(item)

    def _run_crawl(self, seed_url: str, nodes: int):
        # Run crawl in worker thread push progress and events into queue for the UI loop
        def on_progress(event: dict):
            self.events.put(event)

        try:
            result = crawl(seed_url, nodes, progress_callback=on_progress)
            self.events.put({"done": True, "result": result})
        except Exception as exc:  # noqa: BLE001
            self.events.put({"error": str(exc)})

    def _poll_events(self):
        # drain event queue and update UI without blocking main loop
        try:
            while True:
                event = self.events.get_nowait()
                self._handle_event(event)
        except Empty:
            pass
        self.root.after(200, self._poll_events)

    def _handle_event(self, event: dict):
        if "error" in event:
            messagebox.showerror("Crawl error", event["error"])
            self.running = False
            self.start_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
            return

        if event.get("done"):
            self.running = False
            self.start_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
            result = event.get("result", {})
            messagebox.showinfo(
                "Crawl finished",
                f"Processed {result.get('nodes_processed', 0)} nodes into {result.get('search_topic_name', '')}.",
            )
            return

        current_page = event.get("current_page") or "-"
        self.current_label.config(text=current_page)
        self.visited_label.config(text=str(event.get("visited_size", 0)))
        self.queue_label.config(text=str(event.get("queue_size", 0)))

        # update relationships list (parent -> child)
        for child in event.get("children", []):
            edge = (current_page, child)
            if edge in self.seen_edges:
                continue
            self.seen_edges.add(edge)
            self._insert_edge(parent=current_page, child=child)

    def _insert_edge(self, parent: str, child: str):
        # insert child under single parent
        # only supports one level of accordion dropdown
        if parent not in self.parent_children:
            parent_id = self.relation_tree.insert("", tk.END, text=parent, open=False)
            self.parent_children[parent] = set()
        else:
            parent_id = self._get_parent_id(parent)

        if child not in self.parent_children[parent]:
            self.parent_children[parent].add(child)
            self.relation_tree.insert(parent_id, tk.END, text=child)

    def _expand_collapse_all(self, expand: bool):
        for item in self.relation_tree.get_children():
            self.relation_tree.item(item, open=expand)

    def _get_parent_id(self, parent: str):
        # return  tree item id for the given parent
        for item in self.relation_tree.get_children():
            if self.relation_tree.item(item, "text") == parent:
                return item
        return self.relation_tree.insert("", tk.END, text=parent, open=False)

    def run(self):
        self.root.mainloop()


def main():
    ui = LivePageUI()
    ui.run()


if __name__ == "__main__":
    main()
