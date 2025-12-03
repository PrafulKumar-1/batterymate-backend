from app.routes.auth import auth_bp
from app.routes.trips import trips_bp
from app.routes.predictions import predictions_bp
from app.routes.eco_score import eco_score_bp
from app.routes.charging import charging_bp
from app.routes.air_quality import air_quality_bp
from app.routes.grid_carbon import grid_carbon_bp
from app.routes.route_service import routes_bp

__all__ = ['auth_bp', 'trips_bp', 'predictions_bp', 'eco_score_bp', 'charging_bp', 'air_quality_bp', 'grid_carbon_bp', 'routes_bp']
