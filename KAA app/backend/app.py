# type: ignore

from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from routes.auth_routes import auth_bp
from routes.dw_routes import dw_bp   # ✅ Import your DW routes

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

app.config.from_pyfile('config.py')

# ✅ Register Blueprints BEFORE running the app
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(dw_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)