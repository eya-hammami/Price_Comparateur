# type: ignore

from flask import Blueprint, request, jsonify
from database.db_connection import get_db_connection
from flask_jwt_extended import create_access_token
from models.user_model import get_user_by_email

auth_bp = Blueprint('auth', __name__)

# 🚫 Signup disabled
"""
@auth_bp.route('/signup', methods=['POST'])
def signup():
    pass
"""

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

    # ✅ Plain text password check ONLY!
    if user and user['password'] == password:
        access_token = create_access_token(identity=user['email'])
        return jsonify({
            'token': access_token,
            'role': user['role']
        }), 200

    return jsonify({'message': 'Invalid credentials'}), 401
