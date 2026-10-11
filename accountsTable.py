import bcrypt

def account_exists(c, email, password):
    row = c.execute("SELECT rowid,* FROM accounts WHERE email = ?",(email,)).fetchone()
    if row:
        id = row[0]
    else:
        id = None
    return row is not None and bcrypt.checkpw(password.encode('utf-8'), row[2]),id

def email_exists(c,email):
    row = c.execute("SELECT email FROM accounts WHERE email = ?",(email,)).fetchone()
    return row is not None

def create_account(c,email,password):
    cursor = c.execute("INSERT INTO accounts (email,password) VALUES (?,?)",(email,password))
    c.commit()
    return cursor.lastrowid

def get_email_by_id(c,id):
    if id:
        return c.execute("SELECT email FROM accounts WHERE rowid = ?",(id,)).fetchone()[0]
    return None