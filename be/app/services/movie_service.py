from app.models.db import db
from app.models.movie import Movie
from app.models.user_rating import UserRating
from app.models.user_watch_history import UserWatchHistory
from datetime import datetime
import json 
import logging

# Configure logger
logger = logging.getLogger(__name__)

class MovieService:
    @staticmethod
    def get_movies(page=1, per_page=20, genre=None, search=None):
        """
        Get a paginated list of movies with optional filtering.
        
        Args:
            page (int): The page number
            per_page (int): The number of items per page
            genre (str, optional): Filter by genre
            search (str, optional): Filter by title search
            
        Returns:
            tuple: (movies, total, pages, current_page)
        """
        # Base query
        query = Movie.query
        
        # Apply filters
        if genre:
            query = query.filter(Movie.genres.like(f'%{genre}%'))
        
        if search:
            query = query.filter(Movie.title.like(f'%{search}%'))
        
        # Paginate results
        movies_pagination = query.order_by(Movie.popularity.desc()).paginate(page=page, per_page=per_page)
        
        return (
            movies_pagination.items,
            movies_pagination.total,
            movies_pagination.pages,
            movies_pagination.page
        )
    
    @staticmethod
    def get_movie_by_id(movie_id):
        """
        Get a movie by its ID.
        
        Args:
            movie_id (int): The ID of the movie
            
        Returns:
            Movie: The movie object or None if not found
        """
        movie = Movie.query.get(movie_id)
        print('Movie found:', movie)
        print('cast', movie.cast)
        print('crew',movie.crew)
        print('genres',movie.genres)
        print('keyword',movie.keywords) 
        print('production_companies',movie.production_companies) 
        return movie
    

    @staticmethod
    def rate_movie(user_id, movie_id, rating, review=None):
        """
        Rate a movie.
        
        Args:
            user_id (int): The ID of the user
            movie_id (int): The ID of the movie
            rating (float): The rating value (0.5 to 5.0)
            review (str, optional): The review text
            
        Returns:
            tuple: (success, message)
                If successful, returns (True, "Rating saved successfully")
                If error, returns (False, error_message)
        """
        # Validate rating
        if rating < 0.5 or rating > 5.0:
            return False, "Rating must be between 0.5 and 5.0"
        
        # Check if movie exists
        movie = Movie.query.get(movie_id)
        if not movie:
            return False, "Movie not found"
        
        try:
            # Check if user has already rated this movie
            existing_rating = UserRating.query.filter_by(user_id=user_id, movie_id=movie_id).first()
            
            if existing_rating:
                # Update existing rating
                existing_rating.rating = rating
                existing_rating.review = review
                existing_rating.updated_at = datetime.utcnow()
            else:
                # Create new rating
                new_rating = UserRating(
                    user_id=user_id,
                    movie_id=movie_id,
                    rating=rating,
                    review=review
                )
                db.session.add(new_rating)
            
            db.session.commit()
            
            return True, "Rating saved successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error saving rating: {str(e)}"
    
    @staticmethod
    def mark_as_watched(user_id, movie_id):
        """
        Mark a movie as watched by a user.
        
        Args:
            user_id (int): The ID of the user
            movie_id (int): The ID of the movie
            
        Returns:
            tuple: (success, message)
                If successful, returns (True, "Movie marked as watched")
                If error, returns (False, error_message)
        """
        # Check if movie exists
        movie = Movie.query.get(movie_id)
        if not movie:
            return False, "Movie not found"
        
        try:
            # Add to watch history
            watch_entry = UserWatchHistory(
                user_id=user_id,
                movie_id=movie_id,
                watched_at=datetime.utcnow()
            )
            db.session.add(watch_entry)
            db.session.commit()
            
            return True, "Movie marked as watched"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating watch history: {str(e)}"
    
    @staticmethod
    def get_all_genres():
        """
        Get all unique genres from the database.
        
        Returns:
            list: A list of unique genre names
        """
        movies = Movie.query.all()
        all_genres = set()
        
        for movie in movies:
            genres = movie.get_genres_list()
            for genre in genres:
                if isinstance(genre, dict) and 'name' in genre:
                    all_genres.add(genre['name'])
                elif isinstance(genre, str):
                    all_genres.add(genre)
        
        return list(all_genres)
    
    @staticmethod
    def get_trending_movies(limit=10):
        """
        Get trending movies based on popularity.
        
        Args:
            limit (int): The maximum number of movies to return
            
        Returns:
            list: A list of trending movies
        """
        return Movie.query.order_by(Movie.popularity.desc()).limit(limit).all()
    
    @staticmethod
    def get_top_rated_movies(limit=10, min_votes=100):
        """
        Get top rated movies with a minimum number of votes.
        
        Args:
            limit (int): The maximum number of movies to return
            min_votes (int): The minimum number of votes required
            
        Returns:
            list: A list of top rated movies
        """
        # If WR is available, use it for ranking; otherwise, fall back to vote_average
        return Movie.query.filter(Movie.vote_count >= min_votes).order_by(
            Movie.wr.desc().nullslast(), 
            Movie.vote_average.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_top_weighted_rated_movies(limit=10, min_votes=100):
        """
        Get top movies based on weighted rating (WR) with a minimum number of votes.
        
        Args:
            limit (int): The maximum number of movies to return
            min_votes (int): The minimum number of votes required
            
        Returns:
            list: A list of top movies by weighted rating
        """
        return Movie.query.filter(
            Movie.vote_count >= min_votes,
            Movie.wr.isnot(None)  # Ensure WR is not null
        ).order_by(Movie.wr.desc()).limit(limit).all()
        
    @staticmethod
    def calculate_weighted_ratings(min_vote_threshold=None):
        """
        Calculate and update weighted ratings for all movies in the database.
        
        The Weighted Rating is calculated using the formula:
        WR = (v ÷ (v + m)) × R + (m ÷ (v + m)) × C
        
        Where:
        - R: Vote average of the movie
        - v: Vote count of the movie
        - m: Minimum vote count threshold to be considered reliable
        - C: Mean vote average of all movies in the dataset
        
        Args:
            min_vote_threshold (int, optional): Minimum vote count threshold.
                                               If None, the median vote count will be used.
        
        Returns:
            int: Number of movies updated
        """
        try:
            # Get all movies
            movies = Movie.query.all()
            
            if not movies:
                return 0
                
            # Calculate mean vote average (C)
            vote_averages = [movie.vote_average for movie in movies if movie.vote_average is not None]
            C = sum(vote_averages) / len(vote_averages) if vote_averages else 0
            
            # Determine minimum vote threshold (m)
            if min_vote_threshold is None:
                vote_counts = [movie.vote_count for movie in movies if movie.vote_count is not None]
                vote_counts.sort()
                m = vote_counts[len(vote_counts) // 2] if vote_counts else 0  # Median
            else:
                m = min_vote_threshold
            
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
            return count
            
        except Exception as e:
            db.session.rollback()
            raise e