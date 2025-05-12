import pyodbc
from sqlalchemy import create_engine
from flask import current_app

def get_dw_connection():
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=AZIZLAPTOP;'
        'DATABASE=DW_Price_Comparator;'
        'UID=sa;'
        'PWD=aziz;'  # Replace with your real password
    )
    return conn
