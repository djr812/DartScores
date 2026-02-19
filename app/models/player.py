"""Player model"""
from datetime import datetime
from app import db


class Player(db.Model):
    """Player model for darts scoring system"""
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    nickname = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    matches = db.relationship('PlayerMatch', back_populates='player', cascade='all, delete-orphan')
    turns = db.relationship('Turn', back_populates='player')
    
    def __repr__(self):
        return f'<Player {self.name}>'
    
    def to_dict(self):
        """Convert player to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'nickname': self.nickname,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create(cls, name, nickname=None):
        """Create a new player"""
        player = cls(name=name, nickname=nickname)
        db.session.add(player)
        db.session.commit()
        return player
    
    @classmethod
    def get_all_active(cls):
        """Get all active players"""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_by_id(cls, player_id):
        """Get player by ID"""
        return cls.query.get(player_id)