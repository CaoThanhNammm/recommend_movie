from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.models.db import db
import os
import logging
from dotenv import load_dotenv

# Import middleware
from app.middleware import CORSMiddleware

# Import all models to ensure they're registered with SQLAlchemy
from app.models.movie import Movie
from app.models.user import User
from app.models.user_rating import UserRating
from app.models.user_watch_history import UserWatchHistory
from app.models.user_preference import UserPreference
from app.models.genre import Genre
from app.models.cast import Cast
from app.models.crew import Crew
# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable print statements to work properly
import sys
sys.stdout.reconfigure(line_buffering=True)

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)
    # Configure the app from environment variables
    configure_app(app)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # No need for custom CORS handlers here as we're using the middleware
    
    logger.info("Application created and configured successfully")
    return app

def configure_app(app):
    """
    Configure the Flask application from environment variables.
    
    Args:
        app (Flask): The Flask application to configure
    """
    # Basic Flask configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', os.getenv('SECRET_KEY', 'dev-jwt-secret'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # API configuration
    app.config['API_RATE_LIMIT'] = int(os.getenv('API_RATE_LIMIT', 100))
    app.config['API_TIMEOUT'] = int(os.getenv('API_TIMEOUT', 30))
    
    # Configure database
    configure_database(app)

def configure_database(app):
    """
    Configure the database connection for the Flask application.
    
    Args:
        app (Flask): The Flask application to configure
    """
    # Set up database URI from MySQL parameters or use SQLite as fallback
    if all([os.getenv('MYSQL_USER'), os.getenv('MYSQL_HOST'), os.getenv('MYSQL_DB')]):
        mysql_user = os.getenv('MYSQL_USER')
        mysql_password = os.getenv('MYSQL_PASSWORD', '')
        mysql_host = os.getenv('MYSQL_HOST')
        mysql_port = os.getenv('MYSQL_PORT', '3306')
        mysql_db = os.getenv('MYSQL_DB')
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
        logger.info(f"Using MySQL database: {mysql_host}:{mysql_port}/{mysql_db}")
    else:
        # Fallback to SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_recommendation.db'
        logger.info("Using SQLite database")

def initialize_extensions(app):
    """
    Initialize Flask extensions.
    
    Args:
        app (Flask): The Flask application
    """
    # Initialize Flask-CORS
    CORS(app, resources={r"/api/*": {"origins": ["http://127.0.0.1:5500", "http://localhost:5500"], "supports_credentials": True}})
    
    # Initialize custom CORS middleware as a backup
    CORSMiddleware(app)
    
    # Initialize JWT
    JWTManager(app)
    
    # Initialize SQLAlchemy
    db.init_app(app)

def register_blueprints(app):
    """
    Register blueprints with the Flask application.
    
    Args:
        app (Flask): The Flask application
    """
    # Import blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.movie_controller import movie_bp
    from app.controllers.genre_controller import genre_bp
    from app.controllers.cast_controller import cast_bp
    from app.controllers.crew_controller import crew_bp
    from app.controllers.recommendation_controller import recommendation_bp
    from app.controllers.user_preference_controller import user_preference_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(movie_bp, url_prefix='/api/movies')
    app.register_blueprint(genre_bp, url_prefix='/api/genres')
    app.register_blueprint(cast_bp, url_prefix='/api/cast')
    app.register_blueprint(crew_bp, url_prefix='/api/crew')
    app.register_blueprint(recommendation_bp, url_prefix='/api/recommendations')
    app.register_blueprint(user_preference_bp, url_prefix='/api/preferences')
    
    logger.info("All blueprints registered successfully")