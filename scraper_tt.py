import requests
import json
import time
import os
from datetime import datetime

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

    # 1B. NUOVO: Fetch dei match terminati OGGI per recuperare gli scontri diretti quotidiani
    print("Fetching today's ended matches to catch daily encounters...")
    today_ended_matches = []
    today_date_str = datetime.utcnow().strftime('%Y%m%d') # Formato AAAAMMGG richiesto da BetsAPI
    
    ended_today_url = f"https://api.betsapi.com/v1/events/ended?token={api_key}&sport_id={sport_id}&league_id={league_id}&day={today_date_str}"
    try:
        ended_response = requests.get(ended_today_url, timeout=30).json()
        if 'results' in ended_response and ended_response['results']:
            today_ended_matches = ended_response['results']
            print(f"Found {len(today_ended_matches)} matches already ended today.")
    except Exception as e:
        print(f"Error fetching today's ended matches: {e}")

    # 2. Fetch H2H and precise point details
    h2h_dictionary = {}
    
    if all_upcoming_matches:
        print(f"Total upcoming matches found: {len(all_upcoming_matches)}")
        for match in all_upcoming_matches:
            event_id = match['id']
            home_name = match['home']['name']
            away_name = match['away']['name']
            print(f"Processing H2H for: {home_name} vs {away_name}")
            
            # Prepariamo la lista finale degli H2H partendo da quelli giocati OGGI
            history_list = []
            seen_match_ids = set() # Per evitare duplicati se BetsAPI aggiorna velocemente
            
            # Cerca se si sono già sfidati OGGI
            for t_match in today_ended_matches:
                t_home = t_match.get('home', {}).get('name', '')
                t_away = t_match.get('away', {}).get('name', '')
                t_id = t_match.get('id')
                
                # Se i due giocatori coincidono (in qualsiasi ordine)
                if ((t_home == home_name and t_away == away_name) or (t_home == away_name and t_away == home_name)):
                    if t_id not in seen_match_ids:
                        print(f"  -> Found a match played TODAY ({t_id}). Injecting into H2H.")
                        # Salviamo i punteggi dei set in cache se presenti
                        if 'scores' in t_match:
                            score_cache[t_id] = t_match['scores']
                        history_list.append(t_match)
                        seen_match_ids.add(t_id)

            # Ora scarichiamo lo storico H2H standard dall'API
            h2h_url = f"https://api.betsapi.com/v1/event/history?token={api_key}&event_id={event_id}"
            
            try:
                h2h_response = requests.get(h2h_url, timeout=30).json()
                
                if 'results' in h2h_response and 'h2h' in h2h_response['results']:
                    raw_h2h = h2h_response['results']['h2h']
                    
                    # Prendiamo i match storici (fino a riempirne un massimo di 18 totali)
                    for past_match in raw_h2h:
                        past_id = past_match['id']
                        
                        # Se abbiamo già inserito questo match tramite il controllo "di oggi", saltalo
                        if past_id in seen_match_ids:
                            continue
                            
                        if len(history_list) >= 18:
                            break
                        
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
                        seen_match_ids.add(past_id)
                        
                h2h_dictionary[event_id] = history_list
                
            except Exception as e:
                print(f"Error on event {event_id}: {e}")
                # Se fallisce la chiamata H2H, teniamo almeno quelli di oggi intercettati prima
                h2h_dictionary[event_id] = history_list
            
            time.sleep(1)
            
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(score_cache, f, indent=4)
        
    with open("h2h_data.json", "w", encoding="utf-8") as f:
        json.dump(h2h_dictionary, f, indent=4)
    print("All extraction processes completed successfully.")

if __name__ == "__main__":
    fetch_data_with_details()
