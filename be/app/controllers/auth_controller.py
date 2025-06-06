from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Register user using service
    user, error = AuthService.register_user(
        username=data['username'],
        email=data['email'],
        password=data['password']
    )
    
    if error:
        status_code = 409 if "already exists" in error else 500
        return jsonify({'message': error}), status_code
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    # Login user using service
    user, access_token, error = AuthService.login_user(
        username=data['username'],
        password=data['password']
    )
    
    if error:
        return jsonify({'message': error}), 401
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    
    # Get user profile using service
    user, preferences = AuthService.get_user_profile(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict(),
        'preferences': preferences.to_dict() if preferences else None
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # Update user profile using service
    user, error = AuthService.update_user_profile(user_id, data)
    
    if error:
        status_code = 404 if error == "User not found" else 409 if "already exists" in error else 500
        return jsonify({'message': error}), status_code
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': user.to_dict()
    }), 200