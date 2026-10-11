import snapshotsTable
import changesTable

def add_api(c,name,url,id):
    cursor = c.execute("INSERT INTO apis (name, spec_url,user_id) VALUES (?,?,?)",(name,url,id))
    c.commit()
    return cursor.lastrowid

def get_url(c,id):
    return c.execute("SELECT spec_url FROM apis WHERE rowid = ?",(id,)).fetchone()[0]

def update_last_checked(c,id,conn):
    c.execute("UPDATE apis SET last_checked = CURRENT_TIMESTAMP WHERE rowid = ?",(id,))
    conn.commit()

def delete_api(c,id):
    c.execute("DELETE FROM apis WHERE rowid = ?",(id,))
    snapshotsTable.delete_snapshots_by_api_id(c,id)
    c.commit()

def get_name_by_id(c,id):
    return c.execute("SELECT name FROM apis WHERE rowid = ?",(id,)).fetchone()[0]

def get_apis_by_id(c,id):
    apis = c.execute("SELECT rowid, * FROM apis WHERE user_id = ?",(id,)).fetchall()
    return [{"id": api[0], "name": api[1], "url": api[2], "last_checked" : api[3]} for api in apis]

def get_id_by_name(c,name):
    return c.execute("SELECT rowid FROM apis WHERE name = ?",(name,)).fetchone()[0]

def get_user_id_by_api_id(c,id):
    return c.execute("SELECT user_id FROM apis WHERE rowid = ?",(id,)).fetchone()[0]

def get_due_apis(c):
   return c.execute("SELECT rowid FROM apis WHERE last_checked <= datetime('now', '-6 hours')").fetchall()

def get_api_name_by_change_id(c,change_id):
    api_id = changesTable.get_api_id_by_id(c,change_id)
    return get_name_by_id(c,api_id)