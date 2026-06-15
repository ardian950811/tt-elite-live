import requests
import json
import time
import os
from datetime import datetime

def fetch_data_with_details():
    api_key = "247481-2D476S3VQDJuAj"
    sport_id = "92"
    league_id = "29128"
    
    cache_file = "match_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            try:
                score_cache = json.load(f)
            except:
                score_cache = {}
    else:
        score_cache = {}

    # 1. Fetch upcoming matches
    print("Fetching upcoming matches...")
    all_upcoming_matches = []
    for page_num in range(1, 4):
        upcoming_url = f"https://api.betsapi.com/v1/events/upcoming?token={api_key}&sport_id={sport_id}&league_id={league_id}&page={page_num}"
        try:
            response = requests.get(upcoming_url, timeout=30).json()
            if 'results' in response and response['results']:
                all_upcoming_matches.extend(response['results'])
            else:
                break
        except:
            break
        time.sleep(1)
        
    with open("upcoming.json", "w", encoding="utf-8") as f:
        json.dump({"results": all_upcoming_matches}, f, indent=4)

    # 1B. Fetch dei match terminati (Metodo infallibile: ultime 15 ore)
    print("Fetching ended matches (last 15 hours)...")
    today_ended_matches = []
    current_timestamp = time.time()
    
    for page_num in range(1, 4):
        ended_url = f"https://api.betsapi.com/v1/events/ended?token={api_key}&sport_id={sport_id}&league_id={league_id}&page={page_num}"
        try:
            ended_response = requests.get(ended_url, timeout=30).json()
            if 'results' in ended_response and ended_response['results']:
                for m in ended_response['results']:
                    match_time = int(m.get('time', 0))
                    # Se il match è avvenuto nelle ultime 15 ore (54000 secondi)
                    if current_timestamp - match_time < 54000:
                        today_ended_matches.append(m)
            else:
                break
        except:
            break
        time.sleep(1)

    # Calcolo Stato Forma Giornaliero
    player_today_form = {}
    for match in today_ended_matches:
        home_name = match.get('home', {}).get('name')
        away_name = match.get('away', {}).get('name')
        ss = match.get('ss', '')
        if not home_name or not away_name or not ss or '-' not in ss:
            continue
            
        try:
            home_score, away_score = map(int, ss.split('-'))
            time_str = datetime.fromtimestamp(int(match.get('time', 0))).strftime('%H:%M')
            
            if home_name not in player_today_form: player_today_form[home_name] = []
            if away_name not in player_today_form: player_today_form[away_name] = []
            
            if home_score > away_score:
                player_today_form[home_name].append({'res': 'V', 'opp': away_name, 'score': ss, 'time': time_str})
                player_today_form[away_name].append({'res': 'R', 'opp': home_name, 'score': ss, 'time': time_str})
            else:
                player_today_form[home_name].append({'res': 'R', 'opp': away_name, 'score': ss, 'time': time_str})
                player_today_form[away_name].append({'res': 'V', 'opp': home_name, 'score': ss, 'time': time_str})
        except:
            continue

    # Salvataggio dati
    with open("today_form.json", "w", encoding="utf-8") as f:
        json.dump(player_today_form, f, indent=4)

    # 2. H2H (Logica mantenuta)
    h2h_dictionary = {}
    for match in all_upcoming_matches:
        event_id = match['id']
        h2h_url = f"https://api.betsapi.com/v1/event/history?token={api_key}&event_id={event_id}"
        try:
            resp = requests.get(h2h_url, timeout=30).json()
            h2h_dictionary[event_id] = resp['results']['h2h'] if 'results' in resp and 'h2h' in resp['results'] else []
        except:
            h2h_dictionary[event_id] = []
        time.sleep(1)
            
    with open("h2h_data.json", "w", encoding="utf-8") as f:
        json.dump(h2h_dictionary, f, indent=4)
        
    print("Processo completato.")

if __name__ == "__main__":
    fetch_data_with_details()
