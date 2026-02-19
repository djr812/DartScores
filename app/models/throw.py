"""Throw model"""
from datetime import datetime
from app import db


class Throw(db.Model):
    """Throw model for darts scoring system"""
    __tablename__ = 'throws'
    
    id = db.Column(db.Integer, primary_key=True)
    turn_id = db.Column(db.Integer, db.ForeignKey('turns.id'), nullable=False)
    dart_number = db.Column(db.Integer, nullable=False)  # 1, 2, or 3
    segment = db.Column(db.Integer, nullable=False)  # 0-20 or 25 (bull)
    multiplier = db.Column(db.Integer, nullable=False)  # 0=miss, 1=single, 2=double, 3=treble
    points = db.Column(db.Integer, nullable=False)
    is_bust = db.Column(db.Boolean, default=False)
    is_checkout = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    turn = db.relationship('Turn', back_populates='throws')
    
    def __repr__(self):
        return f'<Throw {self.dart_number}: {self.multiplier}x{self.segment} = {self.points}>'
    
    def to_dict(self):
        """Convert throw to dictionary"""
        return {
            'id': self.id,
            'turn_id': self.turn_id,
            'dart_number': self.dart_number,
            'segment': self.segment,
            'multiplier': self.multiplier,
            'points': self.points,
            'is_bust': self.is_bust,
            'is_checkout': self.is_checkout,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_for_turn(cls, turn_id, dart_number, segment, multiplier):
        """Create a new throw for a turn"""
        # Calculate points
        if segment == 0:  # Miss
            points = 0
        elif segment == 25:  # Bull
            points = 25 if multiplier == 1 else 50  # Single bull = 25, Double bull = 50
        else:
            points = segment * multiplier
        
        throw = cls(
            turn_id=turn_id,
            dart_number=dart_number,
            segment=segment,
            multiplier=multiplier,
            points=points
        )
        db.session.add(throw)
        db.session.commit()
        return throw
    
    @classmethod
    def get_last_throw_for_turn(cls, turn_id):
        """Get the last throw for a turn"""
        return cls.query.filter_by(turn_id=turn_id).order_by(cls.dart_number.desc()).first()
    
    @classmethod
    def get_by_id(cls, throw_id):
        """Get throw by ID"""
        return cls.query.get(throw_id)