import apisTable
import snapshotsTable

def add_change(c,api_id,type,description,breaking, old_spec, new_spec,path,old_snapshot_id,conn):
    c.execute("INSERT INTO changes (api_id,type,description,breaking, oldspec, newspec, path, oldsnapshotid) VALUES (?,?,?,?,?,?,?,?)",(api_id,type,description,breaking,old_spec,new_spec,path,old_snapshot_id))
    conn.commit()

    
def get_changes_by_id(c,id):
    apis = apisTable.get_apis_by_id(c,id)
    api_ids = [api["id"] for api in apis]
    if api_ids:
        placeholders = ",".join("?" for _ in api_ids)
        changes = c.execute(f"SELECT rowid,* FROM changes WHERE api_id IN ({placeholders}) ORDER BY rowid DESC", api_ids).fetchall()
    else:
        changes = []
    return [{"id": change[0], "api_id": change[1], "type": change[2], "description":change[3], "breaking": change[4], "oldspec": change[5], "newspec": change[6],"path": change[7],"old_snapshot_id":change[8], "detected_at": change[9]} for change in changes]


def get_changes_by_api_id(c,id):
    changes = c.execute(f"SELECT rowid,* FROM changes WHERE api_id = ? ORDER BY rowid DESC",(id,)).fetchall()
    return [{"id": change[0], "api_id": change[1], "type": change[2], "description":change[3], "breaking": change[4], "oldspec": change[5], "newspec": change[6],"path": change[7], "old_snapshot_id":change[8], "detected_at": change[9]} for change in changes]

def get_changes_by_api_name(c,name):
    api_id = apisTable.get_id_by_name(c,name)
    return get_changes_by_api_id(c,api_id)

def get_specs_by_change_id(c,id):
    return c.execute("SELECT oldspec,newspec FROM changes WHERE rowid = ?",(id,)).fetchone()

def get_path_by_change_id(c,id):
    return c.execute("SELECT path FROM changes WHERE rowid = ?",(id,)).fetchone()[0]

def get_detected_at_by_change_id(c,id):
    return c.execute("SELECT detected_at FROM changes WHERE rowid = ?",(id,)).fetchone()[0]

def get_old_spec_date_by_change_id(c,id):
    old_snapshot_id = c.execute("SELECT oldsnapshotid FROM changes WHERE rowid = ?",(id,)).fetchone()[0]
    return snapshotsTable.get_date_by_snapshot_id(c,old_snapshot_id)

def get_api_id_by_id(c,id):
    return c.execute("SELECT api_id FROM changes WHERE rowid = ?",(id,)).fetchone()[0]