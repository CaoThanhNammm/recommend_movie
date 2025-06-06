from app.models.db import db
from datetime import datetime

class UserWatchHistory(db.Model):
    __tablename__ = 'user_watch_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='watch_history')
    movie = db.relationship('Movie', back_populates='watch_history')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'watched_at': self.watched_at.isoformat() if self.watched_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }