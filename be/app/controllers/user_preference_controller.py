from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.user_preference_service import UserPreferenceService

user_preference_bp = Blueprint('user_preference', __name__)

@user_preference_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_preferences():
    """
    Get the preferences of the authenticated user.
    
    Authentication:
        Requires JWT Bearer token in the Authorization header
    
    Returns:
        JSON response with user preferences
    """
    # Get user ID from JWT
    user_id = int(get_jwt_identity())
    
    # Get user preferences using service
    preferences = UserPreferenceService.get_user_preferences(user_id)
    
    if not preferences:
        return jsonify({
            'message': 'User preferences not found',
            'preferences': None
        }), 404
    
    return jsonify({
        'message': 'User preferences retrieved successfully',
        'preferences': preferences.to_dict()
    }), 200

@user_preference_bp.route('/', methods=['POST'])
@jwt_required()
def create_user_preferences():
    """
    Create preferences for the authenticated user.
    
    Authentication:
        Requires JWT Bearer token in the Authorization header
    
    Request Body:
        {
            "favorite_genres": "Action, Adventure, Sci-Fi",
            "favorite_actors": "Tom Hanks, Leonardo DiCaprio",
            "favorite_directors": "Christopher Nolan, Steven Spielberg",
            "preferred_languages": ["en", "fr", "es"] (optional)
        }
    
    Returns:
        JSON response with created user preferences
    """
    # Get user ID from JWT
    user_id = int(get_jwt_identity())
    
    # Get data from request
    data = request.get_json()
    
    if not data:
        return jsonify({
            'message': 'No data provided'
        }), 400
    
    # Create user preferences using service
    preferences, error = UserPreferenceService.create_user_preferences(user_id, data)
    
    if error:
        status_code = 409 if "already exist" in error else 500
        return jsonify({
            'message': error
        }), status_code
    
    return jsonify({
        'message': 'User preferences created successfully',
        'preferences': preferences.to_dict()
    }), 201

@user_preference_bp.route('/check/', methods=['GET'])
@jwt_required()
def check_user_preferences():
    """
    Check if preferences exist for the authenticated user.
    
    Authentication:
        Requires JWT Bearer token in the Authorization header
    
    Returns:
        JSON response indicating if user preferences exist
    """
    # Get user ID from JWT
    user_id = int(get_jwt_identity())
    
    # Check if user preferences exist
    preferences = UserPreferenceService.get_user_preferences(user_id)
    
    return jsonify({
        'exists': preferences is not None,
        'preferences': preferences.to_dict() if preferences else None
    }), 200

@user_preference_bp.route('/save/', methods=['POST'])
@jwt_required()
def save_user_preferences():
    """
    Save preferences for the authenticated user.
    This endpoint will create new preferences if they don't exist,
    or update existing preferences if they do.
    
    Authentication:
        Requires JWT Bearer token in the Authorization header
    
    Request Body:
        {
            "favorite_genres": "Action, Adventure, Sci-Fi",
            "favorite_actors": "Tom Hanks, Leonardo DiCaprio",
            "favorite_directors": "Christopher Nolan, Steven Spielberg",
            "preferred_languages": ["en", "fr", "es"] (optional)
        }
    
    Returns:
        JSON response with saved user preferences
    """
    # Get user ID from JWT
    user_id = int(get_jwt_identity())
    
    # Get data from request
    data = request.get_json()
    
    if not data:
        return jsonify({
            'message': 'No data provided'
        }), 400
    
    # Check if user preferences exist
    existing_preferences = UserPreferenceService.get_user_preferences(user_id)
    
    if existing_preferences:
        # Update existing preferences
        preferences, error = UserPreferenceService.update_user_preferences(user_id, data)
        success_message = 'User preferences updated successfully'
    else:
        # Create new preferences
        preferences, error = UserPreferenceService.create_user_preferences(user_id, data)
        success_message = 'User preferences created successfully'
    
    if error:
        status_code = 404 if "not found" in error else 500
        if "already exist" in error:
            status_code = 409
        return jsonify({
            'message': error
        }), status_code
    
    return jsonify({
        'message': success_message,
        'preferences': preferences.to_dict()
    }), 200

@user_preference_bp.route('/update/', methods=['POST'])
@jwt_required()
def update_user_preferences():
    """
    Update preferences for the authenticated user.
    
    Authentication:
        Requires JWT Bearer token in the Authorization header
    
    Request Body:
        {
            "favorite_genres": "Action, Adventure, Sci-Fi",
            "favorite_actors": "Tom Hanks, Leonardo DiCaprio",
            "favorite_directors": "Christopher Nolan, Steven Spielberg",
            "preferred_languages": ["en", "fr", "es"] (optional)
        }
    
    Returns:
        JSON response with updated user preferences
    """
    # Get user ID from JWT
    user_id = int(get_jwt_identity())
    
    # Get data from request
    data = request.get_json()
    
    if not data:
        return jsonify({
            'message': 'No data provided'
        }), 400
    
    # Update user preferences using service
    preferences, error = UserPreferenceService.update_user_preferences(user_id, data)
    
    if error:
        status_code = 404 if "not found" in error else 500
        return jsonify({
            'message': error
        }), status_code
    
    return jsonify({
        'message': 'User preferences updated successfully',
        'preferences': preferences.to_dict()
    }), 200