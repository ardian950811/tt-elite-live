import requests
import json
import time

def fetch_data_and_history():
    api_key = "247481-2D476S3VQDJuAj"
    sport_id = "92"
    league_id = "29128"
    
    # 1. Fetch upcoming matches
    upcoming_url = f"https://api.betsapi.com/v1/events/upcoming?token={api_key}&sport_id={sport_id}&league_id={league_id}"
    print(f"Fetching upcoming matches...")
    
    try:
        response = requests.get(upcoming_url, timeout=30)
        upcoming_data = response.json()
        
        with open("upcoming.json", "w", encoding="utf-8") as file_object:
            json.dump(upcoming_data, file_object, indent=4)
        print("upcoming.json successfully saved.")
        
    except Exception as e:
        print(f"Error fetching upcoming matches: {e}")
        return

    # 2. Fetch specific H2H history for each upcoming match
    h2h_dictionary = {}
    
    if 'results' in upcoming_data and upcoming_data['results']:
        matches = upcoming_data['results']
        print(f"Found {len(matches)} upcoming matches. Fetching exact H2H for each...")
        
        for match in matches:
            event_id = match['id']
            home_name = match['home']['name']
            away_name = match['away']['name']
            print(f"Fetching H2H for event {event_id} ({home_name} vs {away_name})...")
            
            h2h_url = f"https://api.betsapi.com/v1/event/history?token={api_key}&event_id={event_id}"
            
            try:
                h2h_response = requests.get(h2h_url, timeout=30)
                h2h_data = h2h_response.json()
                
                # BetsAPI returns 'h2h' array inside 'results'
                if 'results' in h2h_data and 'h2h' in h2h_data['results']:
                    h2h_dictionary[event_id] = h2h_data['results']['h2h']
                else:
                    h2h_dictionary[event_id] = []
                    
            except Exception as e:
                print(f"Error on event {event_id}: {e}")
                h2h_dictionary[event_id] = []
            
            # 1 second delay to respect API rate limits
            time.sleep(1) 
            
    with open("h2h_data.json", "w", encoding="utf-8") as file_object:
        json.dump(h2h_dictionary, file_object, indent=4)
    print("h2h_data.json successfully saved.")

if __name__ == "__main__":
    fetch_data_and_history()
