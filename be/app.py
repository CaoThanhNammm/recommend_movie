import os
import logging
import sys
from app import create_app
from app.models.db import db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Ensure print statements work properly
sys.stdout.reconfigure(line_buffering=True)

if __name__ == '__main__':
    # Create Flask application
    app = create_app()
    
    # Create database tables
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully!")

    
    # Get configuration from environment variables
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    # Run the application
    logger.info(f"Starting application on {host}:{port} (debug={debug_mode})")

    app.run(debug=debug_mode, host=host, port=port)