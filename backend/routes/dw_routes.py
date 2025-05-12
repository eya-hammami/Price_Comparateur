from flask import Blueprint, jsonify, request
from database.dw_connection import get_dw_connection

dw_bp = Blueprint('dw', __name__)

# ✅ Flights - Dynamic Search by Origin, Destination, Date
@dw_bp.route('/dw/search-flights', methods=['GET'])
def search_flights():
    origin = request.args.get('origin', '')
    destination = request.args.get('destination', '')
    date = request.args.get('date', '')

    conn = get_dw_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            d.Full_Date AS Date,
            lo_origin.City AS Origin,
            lo_dest.City AS Destination,
            a.Airline AS Airline,
            f.Departure_Time AS Departure,
            f.Arrival_Time AS Arrival,
            f.Stopover,
            f.Price,
            f.Flight_Duration AS Duration
        FROM Fact_Flight f
        JOIN Dim_Date d ON f.Date_ID = d.Date_ID
        JOIN Dim_Location lo_origin ON f.Origin_ID = lo_origin.Location_ID
        JOIN Dim_Location lo_dest ON f.Destination_ID = lo_dest.Location_ID
        JOIN Dim_Airline a ON f.Airline_ID = a.Airline_ID
        WHERE f.Price IS NOT NULL
    """

    params = []

    if origin:
        query += " AND lo_origin.City = ?"
        params.append(origin)

    if destination:
        query += " AND lo_dest.City = ?"
        params.append(destination)

    if date:
        query += " AND d.Full_Date = ?"
        params.append(date)

    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    return jsonify(results)

# ✅ Flights - Filters for Stopover and Airlines dynamically
@dw_bp.route('/dw/flight-filters', methods=['GET'])
def get_dynamic_flight_filters():
    origin = request.args.get('origin', '')
    destination = request.args.get('destination', '')
    date = request.args.get('date', '')

    conn = get_dw_connection()
    cursor = conn.cursor()

    base_query = """
        FROM Fact_Flight f
        JOIN Dim_Date d ON f.Date_ID = d.Date_ID
        JOIN Dim_Location lo_origin ON f.Origin_ID = lo_origin.Location_ID
        JOIN Dim_Location lo_dest ON f.Destination_ID = lo_dest.Location_ID
        JOIN Dim_Airline a ON f.Airline_ID = a.Airline_ID
        WHERE f.Price IS NOT NULL
    """

    filters = []
    params = []

    if origin:
        filters.append("lo_origin.City = ?")
        params.append(origin)
    if destination:
        filters.append("lo_dest.City = ?")
        params.append(destination)
    if date:
        filters.append("d.Full_Date = ?")
        params.append(date)

    where_clause = " AND " + " AND ".join(filters) if filters else ""

    # 🟢 Dates
    date_query = f"SELECT DISTINCT d.Full_Date {base_query} {where_clause} ORDER BY d.Full_Date"
    cursor.execute(date_query, params)
    dates = [row[0] for row in cursor.fetchall()]

    # 🟢 Origins
    origin_query = f"SELECT DISTINCT lo_origin.City {base_query} {where_clause} ORDER BY lo_origin.City"
    cursor.execute(origin_query, params)
    origins = [row[0] for row in cursor.fetchall()]

    # 🟢 Destinations
    destination_query = f"SELECT DISTINCT lo_dest.City {base_query} {where_clause} ORDER BY lo_dest.City"
    cursor.execute(destination_query, params)
    destinations = [row[0] for row in cursor.fetchall()]

    # 🟢 Stopovers
    stopover_query = f"SELECT DISTINCT f.Stopover {base_query} {where_clause} ORDER BY f.Stopover"
    cursor.execute(stopover_query, params)
    stopovers = [row[0] for row in cursor.fetchall()]

    # 🟢 Airlines
    airline_query = f"SELECT DISTINCT a.Airline {base_query} {where_clause} ORDER BY a.Airline"
    cursor.execute(airline_query, params)
    airlines = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify({
        'dates': dates,
        'origins': origins,
        'destinations': destinations,
        'stopovers': stopovers,
        'airlines': airlines
    })


# ✅ Hotels - Dropdown Filters only for values existing in Fact_Hotel
@dw_bp.route('/dw/hotel-filters', methods=['GET'])
def get_hotel_filters():
    conn = get_dw_connection()
    cursor = conn.cursor()

    # Dates used in Fact_Hotel
    cursor.execute("""
        SELECT DISTINCT d.Full_Date 
        FROM Fact_Hotel h 
        JOIN Dim_Date d ON h.Date_ID = d.Date_ID 
        WHERE d.Full_Date IS NOT NULL
        ORDER BY d.Full_Date
    """)
    dates = [row[0] for row in cursor.fetchall()]

    # Cities used in Fact_Hotel
    cursor.execute("""
        SELECT DISTINCT l.City 
        FROM Fact_Hotel h 
        JOIN Dim_Location l ON h.Location_ID = l.Location_ID 
        WHERE l.City IS NOT NULL 
        ORDER BY l.City
    """)
    locations = [row[0] for row in cursor.fetchall()]

    # Countries used in Fact_Hotel
    cursor.execute("""
        SELECT DISTINCT l.Country 
        FROM Fact_Hotel h 
        JOIN Dim_Location l ON h.Location_ID = l.Location_ID 
        WHERE l.Country IS NOT NULL 
        ORDER BY l.Country
    """)
    countries = [row[0] for row in cursor.fetchall()]

    # Hotels used in Fact_Hotel
    cursor.execute("""
        SELECT DISTINCT ho.hotel_name 
        FROM Fact_Hotel h 
        JOIN Dim_Hotel ho ON h.Hotel_ID = ho.Hotel_ID 
        WHERE ho.hotel_name IS NOT NULL 
        ORDER BY ho.hotel_name
    """)
    hotels = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify({
        'dates': dates,
        'locations': locations,
        'countries': countries,
        'hotels': hotels
    })
@dw_bp.route('/dw/search-hotels', methods=['GET'])
def search_hotels():
    city = request.args.get('city', '')
    date = request.args.get('date', '')
    hotel_name = request.args.get('hotel', '')
    stars = request.args.get('stars', '')
    search = request.args.get('search', '')

    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit

    conn = get_dw_connection()
    cursor = conn.cursor()

    base_query = """
        FROM Fact_Hotel f
        JOIN Dim_Date d ON f.Date_ID = d.Date_ID
        JOIN Dim_Hotel h ON f.Hotel_ID = h.Hotel_ID
        JOIN Dim_Location l ON f.Location_ID = l.Location_ID
        WHERE f.price IS NOT NULL
    """

    filters = []
    params = []

    if city:
        filters.append("l.City = ?")
        params.append(city)
    if date:
        filters.append("d.Full_Date = ?")
        params.append(date)
    if hotel_name:
        filters.append("h.hotel_name = ?")
        params.append(hotel_name)
    if stars:
        filters.append("h.number_of_stars = ?")
        params.append(int(stars))
    if search:
        filters.append("(h.hotel_name LIKE ? OR l.City LIKE ?)")
        search_term = f"%{search}%"
        params.extend([search_term, search_term])

    if filters:
        base_query += " AND " + " AND ".join(filters)

    count_query = "SELECT COUNT(*) " + base_query
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    data_query = f"""
        SELECT 
            d.Full_Date,
            h.hotel_name AS Hotel_Name,
            l.City,
            l.Country,
            h.review_label,
            h.review_count,
            h.number_of_stars,
            h.description,
            h.url,
            f.price,
            f.currency,
            f.checkin_date,
            f.checkout_date
        {base_query}
        ORDER BY f.checkin_date DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    cursor.execute(data_query, params + [offset, limit])
    columns = [col[0] for col in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify({
        "data": rows,
        "total": total_count
    })





# ✅ Products - Dropdown Filters only for values existing in Fact_Supermarket
@dw_bp.route('/dw/product-filters', methods=['GET'])
def get_product_filters():
    conn = get_dw_connection()
    cursor = conn.cursor()

    # Dates actually used
    cursor.execute("""
        SELECT DISTINCT d.Full_Date 
        FROM Fact_Supermarket f 
        JOIN Dim_Date d ON f.Date_ID = d.Date_ID 
        WHERE d.Full_Date IS NOT NULL
        ORDER BY d.Full_Date
    """)
    dates = [row[0] for row in cursor.fetchall()]

    # Locations actually used
    cursor.execute("""
        SELECT DISTINCT l.City 
        FROM Fact_Supermarket f 
        JOIN Dim_Location l ON f.Location_ID = l.Location_ID 
        WHERE l.City IS NOT NULL 
        ORDER BY l.City
    """)
    locations = [row[0] for row in cursor.fetchall()]

    # Stores actually used
    cursor.execute("""
        SELECT DISTINCT sm.Supermarché 
        FROM Fact_Supermarket f 
        JOIN Dim_Supermarché sm ON f.Supermarché_ID = sm.Supermarché_ID 
        WHERE sm.Supermarché IS NOT NULL 
        ORDER BY sm.Supermarché
    """)
    stores = [row[0] for row in cursor.fetchall()]

    # Products actually used
    cursor.execute("""
        SELECT DISTINCT p.Produit 
        FROM Fact_Supermarket f 
        JOIN Dim_Product p ON f.Product_ID = p.Product_ID 
        WHERE p.Produit IS NOT NULL 
        ORDER BY p.Produit
    """)
    products = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify({
        'dates': dates,
        'locations': locations,
        'stores': stores,
        'products': products
    })
# ✅ Products - Comparison Endpoint (Unit Price Focused)
@dw_bp.route('/dw/compare-products', methods=['GET'])
def compare_products():
    conn = get_dw_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            d.Full_Date AS Date,
            l.City AS Location,
            sm.Supermarché AS Store,
            p.Produit AS Product_Name,
            f.Quantite_Achetee AS Quantity,
            f.Prix_Unitaire AS Unit_Price
        FROM Fact_Supermarket f
        JOIN Dim_Date d ON f.Date_ID = d.Date_ID
        JOIN Dim_Location l ON f.Location_ID = l.Location_ID
        JOIN Dim_Supermarché sm ON f.Supermarché_ID = sm.Supermarché_ID
        JOIN Dim_Product p ON f.Product_ID = p.Product_ID
        WHERE f.Prix_Unitaire IS NOT NULL
    """

    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return jsonify(rows)

