from app.models.db import db
from datetime import datetime

class Crew(db.Model):
    __tablename__ = 'crews'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    job = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.Integer, nullable=True)  # 0: Not specified, 1: Female, 2: Male
    profile_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'department': self.department,
            'job': self.job,
            'gender': self.gender,
            'profile_path': self.profile_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }