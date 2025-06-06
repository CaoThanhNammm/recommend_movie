from app.models.db import db
from app.models.movie import Movie
from app.models.user_preference import UserPreference
from app.models.user_watch_history import UserWatchHistory
from app.services.movie_embedder_service import get_instance as get_embedder_instance
import logging
from sqlalchemy import func
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class RecommendationService:
    @staticmethod
    def get_movies_by_weighted_rating(min_wr: float, limit: int = 20) -> List[Movie]:
        """
        Get movies with weighted rating (WR) greater than the specified value.
        
        Args:
            min_wr (float): Minimum weighted rating threshold
            limit (int): Maximum number of movies to return
            
        Returns:
            List[Movie]: List of movies with WR greater than min_wr
        """
        return Movie.query.filter(
            Movie.wr.isnot(None),
            Movie.wr > min_wr
        ).order_by(Movie.wr.desc()).limit(limit).all()
    
    @staticmethod
    def _process_search_results(results: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Process search results from embedder and convert to movie recommendations.
        
        Args:
            results (List[Dict[str, Any]]): Search results from embedder
            limit (int): Maximum number of movies to return
            
        Returns:
            List[Dict[str, Any]]: List of recommended movies with metadata
        """
        # Get movie IDs from results
        movie_ids = [result.get('id') for result in results if 'id' in result]
        logger.debug(f"Extracted movie_ids: {movie_ids}")
        
        # Create a mapping from original ID to integer ID for later use
        id_mapping = {}
        
        # Convert IDs to integers to ensure type consistency with database
        try:
            converted_ids = []
            for id_str in movie_ids:
                try:
                    id_int = int(id_str)
                    converted_ids.append(id_int)
                    id_mapping[id_str] = id_int
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error converting individual ID {id_str} to integer: {e}")
            
            movie_ids = converted_ids
            logger.debug(f"Converted movie_ids to integers: {len(movie_ids)} ids")
        except Exception as e:
            logger.error(f"Error in ID conversion process: {e}")
            # If conversion fails, try to use the original IDs
        
        # Fetch full movie data from database
        movies = Movie.query.filter(Movie.id.in_(movie_ids)).all()
        logger.debug(f"Found {len(movies)} movies in database")
        
        # Create a mapping of movie ID to movie object
        movie_map = {movie.id: movie for movie in movies}
        
        # Combine results with full movie data
        recommendations = []
        
        for result in results:
            movie_id_str = result.get('id')
            
            # Use the ID mapping we created earlier
            if movie_id_str in id_mapping:
                movie_id_int = id_mapping[movie_id_str]
                
                if movie_id_int in movie_map:
                    movie_dict = movie_map[movie_id_int].to_dict()
                    movie_dict['similarity'] = result.get('similarity', 0)
                    recommendations.append(movie_dict)
            else:
                # Try direct conversion as fallback
                try:
                    movie_id_int = int(movie_id_str)
                    
                    if movie_id_int in movie_map:
                        movie_dict = movie_map[movie_id_int].to_dict()
                        movie_dict['similarity'] = result.get('similarity', 0)
                        recommendations.append(movie_dict)
                except (ValueError, TypeError):
                    # Try with original string ID as last resort
                    if movie_id_str in movie_map:
                        movie_dict = movie_map[movie_id_str].to_dict()
                        movie_dict['similarity'] = result.get('similarity', 0)
                        recommendations.append(movie_dict)
        
        logger.debug(f"Final recommendations count: {len(recommendations)}")
        return recommendations[:limit]
    
    @staticmethod
    def get_recommendations_by_preferences(
        favorite_genres: str, 
        favorite_actors: str, 
        favorite_directors: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get movie recommendations based on user preferences using FAISS.
        
        Args:
            favorite_genres (str): Comma-separated string of favorite genres
            favorite_actors (str): Comma-separated string of favorite actors
            favorite_directors (str): Comma-separated string of favorite directors
            limit (int): Maximum number of movies to return
            
        Returns:
            List[Dict[str, Any]]: List of recommended movies with metadata
        """
        # Combine preferences into a single query string
        preferences = []
        
        if favorite_genres:
            preferences.append(f"{favorite_genres}")
        
        if favorite_actors:
            preferences.append(f"{favorite_actors}")
        
        if favorite_directors:
            preferences.append(f"{favorite_directors}")
        
        # If no preferences, return empty list
        if not preferences:
            return []
        
        # Create query string
        query = ",".join(preferences)
        logger.debug(f"Preference query: {query}")
        
        # Get embedder instance
        embedder = get_embedder_instance()
        
        # Search for similar movies
        results = embedder.search(query, k=limit)
        
        # Process results
        return RecommendationService._process_search_results(results, limit)
    
    @staticmethod
    def _extract_movie_features(movies: List[Movie]) -> Dict[str, List[str]]:
        """
        Extract features from a list of movies.
        
        Args:
            movies (List[Movie]): List of movies
            
        Returns:
            Dict[str, List[str]]: Dictionary of extracted features
        """
        titles = []
        overviews = []
        genres_list = []
        cast_list = []
        crew_list = []
        keywords_list = []
        
        for movie in movies:
            titles.append(movie.title)
            
            if movie.overview:
                overviews.append(movie.overview)
            
            genres = movie.get_genres_list()
            if genres:
                genres_str = ", ".join([g['name'] if isinstance(g, dict) and 'name' in g else g for g in genres])
                genres_list.append(genres_str)
            
            cast = movie.get_cast_list()
            if cast:
                cast_str = ", ".join([c['name'] if isinstance(c, dict) and 'name' in c else c for c in cast[:5]])
                cast_list.append(cast_str)
            
            crew = movie.get_crew_list()
            if crew:
                directors = [c['name'] for c in crew if isinstance(c, dict) and c.get('job') == 'Director']
                if directors:
                    crew_list.append(", ".join(directors))
            
            keywords = movie.get_keywords_list()
            if keywords:
                keywords_str = ", ".join([k['name'] if isinstance(k, dict) and 'name' in k else k for k in keywords])
                keywords_list.append(keywords_str)
        
        return {
            'titles': titles,
            'overviews': overviews,
            'genres': genres_list,
            'cast': cast_list,
            'crew': crew_list,
            'keywords': keywords_list
        }
    
    @staticmethod
    def get_recommendations_by_history_and_preferences(
        movie_ids: str,
        favorite_genres: str, 
        favorite_actors: str, 
        favorite_directors: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get movie recommendations based on watch history and user preferences using FAISS.
        
        Args:
            movie_ids (str): Comma-separated string of watched movie IDs
            favorite_genres (str): Comma-separated string of favorite genres
            favorite_actors (str): Comma-separated string of favorite actors
            favorite_directors (str): Comma-separated string of favorite directors
            limit (int): Maximum number of movies to return
            
        Returns:
            List[Dict[str, Any]]: List of recommended movies with metadata
        """
        # Parse movie IDs
        try:
            watched_movie_ids = [int(id.strip()) for id in movie_ids.split(',') if id.strip()]
        except ValueError:
            watched_movie_ids = []
        
        # If no watch history, fall back to preference-based recommendations
        if not watched_movie_ids:
            return RecommendationService.get_recommendations_by_preferences(
                favorite_genres, favorite_actors, favorite_directors, limit
            )
        
        # Fetch watched movies data
        watched_movies = Movie.query.filter(Movie.id.in_(watched_movie_ids)).all()
        
        # Extract relevant information from watched movies
        features = RecommendationService._extract_movie_features(watched_movies)
        
        # Combine watch history data
        query_parts = []
        
        if features['titles']:
            query_parts.append(f"Movies: {', '.join(features['titles'])}")
        
        if features['overviews']:
            # Limit the length of overviews to avoid too long queries
            combined_overview = " ".join(features['overviews'])
            if len(combined_overview) > 500:
                combined_overview = combined_overview[:500] + "..."
            query_parts.append(f"Themes: {combined_overview}")
        
        if features['genres']:
            query_parts.append(f"Genres: {', '.join(features['genres'])}")
        
        if features['cast']:
            query_parts.append(f"Actors: {', '.join(features['cast'])}")
        
        if features['crew']:
            query_parts.append(f"Directors: {', '.join(features['crew'])}")
        
        if features['keywords']:
            query_parts.append(f"Keywords: {', '.join(features['keywords'])}")
        
        # Add user preferences
        if favorite_genres:
            query_parts.append(f"Favorite Genres: {favorite_genres}")
        
        if favorite_actors:
            query_parts.append(f"Favorite Actors: {favorite_actors}")
        
        if favorite_directors:
            query_parts.append(f"Favorite Directors: {favorite_directors}")
        
        # Create query string
        query = " ".join(query_parts)
        logger.debug(f"History and preferences query: {query[:100]}...")
        
        # Get embedder instance
        embedder = get_embedder_instance()
        
        # Search for similar movies
        results = embedder.search(query, k=limit + len(watched_movie_ids))
        
        # Filter out already watched movies
        filtered_results = [result for result in results if int(result.get('id', 0)) not in watched_movie_ids]
        
        # Limit results
        filtered_results = filtered_results[:limit]
        
        # Process results
        return RecommendationService._process_search_results(filtered_results, limit)
    
    @staticmethod
    def get_user_preferences(user_id: int) -> Optional[UserPreference]:
        """
        Get user preferences from database.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Optional[UserPreference]: User preference object or None if not found
        """
        return UserPreference.query.filter_by(user_id=user_id).first()
    
    @staticmethod
    def get_user_watch_history(user_id: int) -> List[UserWatchHistory]:
        """
        Get user watch history from database.
        
        Args:
            user_id (int): User ID
            
        Returns:
            List[UserWatchHistory]: List of user watch history entries
        """
        return UserWatchHistory.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def get_personalized_recommendations(user_id: int, limit: int = 20, min_wr: float = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Get personalized recommendations based on user data.
        
        This method implements the combined recommendation approach:
        - If user has no preferences, use weighted rating (Stage 1)
        - If user has preferences but no watch history, use preferences (Stage 2)
        - If user has both preferences and watch history, use both (Stage 3)
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of movies to return
            min_wr (float, optional): Minimum weighted rating threshold for Stage 1
                If not provided, the average WR will be used
            
        Returns:
            Tuple[List[Dict[str, Any]], str]: Tuple of (recommendations, stage)
                where stage is one of: "stage1", "stage2", "stage3"
        """
        # Get user preferences
        user_preferences = RecommendationService.get_user_preferences(user_id)
        
        # If no preferences, use weighted rating (Stage 1)
        if not user_preferences:
            # If min_wr not provided, use average weighted rating as threshold
            if min_wr is None:
                min_wr = db.session.query(func.avg(Movie.wr)).filter(Movie.wr.isnot(None)).scalar() or 0
            
            movies = RecommendationService.get_movies_by_weighted_rating(min_wr, limit)
            return [movie.to_dict() for movie in movies], "stage1"
        
        # Get user watch history
        watch_history = RecommendationService.get_user_watch_history(user_id)
        
        # If no watch history, use preferences (Stage 2)
        if not watch_history:
            recommendations = RecommendationService.get_recommendations_by_preferences(
                user_preferences.favorite_genres,
                user_preferences.favorite_actors,
                user_preferences.favorite_directors,
                limit
            )
            return recommendations, "stage2"
        
        # If both preferences and watch history, use both (Stage 3)
        
        # Get movie_ids from watch history
        watched_movie_ids = [str(entry.movie_id) for entry in watch_history]
        
        # Create the watched_movie string using movie IDs
        watched_movie = ','.join(watched_movie_ids)
        
        recommendations = RecommendationService.get_recommendations_by_history_and_preferences(
            watched_movie,
            user_preferences.favorite_genres,
            user_preferences.favorite_actors,
            user_preferences.favorite_directors,
            limit
        )
        return recommendations, "stage3"