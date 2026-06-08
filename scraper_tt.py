import requests
import json
import time
import os

def fetch_data_with_details():
    api_key = "247481-2D476S3VQDJuAj"
    sport_id = "92"
    league_id = "29128"
    
    # Load cache to avoid redundant API calls and save tokens
    cache_file = "match_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            try:
                score_cache = json.load(f)
            except:
                score_cache = {}
    else:
        score_cache = {}

    # 1. Fetch upcoming matches with pagination
    print("Fetching upcoming matches...")
    all_upcoming_matches = []
    
    for page_num in range(1, 4):
        upcoming_url = f"https://api.betsapi.com/v1/events/upcoming?token={api_key}&sport_id={sport_id}&league_id={league_id}&page={page_num}"
        print(f"Fetching upcoming page {page_num}...")
        try:
            response = requests.get(upcoming_url, timeout=30)
            data = response.json()
            if 'results' in data and data['results']:
                all_upcoming_matches.extend(data['results'])
            else:
                break 
        except Exception as e:
            print(f"Error fetching upcoming page {page_num}: {e}")
            break
        time.sleep(1) 
        
    upcoming_data = {"results": all_upcoming_matches}
    
    with open("upcoming.json", "w", encoding="utf-8") as f:
        json.dump(upcoming_data, f, indent=4)

    # 2. Fetch H2H and precise point details
    h2h_dictionary = {}
    
    if all_upcoming_matches:
        print(f"Total upcoming matches found: {len(all_upcoming_matches)}")
        for match in all_upcoming_matches:
            event_id = match['id']
            home_name = match['home']['name']
            away_name = match['away']['name']
            print(f"Processing H2H for: {home_name} vs {away_name}")
            
            h2h_url = f"https://api.betsapi.com/v1/event/history?token={api_key}&event_id={event_id}"
            
            try:
                h2h_response = requests.get(h2h_url, timeout=30).json()
                history_list = []
                
                if 'results' in h2h_response and 'h2h' in h2h_response['results']:
                    raw_h2h = h2h_response['results']['h2h']
                    
                    # MODIFICATO QUI: Ora prende fino a 18 match
                    for past_match in raw_h2h[:18]:
                        past_id = past_match['id']
                        
                        if 'scores' not in past_match:
                            if past_id in score_cache:
                                past_match['scores'] = score_cache[past_id]
                            else:
                                print(f"  -> Fetching exact points for past match {past_id}...")
                                view_url = f"https://api.betsapi.com/v1/event/view?token={api_key}&event_id={past_id}"
                                view_response = requests.get(view_url, timeout=30).json()
                                
                                if 'results' in view_response and len(view_response['results']) > 0:
                                    detailed_data = view_response['results'][0]
                                    if 'scores' in detailed_data:
                                        past_match['scores'] = detailed_data['scores']
                                        score_cache[past_id] = detailed_data['scores']
                                
                                time.sleep(1)
                        
                        history_list.append(past_match)
                        
                h2h_dictionary[event_id] = history_list
                
            except Exception as e:
                print(f"Error on event {event_id}: {e}")
                h2h_dictionary[event_id] = []
            
            time.sleep(1)
            
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(score_cache, f, indent=4)
        
    with open("h2h_data.json", "w", encoding="utf-8") as f:
        json.dump(h2h_dictionary, f, indent=4)
    print("All extraction processes completed successfully.")

if __name__ == "__main__":
    fetch_data_with_details()
