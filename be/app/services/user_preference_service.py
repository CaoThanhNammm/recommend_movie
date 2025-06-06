from app.models.db import db
from app.models.user_preference import UserPreference
import json

class UserPreferenceService:
    @staticmethod
    def get_user_preferences(user_id):
        """
        Get the preferences of a user.
        
        Args:
            user_id (int): The ID of the user
            
        Returns:
            UserPreference: The user preferences object or None if not found
        """
        return UserPreference.query.filter_by(user_id=user_id).first()
    
    @staticmethod
    def create_user_preferences(user_id, data):
        """
        Create preferences for a user.
        
        Args:
            user_id (int): The ID of the user
            data (dict): The data to create
            
        Returns:
            tuple: (preferences, error_message)
                If successful, returns (preferences, None)
                If error, returns (None, error_message)
        """
        # Check if user preferences already exist
        existing_preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if existing_preferences:
            return None, "User preferences already exist. Use update instead."
        
        try:
            # Create new preferences
            user_preferences = UserPreference(user_id=user_id)
            
            # Set preferences
            if 'favorite_genres' in data:
                user_preferences.favorite_genres = data['favorite_genres']
            
            if 'favorite_actors' in data:
                user_preferences.favorite_actors = data['favorite_actors']
            
            if 'favorite_directors' in data:
                user_preferences.favorite_directors = data['favorite_directors']
            
            if 'preferred_languages' in data:
                user_preferences.preferred_languages = json.dumps(data['preferred_languages'])
            
            db.session.add(user_preferences)
            db.session.commit()
            
            return user_preferences, None
            
        except Exception as e:
            db.session.rollback()
            return None, f"Error creating preferences: {str(e)}"
    
    @staticmethod
    def update_user_preferences(user_id, data):
        """
        Update the preferences of a user.
        
        Args:
            user_id (int): The ID of the user
            data (dict): The data to update
            
        Returns:
            tuple: (preferences, error_message)
                If successful, returns (preferences, None)
                If error, returns (None, error_message)
        """
        # Get user preferences
        user_preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not user_preferences:
            # Create new preferences if they don't exist
            return UserPreferenceService.create_user_preferences(user_id, data)
        
        try:
            # Update preferences
            if 'favorite_genres' in data:
                user_preferences.favorite_genres = data['favorite_genres']
            
            if 'favorite_actors' in data:
                user_preferences.favorite_actors = data['favorite_actors']
            
            if 'favorite_directors' in data:
                user_preferences.favorite_directors = data['favorite_directors']
            
            if 'preferred_languages' in data:
                user_preferences.preferred_languages = json.dumps(data['preferred_languages'])
            
            db.session.commit()
            
            return user_preferences, None
            
        except Exception as e:
            db.session.rollback()
            return None, f"Error updating preferences: {str(e)}"