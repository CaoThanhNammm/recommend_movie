#!/usr/bin/env python
"""
Script to add a Weighted Rating (WR) column to the movies_processed.csv file.

The Weighted Rating is calculated using the formula:
WR = (v ÷ (v + m)) × R + (m ÷ (v + m)) × C

Where:
- R: Vote average of the movie
- v: Vote count of the movie
- m: Minimum vote count threshold to be considered reliable
- C: Mean vote average of all movies in the dataset
"""

import argparse
from weighted_rating_processor import WeightedRatingProcessor

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Add Weighted Rating column to movies dataset')
    parser.add_argument('--input', default='dataset/movies_processed.csv',
                        help='Path to the input CSV file (default: dataset/movies_processed.csv)')
    parser.add_argument('--output', default=None,
                        help='Path to save the output CSV file (default: overwrites input file)')
    parser.add_argument('--threshold', type=int, default=None,
                        help='Minimum vote count threshold (default: median vote count)')
    parser.add_argument('--top', type=int, default=10,
                        help='Number of top movies to display (default: 10)')
    parser.add_argument('--min-votes', type=int, default=100,
                        help='Minimum votes for a movie to be included in top list (default: 100)')
    
    args = parser.parse_args()
    
    # Create processor and process the data
    processor = WeightedRatingProcessor(args.input, min_vote_threshold=args.threshold)
    output_path = processor.process(args.output)
    
    print(f"\nProcessing complete. Updated file saved to: {output_path}")
    
    # Display top movies by weighted rating
    processor.load_data()
    processor.calculate_weighted_rating()
    
    # Filter movies with minimum votes
    filtered_df = processor.df[processor.df['vote_count'] >= args.min_votes]
    
    # Sort by weighted rating in descending order
    top_movies = filtered_df.sort_values('WR', ascending=False).head(args.top)
    
    print(f"\nTop {args.top} Movies by Weighted Rating (with at least {args.min_votes} votes):")
    print("-" * 80)
    print(f"{'Title':<50} {'WR':<6} {'Votes':<8} {'Avg':<5}")
    print("-" * 80)
    
    for _, movie in top_movies.iterrows():
        print(f"{movie['title']:<50} {movie['WR']:<6.2f} {movie['vote_count']:<8.0f} {movie['vote_average']:<5.1f}")

if __name__ == "__main__":
    main()