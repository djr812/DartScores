"""Models package"""
from app import db

# Import all models here for easy access
from app.models.player import Player
from app.models.match import Match, PlayerMatch
from app.models.leg import Leg
from app.models.turn import Turn
from app.models.throw import Throw

__all__ = ['Player', 'Match', 'PlayerMatch', 'Leg', 'Turn', 'Throw']