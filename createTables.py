import sqlite3
con = sqlite3.connect("database.db")


con.execute("DROP TABLE IF EXISTS accounts")
con.execute("""CREATE TABLE accounts(
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
                )""")

con.execute("DROP TABLE IF EXISTS apis")
con.execute("""CREATE TABLE apis(
                name TEXT NOT NULL,
                spec_url TEXT NOT NULL,
                last_checked DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id)
                REFERENCES accounts (rowid)
                    ON DELETE CASCADE
                )""")

con.execute("DROP TABLE IF EXISTS snapshots")
con.execute("""CREATE TABLE snapshots(
                api_id INTEGER NOT NULL,
                spec_json TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (api_id) 
                REFERENCES apis (rowid)
                    ON DELETE CASCADE
                )""")
con.execute("DROP TABLE IF EXISTS changes")
con.execute("""CREATE TABLE changes(
                api_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                description TEXT NOT NULL,
                breaking INTEGER,
                oldspec TEXT NOT NULL,
                newspec TEXT NOT NULL,
                path TEXT NOT NULL,
                oldsnapshotid INTEGER NOT NULL,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (api_id) 
                REFERENCES apis (rowid)
                    ON DELETE CASCADE
                )""")

con.execute("DROP TABLE IF EXISTS feedback")
con.execute("""CREATE TABLE feedback(
                email TEXT NOT NULL,
                message TEXT NOT NULL
                )""")

con.execute("CREATE TRIGGER update_last_checked AFTER INSERT ON snapshots BEGIN UPDATE apis SET last_checked = NEW.created_at WHERE rowid = NEW.api_id; END;")


con.commit()

con.close()