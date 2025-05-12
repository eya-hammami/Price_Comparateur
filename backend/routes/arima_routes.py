from flask import Blueprint, request, jsonify
from database.dw_connection import get_dw_connection
import pandas as pd
import joblib

# ✅ Load pre-trained ARIMA model (if really needed — but it won’t work per route)
# arima_model = joblib.load('models/arima_model.pkl')  # Comment this for now

arima_bp = Blueprint('arima', __name__)

@arima_bp.route('/predict-flight-price', methods=['POST'])
def predict_flight_price():
    data = request.json
    date = data.get('date')
    source = data.get('source')
    destination = data.get('destination')

    if not date or source is None or destination is None:
        return jsonify({'error': 'Missing input data (date, source, destination)'}), 400

    conn = get_dw_connection()

    query = f"""
    SELECT d.Full_Date, f.Price
    FROM Fact_Flight f
    JOIN Dim_Date d ON f.Date_ID = d.Date_ID
    WHERE f.Destination_ID = {destination} AND f.Origin_ID = {source}
    """

    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500

    conn.close()

    if df.empty:
        return jsonify({'error': 'No data found for this route'}), 404

    df['Full_Date'] = pd.to_datetime(df['Full_Date'])
    df_daily = df.groupby('Full_Date')['Price'].mean().reset_index()

    if df_daily.empty or len(df_daily) < 10:
        return jsonify({'error': 'Not enough data points to train the ARIMA model.'}), 400

    df_daily.set_index('Full_Date', inplace=True)
    ts = df_daily['Price']

    # ✅ Simple ARIMA per-request — using the user’s filter data
    from statsmodels.tsa.arima.model import ARIMA

    model = ARIMA(ts, order=(5,1,0))
    model_fit = model.fit()

    forecast_date = pd.to_datetime(date)
    last_date = ts.index[-1]
    steps_ahead = (forecast_date - last_date).days

    if steps_ahead <= 0:
        return jsonify({'error': 'Date must be after the last available date in the dataset'}), 400

    forecast = model_fit.forecast(steps=steps_ahead)
    predicted_price = forecast.iloc[-1]

    return jsonify({'predicted_price': round(float(predicted_price), 2)})

# ✅ Correct origin cities endpoint
@arima_bp.route('/origin-cities', methods=['GET'])
def get_origin_cities():
    conn = get_dw_connection()

    query = """
        SELECT DISTINCT f.Origin_ID, l.City
        FROM Fact_Flight f
        JOIN Dim_Location l ON f.Origin_ID = l.Location_ID
    """

    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500

# ✅ Correct destination cities endpoint
@arima_bp.route('/destination-cities', methods=['GET'])
def get_destination_cities():
    conn = get_dw_connection()

    query = """
        SELECT DISTINCT f.Destination_ID, l.City
        FROM Fact_Flight f
        JOIN Dim_Location l ON f.Destination_ID = l.Location_ID
    """

    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500
