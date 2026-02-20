"""Turn model"""
from datetime import datetime
from app import db


class Turn(db.Model):
    """Turn model for darts scoring system"""
    __tablename__ = 'turns'
    
    id = db.Column(db.Integer, primary_key=True)
    leg_id = db.Column(db.Integer, db.ForeignKey('legs.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    turn_number = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, default=0)
    remaining_score = db.Column(db.Integer, nullable=False)
    darts_thrown = db.Column(db.Integer, default=0)
    is_bust = db.Column(db.Boolean, default=False)
    is_checkout = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leg = db.relationship('Leg', back_populates='turns')
    player = db.relationship('Player', back_populates='turns')
    throws = db.relationship('Throw', back_populates='turn', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure darts_thrown is initialized to 0 if not provided
        if self.darts_thrown is None:
            self.darts_thrown = 0
        if self.score is None:
            self.score = 0
        if self.is_bust is None:
            self.is_bust = False
        if self.is_checkout is None:
            self.is_checkout = False

    def __repr__(self):
        return f'<Turn {self.turn_number} by Player {self.player_id}>'
    
    def to_dict(self):
        """Convert turn to dictionary"""
        return {
            'id': self.id,
            'leg_id': self.leg_id,
            'player_id': self.player_id,
            'turn_number': self.turn_number,
            'score': self.score,
            'remaining_score': self.remaining_score,
            'darts_thrown': self.darts_thrown,
            'is_bust': self.is_bust,
            'is_checkout': self.is_checkout,
            'throws': [throw.to_dict() for throw in self.throws],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_for_leg(cls, leg_id, player_id, turn_number, remaining_score):
        """Create a new turn for a leg"""
        turn = cls(
            leg_id=leg_id,
            player_id=player_id,
            turn_number=turn_number,
            remaining_score=remaining_score
        )
        db.session.add(turn)
        db.session.commit()
        return turn
    
    @classmethod
    def get_last_turn_for_leg(cls, leg_id: int):
        """Get the last turn for a leg that's not complete (has < 3 darts)"""
        return cls.query.filter_by(
            leg_id=leg_id
        ).filter(
            cls.darts_thrown < 3
        ).order_by(cls.turn_number.desc()).first()
    
    @classmethod
    def get_by_id(cls, turn_id):
        """Get turn by ID"""
        return cls.query.get(turn_id)
    
    # In app/models/turn.py, add this method to the Turn class:
    @classmethod
    def get_next_turn_number(cls, leg_id: int) -> int:
        """Get the next turn number for a leg"""
        last_turn = cls.query.filter_by(leg_id=leg_id).order_by(cls.turn_number.desc()).first()
        if last_turn:
            return last_turn.turn_number + 1
        return 1

    # Also make sure you have this method (for getting the last turn):
    @classmethod
    def get_last_turn_for_leg(cls, leg_id: int):
        """Get the last turn for a leg that's not complete (has < 3 darts)"""
        return cls.query.filter_by(
            leg_id=leg_id
        ).filter(
            cls.darts_thrown < 3
        ).order_by(cls.turn_number.desc()).first()