import os
import sys
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime

def log_message(msg):
    print(f"[*] {msg}")

def send_telegram_alert(token, chat_id, message):
    if not token or not chat_id:
        return
    encoded_msg = urllib.parse.quote(message)
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={encoded_msg}&parse_mode=Markdown"
    try:
        urllib.request.urlopen(url, timeout=5)
        log_message("Telegram alert sent successfully.")
    except Exception as e:
        log_message(f"Failed to send Telegram message: {e}")

def fetch_api_data():
    """Scarica i match reali direttamente da BetsAPI."""
    api_key = "247481-2D476S3VQDJuAj"
    sport_id = "92"
    league_id = "29128"
    
    all_matches = []
    
    # 1. Match in programma
    log_message("Fetching upcoming matches from BetsAPI...")
    for page in range(1, 3):
        url = f"https://api.betsapi.com/v1/events/upcoming?token={api_key}&sport_id={sport_id}&league_id={league_id}&page={page}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                if 'results' in data and data['results']:
                    all_matches.extend(data['results'])
                else:
                    break
        except Exception as e:
            log_message(f"Error fetching upcoming page {page}: {e}")
            break
        time.sleep(1)

    # 2. Match conclusi
    log_message("Fetching recently ended matches from BetsAPI...")
    for page in range(1, 3):
        url = f"https://api.betsapi.com/v1/events/ended?token={api_key}&sport_id={sport_id}&league_id={league_id}&page={page}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                if 'results' in data and data['results']:
                    all_matches.extend(data['results'])
                else:
                    break
        except Exception as e:
            log_message(f"Error fetching ended page {page}: {e}")
            break
        time.sleep(1)

    return {"results": all_matches}

def analyze_tt_elite_series():
    telegram_token = os.environ.get("TELEGRAM_TOKEN", "")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    api_response = fetch_api_data()
    matches = api_response.get("results", [])
    
    if not matches:
        log_message("No data received from API. Exiting.")
        sys.exit(0)

    daily_stats = {}
    played_today = {}
    player_today_form = {}
    
    finished_matches = []
    upcoming_matches = []
    current_timestamp = time.time()

    for match in matches:
        status = match.get("time_status", "")
        match_time = int(match.get("time", 0))
        
        # Filtro infallibile basato sulle ultime 15 ore
        if status == "3":  
            if current_timestamp - match_time < 54000:
                finished_matches.append(match)
        elif status == "0":  
            upcoming_matches.append(match)

    for match in finished_matches:
        home_player = match.get("home", {}).get("name")
        away_player = match.get("away", {}).get("name")
        ss = match.get("ss", "")
        
        if not home_player or not away_player or not ss or '-' not in ss:
            continue
            
        try:
            home_score, away_score = map(int, ss.split('-'))
            time_str = datetime.fromtimestamp(int(match.get('time', 0))).strftime('%H:%M')
            
            if home_player not in daily_stats: daily_stats[home_player] = {"wins": 0, "losses": 0}
            if away_player not in daily_stats: daily_stats[away_player] = {"wins": 0, "losses": 0}
            if home_player not in player_today_form: player_today_form[home_player] = []
            if away_player not in player_today_form: player_today_form[away_player] = []
            
            if home_score > away_score:
                daily_stats[home_player]["wins"] += 1
                daily_stats[away_player]["losses"] += 1
                player_today_form[home_player].append({'res': 'V', 'opp': away_player, 'score': ss, 'time': time_str})
                player_today_form[away_player].append({'res': 'R', 'opp': home_player, 'score': ss, 'time': time_str})
                winner = home_player
            else:
                daily_stats[away_player]["wins"] += 1
                daily_stats[home_player]["losses"] += 1
                player_today_form[home_player].append({'res': 'R', 'opp': away_player, 'score': ss, 'time': time_str})
                player_today_form[away_player].append({'res': 'V', 'opp': home_player, 'score': ss, 'time': time_str})
                winner = away_player
                
            matchup_key = tuple(sorted([home_player, away_player]))
            if matchup_key not in played_today:
                played_today[matchup_key] = []
            played_today[matchup_key].append({"winner": winner, "score": ss, "time": time_str})
        except:
            continue

    # SALVATAGGIO DEI FILE JSON IN LOCALE
    with open("today_form.json", "w", encoding="utf-8") as f:
        json.dump(player_today_form, f, indent=4)
        
    with open("upcoming.json", "w", encoding="utf-8") as f:
        json.dump({"results": upcoming_matches}, f, indent=4)
        
    log_message("JSON files written locally.")

    # NOTIFICHE TELEGRAM
    for match in upcoming_matches:
        p1 = match.get("home", {}).get("name")
        p2 = match.get("away", {}).get("name")
        try:
            match_time_str = datetime.fromtimestamp(int(match.get('time', 0))).strftime('%H:%M')
        except:
            match_time_str = "--:--"
            
        rec_1 = daily_stats.get(p1, {"wins": 0, "losses": 0})
        rec_2 = daily_stats.get(p2, {"wins": 0, "losses": 0})
        matchup_key = tuple(sorted([p1, p2]))
        
        report = (
            f"🏓 *TT ELITE SERIES - MATCH RADAR*\n"
            f"⏰ *Ora:* {match_time_str}\n"
            f"🆚 *{p1} vs {p2}*\n\n"
            f"📊 *Forma di Oggi:*\n"
            f"▪️ {p1}: {rec_1['wins']}V - {rec_1['losses']}P\n"
            f"▪️ {p2}: {rec_2['wins']}V - {rec_2['losses']}P\n"
        )
        
        if matchup_key in played_today:
            report += "\n⚠️ *REMATCH RILEVATO OGGI!*\n"
            for previous in played_today[matchup_key]:
                report += f"➡️ Già giocata oggi: vinta da {previous['winner']} ({previous['score']}) alle {previous['time']}\n"
        else:
            report += "\n✅ Primo scontro diretto oggi."

        print("-" * 30)
        print(report)
        send_telegram_alert(telegram_token, telegram_chat_id, report)

if __name__ == "__main__":
    analyze_tt_elite_series()
