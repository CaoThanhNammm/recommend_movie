"""
Middleware package for Flask application
"""
from app.middleware.cors_middleware import CORSMiddleware

__all__ = ['CORSMiddleware']