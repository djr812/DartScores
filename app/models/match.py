# app/models/match.py - Fix the GameType enum
"""Match model"""
from datetime import datetime
from enum import Enum
from app import db


class GameType(Enum):
    """Game type enumeration"""
    GAME_501 = '501'
    CRICKET = 'cricket'
    
    # This makes the enum return the string value when accessed
    def __str__(self):
        return self.value


class MatchStatus(Enum):
    """Match status enumeration"""
    ACTIVE = 'active'
    COMPLETED = 'completed'
    ABANDONED = 'abandoned'
    
    def __str__(self):
        return self.value


class LegStatus(Enum):
    """Leg status enumeration"""
    ACTIVE = 'active'
    COMPLETED = 'completed'
    
    def __str__(self):
        return self.value


class Match(db.Model):
    """Match model for darts scoring system"""
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    game_type = db.Column(db.Enum('501', 'cricket'), nullable=False, default='501')  # Use strings directly
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.Enum('active', 'completed', 'abandoned'), default='active')  # Use strings directly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    legs = db.relationship('Leg', back_populates='match', cascade='all, delete-orphan')
    player_matches = db.relationship('PlayerMatch', back_populates='match', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Match {self.id} - {self.game_type}>'
    
    def to_dict(self):
        """Convert match to dictionary"""
        return {
            'id': self.id,
            'game_type': self.game_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'players': [pm.player.to_dict() for pm in self.player_matches],
            'legs': [leg.to_dict() for leg in self.legs],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def complete(self):
        """Mark match as completed"""
        self.status = 'completed'
        self.end_time = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_501_match(cls, player_ids):
        """Create a new 501 match with players"""
        match = cls(game_type='501')  # Use string directly
        db.session.add(match)
        
        # Add players to match
        for order, player_id in enumerate(player_ids, 1):
            player_match = PlayerMatch(player_id=player_id, match=match, player_order=order)
            db.session.add(player_match)
        
        db.session.commit()
        return match
    
    @classmethod
    def get_active_matches(cls):
        """Get all active matches"""
        return cls.query.filter_by(status='active').all()
    
    @classmethod
    def get_by_id(cls, match_id):
        """Get match by ID"""
        return cls.query.get(match_id)


class PlayerMatch(db.Model):
    """Many-to-many relationship between players and matches"""
    __tablename__ = 'player_matches'
    
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), primary_key=True)
    player_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', back_populates='matches')
    match = db.relationship('Match', back_populates='player_matches')
    
    def __repr__(self):
        return f'<PlayerMatch player:{self.player_id} match:{self.match_id}>'