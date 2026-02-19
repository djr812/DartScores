"""Statistics routes"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Player, Match, Leg, Turn, Throw
from datetime import datetime, timedelta

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/player/<int:player_id>', methods=['GET'])
def get_player_stats(player_id):
    """Get statistics for a specific player"""
    player = Player.get_by_id(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Get time range from query parameters
    days = request.args.get('days', type=int, default=30)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all throws for this player within time range
    throws_query = db.session.query(Throw).join(Turn).join(Leg).join(Match).filter(
        Turn.player_id == player_id,
        Match.start_time >= since_date
    )
    
    total_throws = throws_query.count()
    
    if total_throws == 0:
        return jsonify({
            'player': player.to_dict(),
            'stats': {
                'total_throws': 0,
                'three_dart_average': 0,
                'checkout_percentage': 0,
                'double_hit_percentage': 0,
                'highest_finish': 0,
                'highest_scoring_visit': 0,
                'first_9_average': 0
            },
            'message': 'No throws recorded in the specified period'
        })
    
    # Calculate total points
    total_points = db.session.query(db.func.sum(Throw.points)).join(Turn).filter(
        Turn.player_id == player_id,
        Throw.is_bust == False
    ).scalar() or 0
    
    # Calculate 3-dart average
    three_dart_average = round((total_points / total_throws) * 3, 2)
    
    # Calculate checkout statistics
    checkout_attempts = throws_query.filter(
        Throw.multiplier == 2,  # Double attempts
        Throw.segment.between(1, 20)  # Not bull
    ).count() + throws_query.filter(
        Throw.segment == 25,
        Throw.multiplier == 2  # Double bull attempts
    ).count()
    
    checkout_success = throws_query.filter(
        Throw.is_checkout == True
    ).count()
    
    checkout_percentage = round((checkout_success / checkout_attempts * 100), 2) if checkout_attempts > 0 else 0
    
    # Calculate double hit percentage
    double_attempts = throws_query.filter(Throw.multiplier == 2).count()
    double_hits = throws_query.filter(
        Throw.multiplier == 2,
        Throw.segment > 0  # Not a miss
    ).count()
    
    double_hit_percentage = round((double_hits / double_attempts * 100), 2) if double_attempts > 0 else 0
    
    # Get highest finish
    highest_finish_query = db.session.query(
        Turn.remaining_score + Turn.score
    ).join(Leg).join(Match).filter(
        Turn.player_id == player_id,
        Turn.is_checkout == True,
        Match.start_time >= since_date
    ).order_by(
        (Turn.remaining_score + Turn.score).desc()
    ).first()
    
    highest_finish = highest_finish_query[0] if highest_finish_query else 0
    
    # Get highest scoring visit (3-dart turn)
    highest_scoring_visit_query = db.session.query(
        db.func.sum(Throw.points)
    ).join(Turn).filter(
        Turn.player_id == player_id,
        Match.start_time >= since_date
    ).group_by(
        Turn.id
    ).order_by(
        db.func.sum(Throw.points).desc()
    ).first()
    
    highest_scoring_visit = highest_scoring_visit_query[0] if highest_scoring_visit_query else 0
    
    # Calculate first 9 average (first 9 darts of a leg)
    # This is more complex - we need to get the first 3 turns for each leg
    first_9_scores = []
    legs = Leg.query.join(Match).filter(
        Match.start_time >= since_date
    ).all()
    
    for leg in legs:
        # Get first 3 turns for this player in this leg
        first_turns = Turn.query.filter(
            Turn.leg_id == leg.id,
            Turn.player_id == player_id
        ).order_by(Turn.turn_number).limit(3).all()
        
        if len(first_turns) >= 3:
            # Calculate total score for first 9 darts
            first_9_total = sum(turn.score for turn in first_turns)
            first_9_scores.append(first_9_total)
    
    first_9_average = round(sum(first_9_scores) / len(first_9_scores), 2) if first_9_scores else 0
    
    return jsonify({
        'player': player.to_dict(),
        'stats': {
            'total_throws': total_throws,
            'three_dart_average': three_dart_average,
            'checkout_percentage': checkout_percentage,
            'double_hit_percentage': double_hit_percentage,
            'highest_finish': highest_finish,
            'highest_scoring_visit': highest_scoring_visit,
            'first_9_average': first_9_average,
            'time_period_days': days
        }
    })


@stats_bp.route('/match/<int:match_id>', methods=['GET'])
def get_match_stats(match_id):
    """Get statistics for a specific match"""
    match = Match.get_by_id(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    # Get all legs for this match
    legs = Leg.query.filter_by(match_id=match_id).all()
    
    # Get player statistics for this match
    player_stats = {}
    for player_match in match.player_matches:
        player = player_match.player
        player_id = player.id
        
        # Get all throws for this player in this match
        throws = db.session.query(Throw).join(Turn).join(Leg).filter(
            Leg.match_id == match_id,
            Turn.player_id == player_id
        ).all()
        
        total_throws = len(throws)
        total_points = sum(throw.points for throw in throws if not throw.is_bust)
        
        # Calculate averages
        three_dart_average = round((total_points / total_throws) * 3, 2) if total_throws > 0 else 0
        
        # Count checkouts
        checkout_attempts = sum(1 for throw in throws if throw.multiplier == 2)
        checkout_success = sum(1 for throw in throws if throw.is_checkout)
        checkout_percentage = round((checkout_success / checkout_attempts * 100), 2) if checkout_attempts > 0 else 0
        
        player_stats[player_id] = {
            'player': player.to_dict(),
            'total_throws': total_throws,
            'total_points': total_points,
            'three_dart_average': three_dart_average,
            'checkout_percentage': checkout_percentage,
            'checkout_attempts': checkout_attempts,
            'checkout_success': checkout_success
        }
    
    return jsonify({
        'match': match.to_dict(),
        'legs_count': len(legs),
        'player_stats': player_stats
    })


@stats_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard for all players"""
    # Get time range from query parameters
    days = request.args.get('days', type=int, default=30)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all active players
    players = Player.get_all_active()
    
    leaderboard = []
    
    for player in players:
        # Get throws for this player within time range
        throws_query = db.session.query(Throw).join(Turn).join(Leg).join(Match).filter(
            Turn.player_id == player.id,
            Match.start_time >= since_date
        )
        
        total_throws = throws_query.count()
        
        if total_throws == 0:
            continue
        
        # Calculate total points
        total_points = db.session.query(db.func.sum(Throw.points)).join(Turn).filter(
            Turn.player_id == player.id,
            Throw.is_bust == False,
            Match.start_time >= since_date
        ).scalar() or 0
        
        # Calculate 3-dart average
        three_dart_average = round((total_points / total_throws) * 3, 2)
        
        # Count legs won
        legs_won = Leg.query.join(Match).filter(
            Leg.winning_player_id == player.id,
            Match.start_time >= since_date
        ).count()
        
        leaderboard.append({
            'player': player.to_dict(),
            'three_dart_average': three_dart_average,
            'total_throws': total_throws,
            'legs_won': legs_won,
            'matches_played': len(player.matches)
        })
    
    # Sort by 3-dart average (descending)
    leaderboard.sort(key=lambda x: x['three_dart_average'], reverse=True)
    
    return jsonify({
        'leaderboard': leaderboard,
        'time_period_days': days
    })