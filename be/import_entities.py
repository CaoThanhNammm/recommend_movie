#!/usr/bin/env python
"""
Script to import genres, cast, and crew from CSV files into the database.

This script:
1. Adds the WR column to the movies table if it doesn't exist
2. Imports genres from genres_extracted.csv
3. Imports cast members from cast_extracted.csv
4. Imports crew members from crew_extracted.csv

Usage:
    python import_entities.py [--genres-csv GENRES_CSV] [--cast-csv CAST_CSV] [--crew-csv CREW_CSV]
"""

import argparse
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.genre_service import GenreService
from app.services.cast_service import CastService
from app.services.crew_service import CrewService

def import_entities(genres_csv, cast_csv, crew_csv):
    """
    Import entities from CSV files.
    
    Args:
        genres_csv (str): Path to the genres CSV file
        cast_csv (str): Path to the cast CSV file
        crew_csv (str): Path to the crew CSV file
    """
    # Import genres
    if os.path.exists(genres_csv):
        print(f"\nImporting genres from {genres_csv}...")
        count, message = GenreService.import_genres_from_csv(genres_csv)
        print(f"{message} ({count} genres imported)")
    else:
        print(f"Genres CSV file not found: {genres_csv}")
    
    # Import cast
    if os.path.exists(cast_csv):
        print(f"\nImporting cast from {cast_csv}...")
        count, message = CastService.import_cast_from_csv(cast_csv)
        print(f"{message} ({count} cast members imported)")
    else:
        print(f"Cast CSV file not found: {cast_csv}")
    
    # Import crew
    if os.path.exists(crew_csv):
        print(f"\nImporting crew from {crew_csv}...")
        count, message = CrewService.import_crew_from_csv(crew_csv)
        print(f"{message} ({count} crew members imported)")
    else:
        print(f"Crew CSV file not found: {crew_csv}")

def main():
    parser = argparse.ArgumentParser(description='Import entities from CSV files')
    parser.add_argument('--genres-csv', default='../dataset/genres_extracted.csv',
                        help='Path to the genres CSV file (default: ../dataset/genres_extracted.csv)')
    parser.add_argument('--cast-csv', default='../dataset/cast_extracted.csv',
                        help='Path to the cast CSV file (default: ../dataset/cast_extracted.csv)')
    parser.add_argument('--crew-csv', default='../dataset/crew_extracted.csv',
                        help='Path to the crew CSV file (default: ../dataset/crew_extracted.csv)')
    
    args = parser.parse_args()
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        import_entities(args.genres_csv, args.cast_csv, args.crew_csv)

if __name__ == "__main__":
    main()