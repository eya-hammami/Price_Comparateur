# type: ignore
import pyodbc

def get_dw_connection():
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=AZIZLAPTOP;'
        'DATABASE=DW_Price_Comparator;'
        'UID=sa;'
        'PWD=aziz;'  # Replace with your real password
    )
    return conn
