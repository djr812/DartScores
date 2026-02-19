# debug_api.py
"""Debug API calls"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_api_endpoints():
    print("Testing API endpoints...")
    print("=" * 50)
    
    # Test 1: Check if API is reachable
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✓ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return
    
    # Test 2: Get players
    try:
        response = requests.get(f"{BASE_URL}/players")
        print(f"\n✓ Get players: {response.status_code}")
        if response.status_code == 200:
            players = response.json().get('players', [])
            print(f"  Found {len(players)} players")
            for player in players:
                print(f"    - {player['name']} (ID: {player['id']})")
            return players
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Get players failed: {e}")
    
    return []

def test_create_match(player_ids):
    print(f"\nTesting create match with players: {player_ids}")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{BASE_URL}/matches",
            json={
                "player_ids": player_ids,
                "game_type": "501"
            },
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✓ Match created successfully!")
            return response.json()
        else:
            print("✗ Failed to create match")
            # Try to get more details
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                pass
    
    except Exception as e:
        print(f"✗ Request failed: {e}")
    
    return None

def main():
    print("Darts Scoring System - API Debug")
    print("=" * 50)
    
    # Get players first
    players = test_api_endpoints()
    
    if players:
        # Try to create a match with first two players
        player_ids = [players[0]['id'], players[1]['id']]
        test_create_match(player_ids)
    
    print("\n" + "=" * 50)
    print("Debug complete")

if __name__ == "__main__":
    main()