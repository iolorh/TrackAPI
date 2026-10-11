def create_snapshot(c,spec,api_id,conn):
    c.execute("INSERT INTO snapshots (api_id, spec_json) VALUES (?,?)",(api_id, spec))
    conn.commit()

def get_latest_spec(iolo,c,api_id):
    if iolo:
        return c.execute("SELECT rowid FROM snapshots WHERE api_id = ? ORDER BY rowid DESC LIMIT 1",(api_id,)).fetchone()[0]
    else:
        return c.execute("SELECT spec_json FROM snapshots WHERE api_id = ? ORDER BY rowid DESC LIMIT 1",(api_id,)).fetchone()[0]

def get_date_by_snapshot_id(c,id):
    return c.execute("SELECT created_at FROM snapshots WHERE rowid = ?",(id,)).fetchone()[0]

def delete_snapshots_by_api_id(c,id):
    c.execute("DELETE from snapshots WHERE api_id = ?",(id,))
    c.commit()