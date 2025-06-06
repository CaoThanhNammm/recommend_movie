"""
CORS middleware for Flask application
"""
from flask import request, Response
import logging

logger = logging.getLogger(__name__)

class CORSMiddleware:
    """
    Middleware to handle CORS requests
    """
    def __init__(self, app):
        self.app = app
        self.app.before_request(self.handle_preflight)
        self.app.after_request(self.add_cors_headers)
        logger.info("CORS middleware initialized")
    
    def handle_preflight(self):
        """
        Handle preflight OPTIONS requests
        """
        if request.method == 'OPTIONS':
            logger.debug(f"Handling OPTIONS preflight request from origin: {request.headers.get('Origin')}")
            # Create a response for preflight requests
            # CORS headers will be added by the after_request handler
            return Response(status=200)
    
    def add_cors_headers(self, response):
        """
        Add CORS headers to all responses
        """
        # Allow requests from the frontend origin
        origin = request.headers.get('Origin')
        if origin:
            logger.debug(f"Setting CORS headers for origin: {origin}")
            # Use set() instead of add() to avoid duplicate headers
            response.headers.set('Access-Control-Allow-Origin', origin)
        else:
            # If no origin header, allow specific origins
            allowed_origins = ['http://127.0.0.1:5500', 'http://localhost:5500']
            logger.debug(f"No origin in request, setting CORS headers for default origins: {allowed_origins}")
            response.headers.set('Access-Control-Allow-Origin', 'http://127.0.0.1:5500')
        
        # Allow credentials
        response.headers.set('Access-Control-Allow-Credentials', 'true')
        
        # Allow all headers
        response.headers.set('Access-Control-Allow-Headers', 
                           'Origin, X-Requested-With, Content-Type, Accept, Authorization')
        
        # Allow all methods
        response.headers.set('Access-Control-Allow-Methods', 
                           'GET, POST, PUT, DELETE, OPTIONS, PATCH')
        
        # Cache preflight response for 1 hour
        response.headers.set('Access-Control-Max-Age', '3600')
        
        logger.debug(f"Response headers after CORS: {dict(response.headers)}")
        return response