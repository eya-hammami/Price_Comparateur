# type: ignore
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

# Define users with roles and passwords
users = [
    {"full_name": "Travel Agency", "email": "travel@agency.com", "password": "travel123", "role": "agency"},
    {"full_name": "Hotel Manager", "email": "hotel@agency.com", "password": "hotel123", "role": "hotel"},
    {"full_name": "Sales Manager", "email": "sales@agency.com", "password": "sales123", "role": "sales"}
]

print("\n-- Copy and run these SQL INSERT statements in phpMyAdmin --\n")

for user in users:
    hashed_pw = bcrypt.generate_password_hash(user["password"]).decode('utf-8')
    sql = f"INSERT INTO users (full_name, email, password, role) VALUES ('{user['full_name']}', '{user['email']}', '{hashed_pw}', '{user['role']}');"
    print(sql)

print("\n-- Done --")
