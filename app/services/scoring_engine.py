"""Scoring engine for darts games"""
from typing import Tuple, Optional, Dict, Any
from enum import Enum
from app import db
from app.models import Match, Leg, Turn, Throw, Player


class DartMultiplier(Enum):
    """Dart multiplier types"""
    MISS = 0
    SINGLE = 1
    DOUBLE = 2
    TREBLE = 3


class ScoringEngine:
    """Scoring engine for 501 darts"""
    
    STARTING_SCORE_501 = 501
    
    @staticmethod
    def calculate_points(segment: int, multiplier: int) -> int:
        """Calculate points for a dart throw"""
        if segment == 0:  # Miss
            return 0
        elif segment == 25:  # Bull
            return 25 if multiplier == DartMultiplier.SINGLE.value else 50
        else:
            return segment * multiplier
    
    @staticmethod
    def is_valid_checkout(remaining_score: int, points: int, multiplier: int, segment: int) -> bool:
        """Check if a throw would result in a valid checkout"""
        if remaining_score == points:
            # Must finish on a double (or bullseye which counts as double)
            # For bullseye (segment 25), multiplier 2 is double bull (50 points)
            # For regular segments, multiplier 2 is double
            if segment == 25:
                return multiplier == 2  # Must be double bull
            else:
                return multiplier == 2  # Must be double
        return False
    
    @staticmethod
    def is_bust(remaining_score: int, points: int) -> bool:
        """Check if a throw would result in a bust"""
        # Bust conditions:
        # 1. Score goes below 2 (can't finish on 1)
        # 2. Score goes to 0 but not on a double
        # 3. Score goes negative
        new_score = remaining_score - points
        return new_score < 2 or (new_score == 0 and remaining_score != points)
    
    @classmethod
    def process_throw(
        cls,
        leg_id: int,
        player_id: int,
        segment: int,
        multiplier: int,
        dart_number: int
    ) -> Dict[str, Any]:
        """Process a single dart throw"""
        # Get or create current turn
        turn = Turn.get_last_turn_for_leg(leg_id)
        
        if not turn or turn.darts_thrown >= 3 or turn.player_id != player_id:
            # Start new turn
            if turn and turn.darts_thrown >= 3:
                turn_number = turn.turn_number + 1
            else:
                turn_number = 1
            
            # Get current remaining score from last turn or start at 501
            if turn:
                remaining_score = turn.remaining_score
            else:
                remaining_score = cls.STARTING_SCORE_501
            
            turn = Turn.create_for_leg(leg_id, player_id, turn_number, remaining_score)
        
        # Calculate points for this throw
        points = cls.calculate_points(segment, multiplier)
        
        # Check for bust
        is_bust = cls.is_bust(turn.remaining_score, points)
        
        # Check for checkout
        is_checkout = False
        if not is_bust:
            is_checkout = cls.is_valid_checkout(turn.remaining_score, points, multiplier, segment)
        
        # Create the throw
        throw = Throw.create_for_turn(turn.id, dart_number, segment, multiplier)
        
        # Update turn statistics
        turn.darts_thrown += 1
        
        if is_bust:
            # Bust - score doesn't count, reset to previous remaining score
            throw.is_bust = True
            turn.is_bust = True
            # For bust, we don't update the score
        elif is_checkout:
            # Checkout - game won!
            throw.is_checkout = True
            turn.is_checkout = True
            turn.score += points
            turn.remaining_score = 0
            
            # Complete the leg
            leg = Leg.get_by_id(leg_id)
            leg.complete(player_id)
        else:
            # Normal throw
            turn.score += points
            turn.remaining_score -= points
        
        # Update throw with bust/checkout flags
        db.session.add(throw)
        db.session.commit()
        
        # Prepare response
        response = {
            'throw': throw.to_dict(),
            'turn': turn.to_dict(),
            'is_bust': is_bust,
            'is_checkout': is_checkout,
            'remaining_score': turn.remaining_score,
            'game_completed': is_checkout
        }
        
        return response
    
    @classmethod
    def undo_last_throw(cls, leg_id: int) -> Optional[Dict[str, Any]]:
        """Undo the last throw in a leg"""
        # Get the last turn
        turn = Turn.get_last_turn_for_leg(leg_id)
        if not turn:
            return None
        
        # Get the last throw
        throw = Throw.get_last_throw_for_turn(turn.id)
        if not throw:
            return None
        
        # Store data before deletion
        throw_data = throw.to_dict()
        
        # Remove the throw
        db.session.delete(throw)
        
        # Update turn
        turn.darts_thrown -= 1
        
        if throw.is_bust:
            # Remove bust flag
            turn.is_bust = False
        elif throw.is_checkout:
            # Remove checkout flag and reset leg
            turn.is_checkout = False
            turn.score -= throw.points
            turn.remaining_score += throw.points
            
            # Reset leg completion
            leg = Leg.get_by_id(leg_id)
            leg.status = 'active'
            leg.winning_player_id = None
            leg.end_time = None
            db.session.add(leg)
        else:
            # Normal throw - subtract points
            turn.score -= throw.points
            turn.remaining_score += throw.points
        
        # If no throws left in turn, delete the turn
        if turn.darts_thrown == 0:
            db.session.delete(turn)
            db.session.commit()
            return {
                'throw_removed': throw_data,
                'turn_removed': True,
                'remaining_score': turn.remaining_score + throw.points if turn else cls.STARTING_SCORE_501
            }
        
        db.session.commit()
        
        return {
            'throw_removed': throw_data,
            'turn_removed': False,
            'remaining_score': turn.remaining_score,
            'turn': turn.to_dict()
        }
    
    @classmethod
    def start_new_leg(cls, match_id: int, starting_player_id: int) -> Dict[str, Any]:
        """Start a new leg in a match"""
        # Get match
        match = Match.get_by_id(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")
        
        # Determine leg number
        existing_legs = Leg.query.filter_by(match_id=match_id).count()
        leg_number = existing_legs + 1
        
        # Create leg
        leg = Leg.create_for_match(match_id, leg_number, starting_player_id)
        
        return {
            'leg': leg.to_dict(),
            'match_id': match_id,
            'leg_number': leg_number,
            'starting_player_id': starting_player_id
        }
    
    @classmethod
    def get_current_game_state(cls, leg_id: int) -> Dict[str, Any]:
        """Get current game state for a leg"""
        leg = Leg.get_by_id(leg_id)
        if not leg:
            raise ValueError(f"Leg {leg_id} not found")
        
        # Get all turns for this leg
        turns = Turn.query.filter_by(leg_id=leg_id).order_by(Turn.turn_number).all()
        
        # Get players in the match
        match = Match.get_by_id(leg.match_id)
        players = [pm.player.to_dict() for pm in match.player_matches]
        
        # Calculate current player
        current_player_id = None
        current_turn = None
        if turns:
            last_turn = turns[-1]
            if last_turn.darts_thrown < 3 and not last_turn.is_bust and not last_turn.is_checkout:
                current_player_id = last_turn.player_id
                current_turn = last_turn.to_dict()
            else:
                # Determine next player
                player_matches = match.player_matches
                player_ids = [pm.player_id for pm in sorted(player_matches, key=lambda x: x.player_order)]
                
                if last_turn:
                    current_index = player_ids.index(last_turn.player_id)
                    next_index = (current_index + 1) % len(player_ids)
                    current_player_id = player_ids[next_index]
        else:
            # First turn of the leg
            current_player_id = leg.starting_player_id
        
        return {
            'leg': leg.to_dict(),
            'match': match.to_dict(),
            'players': players,
            'current_player_id': current_player_id,
            'current_turn': current_turn,
            'turns': [turn.to_dict() for turn in turns],
            'game_type': match.game_type
        }