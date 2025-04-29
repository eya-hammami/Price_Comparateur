def create_user(cursor, full_name, email, hashed_password):
    sql = "INSERT INTO users (full_name, email, password) VALUES (%s, %s, %s)"
    cursor.execute(sql, (full_name, email, hashed_password))

def get_user_by_email(cursor, email):
    sql = "SELECT * FROM users WHERE email = %s"
    cursor.execute(sql, (email,))
    return cursor.fetchone() 