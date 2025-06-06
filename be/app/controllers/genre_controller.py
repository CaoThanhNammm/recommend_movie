from flask import Blueprint, request, jsonify
from app.services.genre_service import GenreService

genre_bp = Blueprint('genre', __name__)


@genre_bp.route('/', methods=['GET'])
def get_genres():
    """Get all genres."""
    genres = GenreService.get_all_genres()
    return jsonify([genre.to_dict() for genre in genres]), 200


    """Get a genre by ID."""
    genre = GenreService.get_genre_by_id(genre_id)
    
    if not genre:
        return jsonify({'message': 'Genre not found'}), 404
    
    return jsonify(genre.to_dict()), 200

@genre_bp.route('/', methods=['POST'])
def create_genre():
    """Create a new genre."""
    data = request.get_json()
    
    # Validate input
    if not data or 'name' not in data:
        return jsonify({'message': 'Name is required'}), 400
    
    # Create genre
    genre, message = GenreService.create_genre(data['name'])
    
    if not genre:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'genre': genre.to_dict()
    }), 201


    """Import genres from a CSV file."""
    data = request.get_json()
    
    # Validate input
    if not data or 'csv_path' not in data:
        return jsonify({'message': 'CSV path is required'}), 400
    
    # Import genres
    count, message = GenreService.import_genres_from_csv(data['csv_path'])
    
    return jsonify({
        'message': message,
        'count': count
    }), 200 if count > 0 else 400