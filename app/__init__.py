# app/__init__.py - Updated with explicit template folder
"""Flask application factory"""
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import config

db = SQLAlchemy()


def create_app(config_name='default'):
    """Application factory"""
    # Get the base directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Create Flask app with explicit template folder
    app = Flask(__name__,
                template_folder=os.path.join(base_dir, '..', 'templates'),
                static_folder=os.path.join(base_dir, '..', 'static'))
    
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)  # Enable CORS for all routes
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def index():
        """Serve the main frontend interface"""
        return render_template('index.html')
    
    @app.route('/test')
    def test_page():
        """Test page"""
        return "<h1>Test Page</h1><p>Flask is working!</p>"
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    return app