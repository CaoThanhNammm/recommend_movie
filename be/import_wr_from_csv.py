#!/usr/bin/env python
"""
Script to import Weighted Rating (WR) values from the movies_processed_with_wr.csv file
into the database.

This script:
1. Reads the WR values from the CSV file
2. Updates the corresponding movies in the database

Usage:
    python import_wr_from_csv.py [--csv-path CSV_PATH]
"""

import argparse
import sys
import os
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.db import db
from app.models.movie import Movie

def import_wr_from_csv(csv_path):
    """
    Import WR values from CSV file and update the database.
    
    Args:
        csv_path (str): Path to the CSV file with WR values
        
    Returns:
        int: Number of movies updated
    """
    try:
        # Read CSV file
        print(f"Reading data from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        if 'WR' not in df.columns:
            print("Error: CSV file does not contain a 'WR' column.")
            return 0
            
        print(f"Found {len(df)} movies in the CSV file.")
        
        # Create a mapping of tmdb_id to WR
        wr_mapping = {}
        for _, row in df.iterrows():
            if pd.notna(row['tmdb_id']) and pd.notna(row['WR']):
                wr_mapping[int(row['tmdb_id'])] = float(row['WR'])
        
        print(f"Created mapping for {len(wr_mapping)} movies with valid tmdb_id and WR.")
        
        # Update movies in the database
        count = 0
        for tmdb_id, wr in wr_mapping.items():
            movie = Movie.query.filter_by(tmdb_id=tmdb_id).first()
            if movie:
                movie.wr = round(wr, 2)
                count += 1
        
        # Commit changes
        db.session.commit()
        print(f"Updated WR values for {count} movies in the database.")
        
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
        print(f"Error importing WR values: {str(e)}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Import WR values from CSV file')
    parser.add_argument('--csv-path', default='../dataset/movies_processed_with_wr.csv',
                        help='Path to the CSV file with WR values (default: ../dataset/movies_processed_with_wr.csv)')
    
    args = parser.parse_args()
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        import_wr_from_csv(args.csv_path)

if __name__ == "__main__":
    main()