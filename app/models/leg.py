# app/models/leg.py - Updated
"""Leg model"""
from datetime import datetime
from app import db


class Leg(db.Model):
    """Leg model for darts scoring system"""
    __tablename__ = 'legs'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    leg_number = db.Column(db.Integer, nullable=False)
    starting_player_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    winning_player_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.Enum('active', 'completed'), default='active')  # Use strings directly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    match = db.relationship('Match', back_populates='legs')
    starting_player = db.relationship('Player', foreign_keys=[starting_player_id])
    winning_player = db.relationship('Player', foreign_keys=[winning_player_id])
    turns = db.relationship('Turn', back_populates='leg', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Leg {self.leg_number} of Match {self.match_id}>'
    
    def to_dict(self):
        """Convert leg to dictionary"""
        return {
            'id': self.id,
            'match_id': self.match_id,
            'leg_number': self.leg_number,
            'starting_player_id': self.starting_player_id,
            'winning_player_id': self.winning_player_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'turns': [turn.to_dict() for turn in self.turns]
        }
    
    def complete(self, winning_player_id):
        """Mark leg as completed"""
        self.status = 'completed'
        self.winning_player_id = winning_player_id
        self.end_time = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_for_match(cls, match_id, leg_number, starting_player_id):
        """Create a new leg for a match"""
        leg = cls(
            match_id=match_id,
            leg_number=leg_number,
            starting_player_id=starting_player_id
        )
        db.session.add(leg)
        db.session.commit()
        return leg
    
    @classmethod
    def get_active_legs_for_match(cls, match_id):
        """Get active legs for a match"""
        return cls.query.filter_by(
            match_id=match_id,
            status='active'
        ).all()
    
    @classmethod
    def get_by_id(cls, leg_id):
        """Get leg by ID"""
        return cls.query.get(leg_id)
    