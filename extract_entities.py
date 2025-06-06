#!/usr/bin/env python
"""
Script to extract unique genres, cast, and crew from the movies_processed_with_wr.csv file
and create three separate CSV files.

This script:
1. Reads the movies_processed_with_wr.csv file
2. Extracts all unique genres, cast members, and crew members
3. Creates three CSV files: genres.csv, cast.csv, and crew.csv
"""

import pandas as pd
import json
import os
import ast

def safe_eval(text):
    """Safely evaluate a string containing a Python literal structure."""
    if pd.isna(text) or not text:
        return []
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return []

def extract_entities(csv_path, output_dir='dataset'):
    """
    Extract unique genres, cast, and crew from the movies CSV file.
    
    Args:
        csv_path (str): Path to the movies CSV file
        output_dir (str): Directory to save the output CSV files
    """
    print(f"Reading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract genres
    print("Extracting genres...")
    genres_set = set()
    for genres_str in df['genres'].dropna():
        genres = safe_eval(genres_str)
        for genre in genres:
            if isinstance(genre, dict) and 'name' in genre and 'id' in genre:
                genres_set.add((genre['id'], genre['name']))
    
    # Create genres DataFrame and save to CSV
    genres_df = pd.DataFrame(list(genres_set), columns=['id', 'name'])
    genres_df = genres_df.sort_values('name')
    genres_csv_path = os.path.join(output_dir, 'genres_extracted.csv')
    genres_df.to_csv(genres_csv_path, index=False)
    print(f"Saved {len(genres_df)} unique genres to {genres_csv_path}")
    
    # Extract cast
    print("Extracting cast members...")
    cast_set = set()
    for cast_str in df['cast'].dropna():
        cast_list = safe_eval(cast_str)
        for cast_member in cast_list:
            if isinstance(cast_member, dict) and 'id' in cast_member and 'name' in cast_member:
                # Extract relevant fields
                cast_id = cast_member.get('id')
                name = cast_member.get('name')
                gender = cast_member.get('gender')
                profile_path = cast_member.get('profile_path')
                
                cast_set.add((cast_id, name, gender, profile_path))
    
    # Create cast DataFrame and save to CSV
    cast_df = pd.DataFrame(list(cast_set), columns=['id', 'name', 'gender', 'profile_path'])
    cast_df = cast_df.sort_values('name')
    cast_csv_path = os.path.join(output_dir, 'cast_extracted.csv')
    cast_df.to_csv(cast_csv_path, index=False)
    print(f"Saved {len(cast_df)} unique cast members to {cast_csv_path}")
    
    # Extract crew
    print("Extracting crew members...")
    crew_set = set()
    for crew_str in df['crew'].dropna():
        crew_list = safe_eval(crew_str)
        for crew_member in crew_list:
            if isinstance(crew_member, dict) and 'id' in crew_member and 'name' in crew_member:
                # Extract relevant fields
                crew_id = crew_member.get('id')
                name = crew_member.get('name')
                department = crew_member.get('department')
                job = crew_member.get('job')
                gender = crew_member.get('gender')
                profile_path = crew_member.get('profile_path')
                
                crew_set.add((crew_id, name, department, job, gender, profile_path))
    
    # Create crew DataFrame and save to CSV
    crew_df = pd.DataFrame(list(crew_set), columns=['id', 'name', 'department', 'job', 'gender', 'profile_path'])
    crew_df = crew_df.sort_values(['department', 'name'])
    crew_csv_path = os.path.join(output_dir, 'crew_extracted.csv')
    crew_df.to_csv(crew_csv_path, index=False)
    print(f"Saved {len(crew_df)} unique crew members to {crew_csv_path}")
    
    return genres_csv_path, cast_csv_path, crew_csv_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract unique genres, cast, and crew from movies CSV')
    parser.add_argument('--csv-path', default='dataset/movies_processed_with_wr.csv',
                        help='Path to the movies CSV file (default: dataset/movies_processed_with_wr.csv)')
    parser.add_argument('--output-dir', default='dataset',
                        help='Directory to save the output CSV files (default: dataset)')
    
    args = parser.parse_args()
    
    extract_entities(args.csv_path, args.output_dir)