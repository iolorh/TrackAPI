import sqlite3

DATABASE = "database.db"

def get_db():
    c = sqlite3.connect(DATABASE, check_same_thread=False)

    try:
        yield c
    finally:
        c.close()