import sqlite3

con = sqlite3.connect("database.db")

con.execute("DELETE FROM apis")
con.commit()

con.close()