# debug_throw_400.py
"""Debug the 400 error on throw endpoint"""
import requests
import json

def test_throw_endpoint():
    BASE_URL = "http://127.0.0.1:5000/api"
    
    print("Testing throw endpoint...")
    print("=" * 50)
    
    # First, check if we can get players
    try:
        response = requests.get(f"{BASE_URL}/players", timeout=5)
        print(f"GET /players: {response.status_code}")
        if response.status_code == 200:
            players = response.json().get('players', [])
            print(f"Found {len(players)} players")
            
            if len(players) >= 2:
                player_ids = [players[0]['id'], players[1]['id']]
                
                # Create a match
                print(f"\nCreating match with players {player_ids}...")
                response = requests.post(
                    f"{BASE_URL}/matches",
                    json={"player_ids": player_ids, "game_type": "501"},
                    timeout=5
                )
                
                print(f"POST /matches: {response.status_code}")
                if response.status_code == 201:
                    match_data = response.json()
                    match_id = match_data['match']['id']
                    leg_id = match_data['leg']['leg']['id']
                    
                    print(f"Match ID: {match_id}, Leg ID: {leg_id}")
                    
                    # Test the throw endpoint
                    print(f"\nTesting throw endpoint for dart 1...")
                    test_data = {
                        "player_id": player_ids[0],
                        "segment": 20,
                        "multiplier": 1,
                        "dart_number": 1
                    }
                    
                    print(f"Request data: {json.dumps(test_data, indent=2)}")
                    
                    response = requests.post(
                        f"{BASE_URL}/matches/{match_id}/legs/{leg_id}/throw",
                        json=test_data,
                        timeout=5
                    )
                    
                    print(f"\nPOST /throw: {response.status_code}")
                    print(f"Response: {response.text}")
                    
                    if response.status_code == 400:
                        print("\n400 Error details:")
                        try:
                            error_data = response.json()
                            print(json.dumps(error_data, indent=2))
                        except:
                            print("Could not parse error response")
                
                else:
                    print(f"Failed to create match: {response.text}")
            
        else:
            print(f"Failed to get players: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Flask server")
        print("Make sure Flask is running: python run.py")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_throw_endpoint()