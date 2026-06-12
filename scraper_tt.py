import os
import sys
import json
import urllib.parse
import urllib.request
from datetime import datetime

def log_message(msg):
    print(f"[*] {msg}")

def fetch_api_data(api_url):
    """
    Fetches the live schedule and results from your sports API.
    """
    # Se hai l'URL reale dell'API configurato, rimuovi i '#' dalle righe sotto:
    # req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    # try:
    #     with urllib.request.urlopen(req, timeout=10) as response:
    #         return json.loads(response.read())
    # except Exception as e:
    #     log_message(f"API Error: {e}")
    #     return {}
    
    # DATI DI SIMULAZIONE (Sostituisci o attiva la chiamata reale qui sopra)
    # Questo serve per testare il comportamento quando ci sono più match lo stesso giorno
    return {
        "results": [
            {
                "time": f"{datetime.now().strftime('%Y-%m-%d')} 09:30:00",
                "status": "ended",
                "home": {"name": "Jan Zandecki"},
                "away": {"name": "Jaime Lama"},
                "scores": {"home": "3", "away": "1"}
            },
            {
                "time": f"{datetime.now().strftime('%Y-%m-%d')} 10:15:00",
                "status": "ended",
                "home": {"name": "Alex Moreno"},
                "away": {"name": "Jan Zandecki"},
                "scores": {"home": "3", "away": "2"}
            },
            {
                "time": f"{datetime.now().strftime('%Y-%m-%d')} 14:00:00",
                "status": "notstarted",
                "home": {"name": "Jaime Lama"},
                "away": {"name": "Jan Zandecki"},
                "scores": {"home": "0", "away": "0"}
            }
        ]
    }

def analyze_tt_elite_series():
    # Inserisci qui l'indirizzo della tua API (es. BetsAPI o AiScore)
    api_url = "INSERISCI_QUI_IL_TUO_URL_API" 
    
    api_response = fetch_api_data(api_url)
    matches = api_response.get("results", [])
    
    if not matches:
        log_message("No data received from API. Exiting.")
        sys.exit(0)

    daily_stats = {}
    played_today = {}
    
    finished_matches = []
    upcoming_matches = []
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Separa i match finiti da quelli da giocare (solo relativi a oggi)
    for match in matches:
        match_time = match.get("time", "")
        if current_date not in match_time:
            continue
            
        status = match.get("status", "")
        if status == "ended":
            finished_matches.append(match)
        else:
            upcoming_matches.append(match)

    # 2. Elabora i match conclusi per aggiornare la forma e registrare i scontrati del giorno
    for match in finished_matches:
        home_player = match["home"]["name"]
        away_player = match["away"]["name"]
        home_score = int(match["scores"]["home"])
        away_score = int(match["scores"]["away"])
        
        winner = home_player if home_score > away_score else away_player
        
        for player in [home_player, away_player]:
            if player not in daily_stats:
                daily_stats[player] = {"wins": 0, "losses": 0}
                
        if winner == home_player:
            daily_stats[home_player]["wins"] += 1
            daily_stats[away_player]["losses"] += 1
        else:
            daily_stats[away_player]["wins"] += 1
            daily_stats[home_player]["losses"] += 1
            
        # Genera una chiave unica per la coppia di giocatori (indipendentemente da chi gioca in casa)
        matchup_key = tuple(sorted([home_player, away_player]))
        if matchup_key not in played_today:
            played_today[matchup_key] = []
        
        played_today[matchup_key].append({
            "winner": winner,
            "score": f"{home_score}-{away_score}",
            "time": match_time.split(" ")[1]
        })

    # 3. Analizza e stampa i match in arrivo o live nel terminale delle Actions
    print(f"\n=======================================================")
    print(f"   TT ELITE SERIES DAILY RADAR REPORT ({current_date})")
    print(f"=======================================================")
    
    for match in upcoming_matches:
        p1 = match["home"]["name"]
        p2 = match["away"]["name"]
        match_time = match.get("time", "").split(" ")[1]
        
        rec_1 = daily_stats.get(p1, {"wins": 0, "losses": 0})
        rec_2 = daily_stats.get(p2, {"wins": 0, "losses": 0})
        
        matchup_key = tuple(sorted([p1, p2]))
        
        print(f"\n[MATCH] Time: {match_time} | {p1} vs {p2}")
        print(f"   -> Form {p1}: {rec_1['wins']}W - {rec_1['losses']}L")
        print(f"   -> Form {p2}: {rec_2['wins']}W - {rec_2['losses']}L")
        
        # Verifica se la coppia ha già giocato oggi
        if matchup_key in played_today:
            print(f"   ⚠️ ALERT: SAME-DAY REMATCH DETECTED!")
            for previous in played_today[matchup_key]:
                print(f"      - Played earlier: Winner was {previous['winner']} ({previous['score']}) at {previous['time']}")
        else:
            print("   ✅ First meeting today.")
            
    print("\n=======================================================")

if __name__ == "__main__":
    analyze_tt_elite_series()
