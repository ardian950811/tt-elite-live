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

    # 1B. Fetch dei match terminati OGGI per recuperare gli scontri diretti quotidiani
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

    # --- NUOVA LOGICA: CALCOLO STATO FORMA GIORNALIERO COMPLETO ---
    player_today_form = {}
    
    for match in today_ended_matches:
        home_name = match.get('home', {}).get('name')
        away_name = match.get('away', {}).get('name')
        if not home_name or not away_name:
            continue
            
        ss = match.get('ss', '') # Punteggio es. "3-1" o "2-3"
        if not ss or '-' not in ss:
            continue
            
        try:
            home_score, away_score = map(int, ss.split('-'))
        except:
            continue
            
        # Calcola l'orario italiano del match
        try:
            timestamp = int(match.get('time', 0))
            time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M')
        except:
            time_str = "--:--"
            
        if home_name not in player_today_form:
            player_today_form[home_name] = []
        if away_name not in player_today_form:
            player_today_form[away_name] = []
            
        # Determina chi ha vinto e aggiunge alla cronologia odierna del giocatore
        if home_score > away_score:
            player_today_form[home_name].append({'res': 'V', 'opp': away_name, 'score': ss, 'time': time_str})
            player_today_form[away_name].append({'res': 'R', 'opp': home_name, 'score': ss, 'time': time_str})
        else:
            player_today_form[home_name].append({'res': 'R', 'opp': away_name, 'score': ss, 'time': time_str})
            player_today_form[away_name].append({'res': 'V', 'opp': home_name, 'score': ss, 'time': time_str})

    # 2. Fetch H2H and precise point details
    h2h_dictionary = {}
    
    if all_upcoming_matches:
        print(f"Total upcoming matches found: {len(all_upcoming_matches)}")
        for match in all_upcoming_matches:
            event_id = match['id']
            home_name = match['home']['name']
            away_name = match['away']['name']
            print(f"Processing H2H for: {home_name} vs {away_name}")
            
            history_list = []
            seen_match_ids = set() 
            
            for t_match in today_ended_matches:
                t_home = t_match.get('home', {}).get('name', '')
                t_away = t_match.get('away', {}).get('name', '')
                t_id = t_match.get('id')
                
                if ((t_home == home_name and t_away == away_name) or (t_home == away_name and t_away == home_name)):
                    if t_id not in seen_match_ids:
                        if 'scores' in t_match:
                            score_cache[t_id] = t_match['scores']
                        history_list.append(t_match)
                        seen_match_ids.add(t_id)

            h2h_url = f"https://api.betsapi.com/v1/event/history?token={api_key}&event_id={event_id}"
            
            try:
                h2h_response = requests.get(h2h_url, timeout=30).json()
                if 'results' in h2h_response and 'h2h' in h2h_response['results']:
                    raw_h2h = h2h_response['results']['h2h']
                    for past_match in raw_h2h:
                        past_id = past_match['id']
                        if past_id in seen_match_ids:
                            continue
                        if len(history_list) >= 18:
                            break
                        
                        if 'scores' not in past_match:
                            if past_id in score_cache:
                                past_match['scores'] = score_cache[past_id]
                            else:
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
                h2h_dictionary[event_id] = history_list
            
            time.sleep(1)
            
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(score_cache, f, indent=4)
        
    with open("h2h_data.json", "w", encoding="utf-8") as f:
        json.dump(h2h_dictionary, f, indent=4)

    # ---> SALVATAGGIO STATO FORMA OGGI (Aggiunto per l'interfaccia scura) <---
    with open("today_form.json", "w", encoding="utf-8") as f:
        json.dump(player_today_form, f, indent=4)

    # --- NUOVA LOGICA: GENERAZIONE FILE HTML VISIVO ---
    print("Generating HTML visualization...")
    
    html_content = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TT Elite Series - Radar Stato Forma</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; color: #333; }
        h2 { text-align: center; color: #222; margin-bottom: 30px; }
        .match-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); max-width: 700px; margin: 0 auto 25px auto; }
        .match-header { font-size: 18px; font-weight: bold; margin-bottom: 15px; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; color: #0056b3; text-align: center; }
        .players-container { display: flex; justify-content: space-between; }
        .player-column { width: 48%; background: #fafafa; padding: 12px; border-radius: 6px; border: 1px solid #eef0f2; }
        .player-title { font-weight: bold; font-size: 16px; margin-bottom: 12px; color: #111; text-align: center; border-bottom: 1px solid #ddd; padding-bottom: 4px; }
        .history-row { display: flex; align-items: center; margin-bottom: 8px; font-size: 14px; }
        .box-v { background-color: #28a745; color: white; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 14px; border-radius: 4px; margin-right: 10px; flex-shrink: 0; }
        .box-r { background-color: #dc3545; color: white; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 14px; border-radius: 4px; margin-right: 10px; flex-shrink: 0; }
        .no-matches { color: #888; font-style: italic; text-align: center; font-size: 14px; padding-top: 10px; }
    </style>
</head>
<body>
    <h2>🏓 TT Elite Series - Palinsesto & Stato Forma Giornaliero</h2>
"""

    if not all_upcoming_matches:
        html_content += "<p style='text-align:center; color:#666;'>Nessun match in programma al momento.</p>"
    else:
        for match in all_upcoming_matches:
            home_name = match.get('home', {}).get('name', 'Unknown')
            away_name = match.get('away', {}).get('name', 'Unknown')
            
            try:
                timestamp = int(match.get('time', 0))
                time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M')
            except:
                time_str = "--:--"
                
            html_content += f"""
            <div class="match-card">
                <div class="match-header">Ore {time_str} | {home_name} vs {away_name}</div>
                <div class="players-container">
                    <div class="player-column">
                        <div class="player-title">{home_name}</div>
            """
            
            home_history = player_today_form.get(home_name, [])
            if home_history:
                for h in home_history:
                    box_class = "box-v" if h['res'] == 'V' else "box-r"
                    html_content += f"""
                        <div class="history-row">
                            <div class="{box_class}">{h['res']}</div>
                            <div>vs {h['opp']} ({h['score']}) alle {h['time']}</div>
                        </div>
                    """
            else:
                html_content += "<div class='no-matches'>Nessun match giocato oggi</div>"
                
            html_content += f"""
                    </div>
                    
                    <div class="player-column">
                        <div class="player-title">{away_name}</div>
            """
            
            away_history = player_today_form.get(away_name, [])
            if away_history:
                for a in away_history:
                    box_class = "box-v" if a['res'] == 'V' else "box-r"
                    html_content += f"""
                        <div class="history-row">
                            <div class="{box_class}">{a['res']}</div>
                            <div>vs {a['opp']} ({a['score']}) alle {a['time']}</div>
                        </div>
                    """
            else:
                html_content += "<div class='no-matches'>Nessun match giocato oggi</div>"
                
            html_content += """
                    </div>
                </div>
            </div>
            """
            
    html_content += """
</body>
</html>
"""

    with open("pingpong.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("All extraction processes and HTML generation completed successfully.")

if __name__ == "__main__":
    fetch_data_with_details()
