# check_current_games.py
"""Check what games exist in the database"""
from app import create_app, db
from app.models import Match, Leg, Player

app = create_app()
with app.app_context():
    print("Current Games in Database")
    print("=" * 50)
    
    # Get all matches
    matches = Match.query.all()
    print(f"Total matches: {len(matches)}")
    
    for match in matches:
        print(f"\nMatch {match.id}:")
        print(f"  Game type: {match.game_type}")
        print(f"  Status: {match.status}")
        print(f"  Created: {match.created_at}")
        
        # Get players in this match
        player_names = [pm.player.name for pm in match.player_matches]
        print(f"  Players: {', '.join(player_names)}")
        
        # Get legs for this match
        legs = Leg.query.filter_by(match_id=match.id).all()
        print(f"  Legs: {len(legs)}")
        for leg in legs:
            print(f"    Leg {leg.id}: #{leg.leg_number}, Status: {leg.status}")
    
    print("\n" + "=" * 50)
    print("Active matches (status='active'):")
    active_matches = Match.query.filter_by(status='active').all()
    for match in active_matches:
        print(f"  Match {match.id} - {match.game_type}")