"""Routes package"""
from flask import Blueprint

# Create main API blueprint
api_bp = Blueprint('api', __name__)

# Import all route modules
from app.routes import players, matches, stats

# Register blueprints
from app.routes.players import players_bp
from app.routes.matches import matches_bp
from app.routes.stats import stats_bp

api_bp.register_blueprint(players_bp, url_prefix='/players')
api_bp.register_blueprint(matches_bp, url_prefix='/matches')
api_bp.register_blueprint(stats_bp, url_prefix='/stats')