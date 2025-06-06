from app.models.db import db
from datetime import datetime
import json

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    favorite_genres = db.Column(db.Text, nullable=True)  # Stored as string (comma-separated)
    favorite_actors = db.Column(db.Text, nullable=True)  # Stored as string (comma-separated)
    favorite_directors = db.Column(db.Text, nullable=True)  # Stored as string (comma-separated)
    preferred_languages = db.Column(db.Text, nullable=True)  # Stored as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='preferences')
    
    def get_favorite_genres(self):
        if not self.favorite_genres:
            return ""
        return self.favorite_genres
    
    def get_favorite_actors(self):
        if not self.favorite_actors:
            return ""
        return self.favorite_actors
    
    def get_favorite_directors(self):
        if not self.favorite_directors:
            return ""
        return self.favorite_directors
    
    def get_preferred_languages(self):
        if not self.preferred_languages:
            return []
        try:
            return json.loads(self.preferred_languages)
        except json.JSONDecodeError:
            return []
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'favorite_genres': self.get_favorite_genres(),
            'favorite_actors': self.get_favorite_actors(),
            'favorite_directors': self.get_favorite_directors(),
            'preferred_languages': self.get_preferred_languages(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }