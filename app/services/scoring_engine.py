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
        """Process a single dart throw - COMPLETE FIXED VERSION"""
        from app.models import Turn, Throw
        
        print(f"=== PROCESS_THROW START ===")
        print(f"Leg: {leg_id}, Player: {player_id}, Dart: {dart_number}, {multiplier}x{segment}")
        
        # Validate inputs
        if dart_number not in [1, 2, 3]:
            raise ValueError(f"Invalid dart number: {dart_number}. Must be 1, 2, or 3")
        
        if segment not in list(range(0, 21)) + [25]:
            raise ValueError(f"Invalid segment: {segment}. Must be 0-20 or 25")
        
        if multiplier not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid multiplier: {multiplier}. Must be 0-3")
        
        # Get or create current turn
        turn = Turn.get_last_turn_for_leg(leg_id)
        
        print(f"Current turn: {turn.id if turn else 'None'}")
        if turn:
            print(f"  Player: {turn.player_id}, Darts thrown: {turn.darts_thrown}, Score: {turn.score}")
        
        # Check if we need a new turn
        need_new_turn = False
        if not turn:
            print("No current turn - creating new one")
            need_new_turn = True
        elif turn.darts_thrown >= 3:
            print(f"Turn complete ({turn.darts_thrown} darts) - creating new one")
            need_new_turn = True
        elif turn.player_id != player_id:
            print(f"Wrong player (turn:{turn.player_id}, request:{player_id}) - creating new one")
            need_new_turn = True
        
        if need_new_turn:
            # Get next turn number
            turn_number = Turn.get_next_turn_number(leg_id)
            print(f"New turn number: {turn_number}")
            
            # Calculate player's current score
            player_current_score = 501  # Start with 501
            
            # Subtract all NON-BUSTED turns for this player
            player_turns = Turn.query.filter_by(
                leg_id=leg_id,
                player_id=player_id,
                is_bust=False  # ONLY count non-busted turns!
            ).all()
            
            print(f"Found {len(player_turns)} non-busted turns for player {player_id}")
            for player_turn in player_turns:
                print(f"  Turn {player_turn.turn_number}: {player_turn.score} points")
                player_current_score -= player_turn.score
            
            print(f"Player {player_id} current score: {player_current_score}")
            
            # Create new turn - EXPLICITLY set all fields
            turn = Turn(
                leg_id=leg_id,
                player_id=player_id,
                turn_number=turn_number,
                remaining_score=player_current_score,
                score=0,
                darts_thrown=0,
                is_bust=False,
                is_checkout=False
            )
            db.session.add(turn)
            db.session.flush()  # Get ID without committing
            print(f"Created new turn ID: {turn.id}")
        
        # CRITICAL: Check for duplicate dart number in this turn
        existing_throw = Throw.query.filter_by(
            turn_id=turn.id,
            dart_number=dart_number
        ).first()
        
        if existing_throw:
            print(f"ERROR: Dart {dart_number} already exists in turn {turn.id}!")
            print(f"Existing throw: ID {existing_throw.id}, {existing_throw.multiplier}x{existing_throw.segment}")
            raise ValueError(f"Dart {dart_number} already recorded for this turn")
        
        # Ensure darts_thrown is valid
        if turn.darts_thrown is None:
            print("WARNING: turn.darts_thrown was None, setting to 0")
            turn.darts_thrown = 0
        
        # Check if this dart number makes sense
        expected_dart_number = turn.darts_thrown + 1
        if dart_number != expected_dart_number:
            print(f"WARNING: Dart number mismatch. Expected: {expected_dart_number}, Got: {dart_number}")
            # But continue anyway - frontend might have wrong state
        
        # Calculate points
        points = cls.calculate_points(segment, multiplier)
        print(f"Points: {points} ({multiplier}x{segment})")
        
        # Check for bust
        new_remaining = turn.remaining_score - points
        is_bust = new_remaining < 2 or (new_remaining == 0 and multiplier != 2 and segment != 25)
        
        print(f"Bust check: {turn.remaining_score} - {points} = {new_remaining}, is_bust: {is_bust}")
        
        # Create throw
        throw = Throw(
            turn_id=turn.id,
            dart_number=dart_number,
            segment=segment,
            multiplier=multiplier,
            points=points,
            is_bust=is_bust,
            is_checkout=False
        )
        db.session.add(throw)
        
        if is_bust:
            print("BUST DETECTED!")
            throw.is_bust = True
            turn.is_bust = True
            turn.score = 0  # Bust means 0 points for the entire turn
            # DO NOT update remaining_score - it stays the same!
            print(f"Bust: Turn score set to 0, remaining stays at {turn.remaining_score}")
        else:
            # Valid throw
            turn.score += points
            turn.remaining_score = new_remaining
            
            print(f"Valid throw: Turn score now {turn.score}, remaining {turn.remaining_score}")
            
            # Check for checkout (must finish on double)
            if new_remaining == 0:
                print("CHECKOUT ATTEMPT!")
                if segment == 25:
                    is_checkout = multiplier == 2  # Double bull
                else:
                    is_checkout = multiplier == 2  # Double
                
                if is_checkout:
                    print("SUCCESSFUL CHECKOUT!")
                    throw.is_checkout = True
                    turn.is_checkout = True
                else:
                    print("INVALID CHECKOUT - not a double!")
                    # This should actually be a bust!
                    throw.is_bust = True
                    turn.is_bust = True
                    turn.score = 0  # Revert score
                    turn.remaining_score += points  # Add points back
                    is_bust = True
                    print(f"Invalid checkout - treated as bust. Score reverted to {turn.score}")
        
        # Increment darts thrown
        turn.darts_thrown += 1
        print(f"Darts thrown updated to: {turn.darts_thrown}")
        
        # Commit everything
        db.session.add(turn)
        db.session.commit()
        
        print(f"=== PROCESS_THROW END ===")
        print(f"Turn ID: {turn.id}, Throw ID: {throw.id}")
        print(f"Final state - Score: {turn.score}, Remaining: {turn.remaining_score}, Bust: {turn.is_bust}")
        
        # Return response
        return {
            'game_completed': turn.is_checkout,  # Game completed on checkout
            'is_bust': is_bust,
            'is_checkout': throw.is_checkout,
            'remaining_score': turn.remaining_score,
            'throw': throw.to_dict(),
            'turn': turn.to_dict()
        }

    @classmethod
    def get_player_current_score(cls, leg_id: int, player_id: int) -> int:
        """Get a player's current score in a leg"""
        # Start with 501
        total_score = 501
        
        # Subtract all non-busted turns for this player
        turns = Turn.query.filter_by(
            leg_id=leg_id,
            player_id=player_id,
            is_bust=False
        ).all()
        
        for turn in turns:
            total_score -= turn.score
        
        return total_score
    
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