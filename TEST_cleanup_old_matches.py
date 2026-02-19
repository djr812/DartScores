# cleanup_old_matches.py
"""Clean up old matches to prevent confusion"""
from app import create_app, db
from app.models import Match, Leg, Turn, Throw, PlayerMatch
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print("Cleaning up old matches...")
    print("=" * 50)
    
    # Get all matches
    matches = Match.query.all()
    print(f"Total matches before cleanup: {len(matches)}")
    
    # Keep only the most recent match, delete others
    if len(matches) > 0:
        # Find the most recent match
        latest_match = max(matches, key=lambda m: m.id)
        print(f"Keeping match {latest_match.id} (created: {latest_match.created_at})")
        
        # Delete all other matches
        matches_to_delete = [m for m in matches if m.id != latest_match.id]
        
        for match in matches_to_delete:
            print(f"Deleting match {match.id}...")
            
            # Delete related records (cascade should handle most)
            db.session.delete(match)
        
        db.session.commit()
        print(f"Deleted {len(matches_to_delete)} old matches")
    
    # Verify cleanup
    matches = Match.query.all()
    print(f"\nTotal matches after cleanup: {len(matches)}")
    for match in matches:
        print(f"  Match {match.id}: {match.game_type}, created {match.created_at}")
    
    print("\n" + "=" * 50)
    print("Cleanup complete!")