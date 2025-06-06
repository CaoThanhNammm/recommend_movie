#!/usr/bin/env python
"""
Script to create database tables for the movie recommendation system.

This script:
1. Creates all database tables defined in the models
2. Prints the list of created tables
"""

import sys
import os
from sqlalchemy import inspect

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.db import db

# Import all models to ensure they're registered with SQLAlchemy
from app.models.movie import Movie
from app.models.user import User
from app.models.user_rating import UserRating
from app.models.user_watch_history import UserWatchHistory
from app.models.user_preference import UserPreference
from app.models.genre import Genre
from app.models.cast import Cast
from app.models.crew import Crew

def create_tables():
    """Create all database tables."""
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Get list of existing tables
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print(f"Existing tables: {existing_tables}")
        
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Get list of tables after creation
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"Tables in database: {tables}")
        
        # Check if our models' tables exist
        model_tables = [
            Movie.__tablename__,
            User.__tablename__,
            UserRating.__tablename__,
            UserWatchHistory.__tablename__,
            UserPreference.__tablename__,
            Genre.__tablename__,
            Cast.__tablename__,
            Crew.__tablename__
        ]
        
        print("\nChecking if model tables exist:")
        for table in model_tables:
            exists = table in tables
            print(f"- {table}: {'✓' if exists else '✗'}")

if __name__ == "__main__":
    create_tables()