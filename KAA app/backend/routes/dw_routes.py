# routes/dw_routes.py

from flask import Blueprint, jsonify
import pyodbc

dw_bp = Blueprint('dw', __name__)

def get_dw_connection():
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=AZIZLAPTOP;'
        'DATABASE=DW_Price_Comparator;'
        'UID=sa;'
        'PWD=aziz;'  # Replace with a secure password or use environment variables in production
    )
    return conn

@dw_bp.route('/dw/flights-summary', methods=['GET'])
def get_flights_summary():
    conn = get_dw_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 10 * FROM Fact_Flight")  # Sample query
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(results)
