from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.recommendation_service import RecommendationService
import logging
from app.models.db import db
from app.models.movie import Movie
from sqlalchemy import func
import os
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
recommendation_bp = Blueprint('recommendation', __name__)

# Get API timeout from environment
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 30))

def handle_exceptions(f):
    """
    Decorator to handle exceptions in API endpoints.
    
    Args:
        f: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'message': f'Error getting recommendations: {str(e)}'
            }), 500
    return decorated_function

@recommendation_bp.route('/by-weighted-rating', methods=['POST'])
@jwt_required()
@handle_exceptions
def get_recommendations_by_weighted_rating():
    """
    Get movie recommendations based on weighted rating.
    
    Authentication:
        Requires JWT Bearer token in the Authorization header
    
    Request Body:
        {
            "min_wr": float,  // Optional, default: average WR
            "limit": int      // Optional, default: 20
        }
    
    Returns:
        JSON response with recommended movies
    """
    # Get user ID from JWT
    user_id = int(get_jwt_identity())
    
    # Get parameters from request body
    data = request.get_json() or {}
    min_wr = data.get('min_wr')
    limit = data.get('limit', 20)
    
    # If min_wr not provided, use average WR
    if min_wr is None:
        min_wr = db.session.query(func.avg(Movie.wr)).filter(Movie.wr.isnot(None)).scalar() or 0
    
    # Get recommendations
    movies = RecommendationService.get_movies_by_weighted_rating(min_wr, limit)
    
    return jsonify({
        'recommendations': [movie.to_dict() for movie in movies],
        'count': len(movies),
        'min_wr': min_wr,
        'user_id': user_id
    }), 200

@recommendation_bp.route('/by-preferences/', methods=['POST'])
@jwt_required()
@handle_exceptions
def get_recommendations_by_preferences():
    """
    Get movie recommendations based on user preferences.
    
    Authentication:
        Requires JWT Bearer token in the Authorization header
    
    Request Body:
        {
            "favorite_genres": "string, string, string",
            "favorite_actors": "string, string, string",
            "favorite_directors": "string, string, string",
            "limit": int (optional, default: 20)
        }
    
    Returns:
        JSON response with recommended movies
    """
    # Get user ID from JWT
    user_id = int(get_jwt_identity())
    
    # Get data from request
    data = request.get_json()
    
    if not data:
        return jsonify({
            'message': 'No data provided'
        }), 400
    
    # Extract parameters
    favorite_genres = data.get('favorite_genres', '')
    favorite_actors = data.get('favorite_actors', '')
    favorite_directors = data.get('favorite_directors', '')
    limit = data.get('limit', 20)
    
    # Get recommendations
    recommendations = RecommendationService.get_recommendations_by_preferences(
        favorite_genres, favorite_actors, favorite_directors, limit
    )
    
    return jsonify({
        'recommendations': recommendations,
        'count': len(recommendations),
        'user_id': user_id
    }), 200

@recommendation_bp.route('/by-history-and-preferences', methods=['POST'])
@jwt_required()
@handle_exceptions
def get_recommendations_by_history_and_preferences():
    """
    Get movie recommendations based on watch history and user preferences.
    
    Authentication:
        Requires JWT Bearer token in the Authorization header
    
    Request Body:
        {
            "movie_ids": "id, id, id",
            "favorite_genres": "string, string, string",
            "favorite_actors": "string, string, string",
            "favorite_directors": "string, string, string",
            "limit": int (optional, default: 20)
        }
    
    Returns:
        JSON response with recommended movies
    """
    # Get user ID from JWT
    user_id = int(get_jwt_identity())
    
    # Get data from request
    data = request.get_json()
    
    if not data:
        return jsonify({
            'message': 'No data provided'
        }), 400
    
    # Extract parameters
    movie_ids = data.get('movie_ids', '')
    favorite_genres = data.get('favorite_genres', '')
    favorite_actors = data.get('favorite_actors', '')
    favorite_directors = data.get('favorite_directors', '')
    limit = data.get('limit', 20)
    
    # Get recommendations
    recommendations = RecommendationService.get_recommendations_by_history_and_preferences(
        movie_ids, favorite_genres, favorite_actors, favorite_directors, limit
    )
    
    return jsonify({
        'recommendations': recommendations,
        'count': len(recommendations),
        'user_id': user_id
    }), 200

@recommendation_bp.route('/personalized/', methods=['POST'])
@jwt_required()
@handle_exceptions
def get_personalized_recommendations():
    """
    Get personalized recommendations based on user data.
    
    This endpoint implements the combined recommendation approach:
    - If user has no preferences, use weighted rating (Stage 1)
    - If user has preferences but no watch history, use preferences (Stage 2)
    - If user has both preferences and watch history, use both (Stage 3)
    
    Authentication:
        Requires JWT Bearer token in the Authorization header
    
    Request Body:
        {
            "limit": int,  // Optional, default: 20
            "min_wr": float  // Optional, for Stage 1
        }
    
    Returns:
        JSON response with recommended movies and the stage used
    """
    # Get user ID from JWT
    user_id = int(get_jwt_identity())
    
    # Get parameters from request body
    data = request.get_json() or {}
    limit = data.get('limit', 20)
    min_wr = data.get('min_wr')
    
    # Get personalized recommendations
    recommendations, stage = RecommendationService.get_personalized_recommendations(
        user_id, 
        limit=limit,
        min_wr=min_wr
    )
    
    return jsonify({
        'recommendations': recommendations,
        'count': len(recommendations),
        'stage': stage
    }), 200