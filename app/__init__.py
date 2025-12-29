from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv

# Import db from your master model file
from app.models.user import db 

jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # 1. Force Load Environment Variables
    # This looks for .env in the current directory (backend/)
    load_dotenv()
    
    # 2. Get Database URL
    db_url = os.getenv('DATABASE_URL')
    
    # Debug: Print to console to verify (Remove this line in production)
    print(f"🔌 Connecting to Database: {db_url}")

    if not db_url:
        # Fallback to SQLite if MySQL config is missing so app doesn't crash
        print("⚠️  WARNING: DATABASE_URL not found. Falling back to SQLite.")
        db_url = 'sqlite:///batterymate.db'

    # 3. Apply Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    
    # 4. Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    
    # Enable CORS
    CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://batterymate.netlify.app",
            "http://localhost:3000" ,
             "http://localhost:5000" # Keep for local development
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})


    # 5. Initialize ML Service
    from app.services.ml_service import ml_service
    with app.app_context():
        ml_service.initialize()

    # 6. Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.trips import trips_bp
    from app.routes.predictions import predictions_bp
    from app.routes.eco_score import eco_score_bp
    from app.routes.charging import charging_bp
    from app.routes.air_quality import air_quality_bp
    from app.routes.grid_carbon import grid_carbon_bp
    from app.routes.route_service import routes_bp
    from app.routes.chatbot import chatbot_bp
    
    
    app.register_blueprint(routes_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(eco_score_bp)
    app.register_blueprint(charging_bp)
    app.register_blueprint(air_quality_bp)
    app.register_blueprint(grid_carbon_bp)
    app.register_blueprint(chatbot_bp)
    
    # Register middleware
    from app.middleware.error_handler import register_error_handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created/verified.")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
    
    @app.route('/api/health', methods=['GET'])
    def health():
        from datetime import datetime
        return {'status': 'healthy', 'timestamp': datetime.utcnow()}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)