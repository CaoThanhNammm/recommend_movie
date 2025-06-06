#!/usr/bin/env python
"""
Script to update the database with the WR (Weighted Rating) column and calculate values.

This script:
1. Adds the WR column to the movies table if it doesn't exist
2. Calculates the weighted rating for all movies using the formula:
   WR = (v ÷ (v + m)) × R + (m ÷ (v + m)) × C
3. Updates the movies table with the calculated values

Usage:
    python update_db_with_wr.py [--min-votes MIN_VOTES]
"""

import argparse
import sys
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.db import db
from app.models.movie import Movie

def add_wr_column():
    """Add the WR column to the movies table if it doesn't exist."""
    try:
        # Check if the column already exists
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(movies)"))
            columns = [row[1] for row in result]
            
            if 'wr' not in columns:
                print("Adding 'wr' column to movies table...")
                conn.execute(text("ALTER TABLE movies ADD COLUMN wr FLOAT"))
                print("Column added successfully.")
            else:
                print("The 'wr' column already exists in the movies table.")
                
        return True
    except SQLAlchemyError as e:
        print(f"Error adding column: {str(e)}")
        return False

def calculate_weighted_ratings(min_vote_threshold=None):
    """
    Calculate weighted ratings for all movies and update the database.
    
    Args:
        min_vote_threshold (int, optional): Minimum vote count threshold.
                                           If None, the median vote count will be used.
    """
    try:
        # Get all movies
        movies = Movie.query.all()
        
        if not movies:
            print("No movies found in the database.")
            return 0
            
        print(f"Found {len(movies)} movies in the database.")
            
        # Calculate mean vote average (C)
        vote_averages = [movie.vote_average for movie in movies if movie.vote_average is not None]
        C = sum(vote_averages) / len(vote_averages) if vote_averages else 0
        print(f"Mean vote average (C): {C:.2f}")
        
        # Determine minimum vote threshold (m)
        if min_vote_threshold is None:
            vote_counts = [movie.vote_count for movie in movies if movie.vote_count is not None]
            vote_counts.sort()
            m = vote_counts[len(vote_counts) // 2] if vote_counts else 0  # Median
            print(f"Using median vote count as threshold: {m:.2f}")
        else:
            m = min_vote_threshold
            print(f"Using provided vote threshold: {m}")
        
        # Calculate weighted rating for each movie
        count = 0
        for movie in movies:
            if movie.vote_average is not None and movie.vote_count is not None:
                v = movie.vote_count
                R = movie.vote_average
                
                # Calculate weighted rating
                # WR = (v ÷ (v + m)) × R + (m ÷ (v + m)) × C
                denominator = v + m
                if denominator > 0:
                    weight_v = v / denominator
                    weight_m = m / denominator
                    movie.wr = round((weight_v * R + weight_m * C), 2)
                    count += 1
        
        # Commit changes to database
        db.session.commit()
        print(f"Updated weighted ratings for {count} movies.")
        
        # Display some top movies by WR
        top_movies = Movie.query.filter(
            Movie.vote_count >= 100,
            Movie.wr.isnot(None)
        ).order_by(Movie.wr.desc()).limit(10).all()
        
        print("\nTop 10 Movies by Weighted Rating (with at least 100 votes):")
        print("-" * 80)
        print(f"{'Title':<50} {'WR':<6} {'Votes':<8} {'Avg':<5}")
        print("-" * 80)
        
        for movie in top_movies:
            print(f"{movie.title:<50} {movie.wr:<6.2f} {movie.vote_count:<8.0f} {movie.vote_average:<5.1f}")
        
        return count
        
    except Exception as e:
        db.session.rollback()
        print(f"Error calculating weighted ratings: {str(e)}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Update database with WR column and calculate weighted ratings')
    parser.add_argument('--min-votes', type=int, default=None,
                        help='Minimum vote count threshold (default: median vote count)')
    
    args = parser.parse_args()
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Add WR column to the database
        if add_wr_column():
            # Calculate weighted ratings
            calculate_weighted_ratings(min_vote_threshold=args.min_votes)

if __name__ == "__main__":
    main()