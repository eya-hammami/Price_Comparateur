# type: ignore

from flask import Blueprint, request, jsonify
from database.db_connection import get_db_connection
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models.user_model import create_user, get_user_by_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    full_name = data['full_name']
    email = data['email']
    password = data['password']

    hashed_pw = generate_password_hash(password).decode('utf-8')

    conn = get_db_connection()
    cursor = conn.cursor()
    create_user(cursor, full_name, email, hashed_pw)
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'User created successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    user = get_user_by_email(cursor, email)
    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=user['email'])
        return jsonify({'token': access_token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401
