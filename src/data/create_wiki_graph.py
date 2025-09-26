# Facilitate a depth first search through wikipedia web pages
# Uses a queue data structure
# Keep track of visited pages and directed edges via a SQLite database

import wiki_interface
import sqlite_interface

begin = input("URL of starting Wikipedia page: ")

