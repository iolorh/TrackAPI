def add_feedback(c,email,message):
    c.execute("INSERT INTO feedback VALUES (?,?)",(email,message))
    c.commit()