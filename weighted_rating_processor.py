import pandas as pd
import numpy as np

class WeightedRatingProcessor:
    """
    A class to add a Weighted Rating (WR) column to the movies dataset.
    
    The Weighted Rating is calculated using the formula:
    WR = (v ÷ (v + m)) × R + (m ÷ (v + m)) × C
    
    Where:
    - R: Vote average of the movie
    - v: Vote count of the movie
    - m: Minimum vote count threshold to be considered reliable
    - C: Mean vote average of all movies in the dataset
    """
    
    def __init__(self, csv_path, min_vote_threshold=None):
        """
        Initialize the WeightedRatingProcessor.
        
        Args:
            csv_path (str): Path to the movies_processed.csv file
            min_vote_threshold (int, optional): Minimum vote count threshold. 
                                               If None, the median vote count will be used.
        """
        self.csv_path = csv_path
        self.min_vote_threshold = min_vote_threshold
        self.df = None
        
    def load_data(self):
        """Load the movies data from CSV file."""
        print(f"Loading data from {self.csv_path}...")
        self.df = pd.read_csv(self.csv_path)
        print(f"Loaded {len(self.df)} movies.")
        return self
        
    def calculate_weighted_rating(self):
        """
        Calculate the Weighted Rating for each movie and add it as a new column.
        
        Returns:
            self: For method chaining
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        # Extract vote_average and vote_count
        vote_averages = self.df['vote_average']
        vote_counts = self.df['vote_count']
        
        # Calculate mean vote average (C)
        C = vote_averages.mean()
        print(f"Mean vote average (C): {C:.2f}")
        
        # Determine minimum vote threshold (m)
        if self.min_vote_threshold is None:
            m = vote_counts.median()
            print(f"Using median vote count as threshold: {m:.2f}")
        else:
            m = self.min_vote_threshold
            print(f"Using provided vote threshold: {m}")
        
        # Calculate weighted rating
        # WR = (v ÷ (v + m)) × R + (m ÷ (v + m)) × C
        v = vote_counts
        R = vote_averages
        
        # Handle potential division by zero
        denominator = v + m
        weight_v = np.where(denominator > 0, v / denominator, 0)
        weight_m = np.where(denominator > 0, m / denominator, 1)  # Default to C if denominator is 0
        
        weighted_rating = weight_v * R + weight_m * C
        
        # Add the weighted rating column to the dataframe
        self.df['WR'] = weighted_rating
        
        # Round to 2 decimal places for readability
        self.df['WR'] = self.df['WR'].round(2)
        
        print("Weighted Rating (WR) column added successfully.")
        return self
    
    def save_data(self, output_path=None):
        """
        Save the updated dataframe with the WR column back to CSV.
        
        Args:
            output_path (str, optional): Path to save the updated CSV file.
                                        If None, overwrites the original file.
        
        Returns:
            str: Path to the saved file
        """
        if self.df is None:
            raise ValueError("Data not processed. Call calculate_weighted_rating() first.")
            
        # If no output path is provided, overwrite the original file
        if output_path is None:
            output_path = self.csv_path
            
        # Save to CSV
        self.df.to_csv(output_path, index=False)
        print(f"Updated data saved to {output_path}")
        return output_path
    
    def process(self, output_path=None):
        """
        Process the data: load, calculate weighted rating, and save.
        
        Args:
            output_path (str, optional): Path to save the updated CSV file.
        
        Returns:
            str: Path to the saved file
        """
        return (self.load_data()
                .calculate_weighted_rating()
                .save_data(output_path))


if __name__ == "__main__":
    # Example usage
    processor = WeightedRatingProcessor("dataset/movies_processed.csv")
    processor.process()
    
    # Alternative usage with custom threshold and output path
    # processor = WeightedRatingProcessor("dataset/movies_processed.csv", min_vote_threshold=100)
    # processor.process("dataset/movies_processed_with_wr.csv")
    
    # Print top 10 movies by weighted rating with at least 100 votes
    processor.load_data()
    processor.calculate_weighted_rating()
    
    # Filter movies with at least 100 votes
    filtered_df = processor.df[processor.df['vote_count'] >= 100]
    
    # Sort by weighted rating in descending order
    top_movies = filtered_df.sort_values('WR', ascending=False).head(10)
    
    print("\nTop 10 Movies by Weighted Rating (with at least 100 votes):")
    for _, movie in top_movies.iterrows():
        print(f"{movie['title']} - WR: {movie['WR']:.2f} (Votes: {movie['vote_count']}, Avg: {movie['vote_average']:.1f})")