def create_user(cursor, full_name, email, password, role):
    sql = "INSERT INTO users (full_name, email, password, role) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (full_name, email, password, role))

def get_user_by_email(cursor, email):
    sql = "SELECT * FROM users WHERE email = %s"
    cursor.execute(sql, (email,))
    return cursor.fetchone() 