from flask import Blueprint, request, jsonify
import pandas as pd
import joblib
import os
from database.dw_connection import get_dw_connection

sarima_bp = Blueprint('sarima', __name__)

# ✅ Load pre-trained SARIMA model once at startup
model_path = os.path.join('models', 'sarima_model.pkl')
sarima_model = joblib.load(model_path)

@sarima_bp.route('/predict-product-price', methods=['POST'])
def predict_product_price():
    data = request.json
    product = data.get('product')
    supermarket = data.get('supermarket')
    date = data.get('date')

    if not product or not supermarket or not date:
        return jsonify({'error': 'Missing product, supermarket, or date'}), 400

    try:
        conn = get_dw_connection()

        query = f"""
        SELECT d.Full_Date, f.Prix_Unitaire
        FROM Fact_Supermarket f
        JOIN Dim_Date d ON f.Date_ID = d.Date_ID
        JOIN Dim_Product p ON f.Product_ID = p.Product_ID
        JOIN Dim_Supermarché s ON f.Supermarché_ID = s.Supermarché_ID
        WHERE p.Produit = '{product}' AND s.Supermarché = '{supermarket}'
        """

        df = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500

    if df.empty:
        return jsonify({'error': 'No price data found for the selected product and supermarket'}), 404

    try:
        df['Full_Date'] = pd.to_datetime(df['Full_Date'])
        ts = df.groupby('Full_Date')['Prix_Unitaire'].mean()
        ts = ts.asfreq('D').ffill()  # ✅ Replace deprecated fillna

        forecast_date = pd.to_datetime(date).tz_localize(None)
        last_date = ts.index[-1].tz_localize(None)

        steps_ahead = (forecast_date - last_date).days

        if steps_ahead <= 0:
            return jsonify({'error': 'Date must be after the last available data point'}), 400

        forecast = sarima_model.forecast(steps=steps_ahead)
        predicted_price = forecast[-1]

        return jsonify({'predicted_price': round(float(predicted_price), 2)})

    except Exception as e:
        return jsonify({'error': f'Model forecast failed: {str(e)}'}), 500


# ✅ Product list endpoint (unchanged)
@sarima_bp.route('/product-list', methods=['GET'])
def get_product_list():
    conn = get_dw_connection()

    query = """
        SELECT DISTINCT Produit
        FROM Dim_Product
        WHERE Produit IS NOT NULL
        ORDER BY Produit
    """

    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return jsonify(df['Produit'].tolist())
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500
