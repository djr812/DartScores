"""Match routes"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Match, Leg, Player
from app.services.scoring_engine import ScoringEngine

matches_bp = Blueprint('matches', __name__)


@matches_bp.route('/', methods=['GET'])
def get_matches():
    """Get all matches"""
    status = request.args.get('status', 'active')
    
    if status == 'active':
        matches = Match.get_active_matches()
    else:
        matches = Match.query.all()
    
    return jsonify({
        'matches': [match.to_dict() for match in matches]
    })


@matches_bp.route('/', methods=['POST'])
def create_match():
    """Create a new match"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'player_ids' not in data:
        return jsonify({'error': 'player_ids is required'}), 400
    
    player_ids = data['player_ids']
    game_type = data.get('game_type', '501')
    
    # Validate players exist
    for player_id in player_ids:
        player = Player.get_by_id(player_id)
        if not player:
            return jsonify({'error': f'Player {player_id} not found'}), 404
    
    # Validate game type
    if game_type not in ['501', 'cricket']:
        return jsonify({'error': 'Invalid game type. Must be 501 or cricket'}), 400
    
    try:
        if game_type == '501':
            match = Match.create_501_match(player_ids)
        else:
            # For now, only 501 is implemented
            return jsonify({'error': 'Cricket not yet implemented'}), 501
        
        # Start first leg with first player
        leg_result = ScoringEngine.start_new_leg(match.id, player_ids[0])
        
        return jsonify({
            'message': 'Match created successfully',
            'match': match.to_dict(),
            'leg': leg_result
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Log the full error for debugging
        print(f"Error creating match: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to create match: {str(e)}'}), 500

@matches_bp.route('/<int:match_id>', methods=['GET'])
def get_match(match_id):
    """Get a specific match"""
    match = Match.get_by_id(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    return jsonify({'match': match.to_dict()})


@matches_bp.route('/<int:match_id>/legs', methods=['GET'])
def get_match_legs(match_id):
    """Get all legs for a match"""
    match = Match.get_by_id(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    legs = Leg.query.filter_by(match_id=match_id).order_by(Leg.leg_number).all()
    
    return jsonify({
        'legs': [leg.to_dict() for leg in legs]
    })


@matches_bp.route('/<int:match_id>/legs/current', methods=['GET'])
def get_current_leg(match_id):
    """Get current active leg for a match"""
    match = Match.get_by_id(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    active_legs = Leg.get_active_legs_for_match(match_id)
    
    if not active_legs:
        return jsonify({'error': 'No active leg found'}), 404
    
    # Get the most recent active leg
    current_leg = active_legs[-1]
    
    # Get game state
    game_state = ScoringEngine.get_current_game_state(current_leg.id)
    
    return jsonify(game_state)


@matches_bp.route('/<int:match_id>/legs/<int:leg_id>/throw', methods=['POST'])
def record_throw(match_id, leg_id):
    """Record a dart throw"""
    data = request.get_json()
    
    print(f"=== THROW REQUEST ===")
    print(f"Match: {match_id}, Leg: {leg_id}")
    print(f"Data: {data}")
    
    # Validate required fields
    required_fields = ['player_id', 'segment', 'multiplier', 'dart_number']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        error_msg = f'Missing required fields: {", ".join(missing_fields)}'
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    player_id = data['player_id']
    segment = data['segment']
    multiplier = data['multiplier']
    dart_number = data['dart_number']
    
    # Validate dart_number specifically
    if not isinstance(dart_number, int):
        error_msg = f'Dart number must be an integer, got {type(dart_number)}: {dart_number}'
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    # Validate values
    if segment not in list(range(0, 21)) + [25]:
        error_msg = f'Segment must be 0-20 or 25, got {segment}'
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    if multiplier not in [0, 1, 2, 3]:
        error_msg = f'Multiplier must be 0-3, got {multiplier}'
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    if dart_number not in [1, 2, 3]:
        error_msg = f'Dart number must be 1-3, got {dart_number}'
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    # Verify leg exists and belongs to match
    leg = Leg.get_by_id(leg_id)
    if not leg:
        error_msg = f'Leg {leg_id} not found'
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 404
    
    if leg.match_id != match_id:
        error_msg = f'Leg {leg_id} does not belong to match {match_id}'
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    # Verify player is in the match
    match = Match.get_by_id(match_id)
    if not match:
        error_msg = f'Match {match_id} not found'
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 404
    
    player_in_match = any(pm.player_id == player_id for pm in match.player_matches)
    if not player_in_match:
        error_msg = f'Player {player_id} is not in match {match_id}'
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    try:
        print(f"Calling ScoringEngine.process_throw...")
        result = ScoringEngine.process_throw(
            leg_id=leg_id,
            player_id=player_id,
            segment=segment,
            multiplier=multiplier,
            dart_number=dart_number
        )
        
        print(f"Throw processed successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"ERROR in process_throw: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': f'Failed to process throw: {str(e)}'}), 500


@matches_bp.route('/<int:match_id>/legs/<int:leg_id>/next-player', methods=['POST'])
def next_player(match_id, leg_id):
    """Force move to next player (for busts or manual advancement)"""
    # Verify leg exists and belongs to match
    leg = Leg.get_by_id(leg_id)
    if not leg or leg.match_id != match_id:
        return jsonify({'error': 'Leg not found or does not belong to match'}), 404
    
    # Get current game state
    game_state = ScoringEngine.get_current_game_state(leg_id)
    
    # Get players in match
    match = Match.get_by_id(match_id)
    player_matches = match.player_matches
    player_ids = [pm.player_id for pm in sorted(player_matches, key=lambda x: x.player_order)]
    
    # Determine current player
    current_player_id = game_state['current_player_id']
    if not current_player_id:
        current_player_id = leg.starting_player_id
    
    # Find next player
    current_index = player_ids.index(current_player_id)
    next_index = (current_index + 1) % len(player_ids)
    next_player_id = player_ids[next_index]
    
    return jsonify({
        'current_player_id': current_player_id,
        'next_player_id': next_player_id,
        'message': f'Next player is {next_player_id}'
    })


@matches_bp.route('/<int:match_id>/complete', methods=['POST'])
def complete_match(match_id):
    """Mark a match as completed"""
    match = Match.get_by_id(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    match.complete()
    
    return jsonify({
        'message': 'Match completed successfully',
        'match': match.to_dict()
    })