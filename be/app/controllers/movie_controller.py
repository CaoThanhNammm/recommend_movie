from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.movie_service import MovieService

movie_bp = Blueprint('movie', __name__)

@movie_bp.route('/', methods=['GET'])
def get_movies():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    genre = request.args.get('genre')
    search = request.args.get('search')
    
    # Get movies using service
    movies, total, pages, current_page = MovieService.get_movies(
        page=page,
        per_page=per_page,
        genre=genre,
        search=search
    )
    
    return jsonify({
        'movies': [movie.to_dict() for movie in movies],
        'total': total,
        'pages': pages,
        'current_page': current_page
    }), 200

@movie_bp.route('/<int:movie_id>/', methods=['GET'])
def get_movie(movie_id):
    # Get movie using service
    movie = MovieService.get_movie_by_id(movie_id)
    
    if not movie:
        return jsonify({'message': 'Movie not found'}), 404
    
    return jsonify(movie.to_dict()), 200

@movie_bp.route('/<int:movie_id>/rate/', methods=['POST'])
@jwt_required()
def rate_movie(movie_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # Validate input
    if not data or 'rating' not in data:
        return jsonify({'message': 'Rating is required'}), 400
    
    # Rate movie using service
    success, message = MovieService.rate_movie(
        user_id=user_id,
        movie_id=movie_id,
        rating=float(data['rating']),
        review=data.get('review')
    )
    
    if not success:
        status_code = 400 if "between 0.5 and 5.0" in message else 404 if "not found" in message else 500
        return jsonify({'message': message}), status_code
    
    return jsonify({'message': message}), 200

@movie_bp.route('/<int:movie_id>/watch/', methods=['POST'])
@jwt_required()
def mark_as_watched(movie_id):
    user_id = int(get_jwt_identity())
    
    # Mark movie as watched using service
    success, message = MovieService.mark_as_watched(user_id, movie_id)
    
    if not success:
        status_code = 404 if "not found" in message else 500
        return jsonify({'message': message}), status_code
    
    return jsonify({'message': message}), 200

@movie_bp.route('/genres', methods=['GET'])
def get_genres():
    # Get all genres using service
    genres = MovieService.get_all_genres()
    
    return jsonify(genres), 200

@movie_bp.route('/top-weighted', methods=['GET'])
def get_top_weighted_rated():
    limit = request.args.get('limit', 10, type=int)
    min_votes = request.args.get('min_votes', 100, type=int)
    
    # Get top movies by weighted rating
    movies = MovieService.get_top_weighted_rated_movies(limit=limit, min_votes=min_votes)
    
    return jsonify({
        'movies': [movie.to_dict() for movie in movies]
    }), 200

@movie_bp.route('/calculate-wr', methods=['POST'])
def calculate_weighted_ratings():
    min_vote_threshold = request.args.get('min_votes', None, type=int)
    
    try:
        # Calculate weighted ratings for all movies
        count = MovieService.calculate_weighted_ratings(min_vote_threshold=min_vote_threshold)
        
        return jsonify({
            'message': f'Weighted ratings calculated for {count} movies',
            'count': count
        }), 200
    except Exception as e:
        return jsonify({
            'message': f'Error calculating weighted ratings: {str(e)}'
        }), 500