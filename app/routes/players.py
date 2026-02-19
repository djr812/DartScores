"""Player routes"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Player

players_bp = Blueprint('players', __name__)


@players_bp.route('/', methods=['GET'])
def get_players():
    """Get all active players"""
    players = Player.get_all_active()
    return jsonify({
        'players': [player.to_dict() for player in players]
    })


@players_bp.route('/', methods=['POST'])
def create_player():
    """Create a new player"""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    name = data['name'].strip()
    nickname = data.get('nickname', '').strip() or None
    
    # Check if player already exists
    existing = Player.query.filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Player with this name already exists'}), 409
    
    try:
        player = Player.create(name=name, nickname=nickname)
        return jsonify({
            'message': 'Player created successfully',
            'player': player.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@players_bp.route('/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """Get a specific player"""
    player = Player.get_by_id(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    return jsonify({'player': player.to_dict()})


@players_bp.route('/<int:player_id>', methods=['PUT'])
def update_player(player_id):
    """Update a player"""
    player = Player.get_by_id(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        new_name = data['name'].strip()
        if new_name != player.name:
            # Check if new name already exists
            existing = Player.query.filter_by(name=new_name).first()
            if existing and existing.id != player_id:
                return jsonify({'error': 'Player with this name already exists'}), 409
            player.name = new_name
    
    if 'nickname' in data:
        player.nickname = data['nickname'].strip() or None
    
    if 'is_active' in data:
        player.is_active = bool(data['is_active'])
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Player updated successfully',
            'player': player.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@players_bp.route('/<int:player_id>', methods=['DELETE'])
def delete_player(player_id):
    """Delete a player (soft delete)"""
    player = Player.get_by_id(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    player.is_active = False
    
    try:
        db.session.commit()
        return jsonify({'message': 'Player deactivated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500