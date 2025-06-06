from app.models.db import db
from app.models.user import User
from app.models.user_preference import UserPreference
from flask_jwt_extended import create_access_token
import json
from datetime import timedelta

class AuthService:
    @staticmethod
    def register_user(username, email, password):
        """
        Register a new user with the given credentials.
        
        Args:
            username (str): The username for the new user
            email (str): The email for the new user
            password (str): The password for the new user
            
        Returns:
            tuple: (user, error_message)
                If successful, returns (user, None)
                If error, returns (None, error_message)
        """
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        
        if User.query.filter_by(email=email).first():
            return None, "Email already exists"
        
        try:
            # Create new user
            new_user = User(
                username=username,
                email=email,
                password=password
            )
            db.session.add(new_user)
            db.session.commit()
            
        
            return new_user, None
            
        except Exception as e:
            db.session.rollback()
            return None, f"Error creating user: {str(e)}"
    
    @staticmethod
    def login_user(username, password):
        """
        Authenticate a user with the given credentials.
        
        Args:
            username (str): The username of the user
            password (str): The password of the user
            
        Returns:
            tuple: (user, access_token, error_message)
                If successful, returns (user, access_token, None)
                If error, returns (None, None, error_message)
        """
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            return None, None, "Invalid username or password"
        
        # Generate access token
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=1)
        )
        
        return user, access_token, None
    
    @staticmethod
    def get_user_profile(user_id):
        """
        Get the profile of a user.
        
        Args:
            user_id (int): The ID of the user
            
        Returns:
            tuple: (user, preferences)
                If successful, returns (user, preferences)
                If user not found, returns (None, None)
        """
        user = User.query.get(user_id)
        
        if not user:
            return None, None
        
        # Get user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        return user, preferences
    
    @staticmethod
    def update_user_profile(user_id, data):
        """
        Update the profile of a user.
        
        Args:
            user_id (int): The ID of the user
            data (dict): The data to update
            
        Returns:
            tuple: (user, error_message)
                If successful, returns (user, None)
                If error, returns (None, error_message)
        """
        user = User.query.get(user_id)
        
        if not user:
            return None, "User not found"
        
        try:
            # Update user information
            if data.get('username') and data['username'] != user.username:
                if User.query.filter_by(username=data['username']).first():
                    return None, "Username already exists"
                user.username = data['username']
            
            if data.get('email') and data['email'] != user.email:
                if User.query.filter_by(email=data['email']).first():
                    return None, "Email already exists"
                user.email = data['email']
            
            if data.get('password'):
                user.set_password(data['password'])
            
            db.session.commit()
            
            return user, None
            
        except Exception as e:
            db.session.rollback()
            return None, f"Error updating profile: {str(e)}"