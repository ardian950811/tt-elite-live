import os
import sys
import json
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

def fetch_api_data(api_url):
    """
    Fetches the live schedule and results from your sports API.
    """
    # Se hai un URL reale, usa questa parte:
    # req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    # try:
    #     with urllib.request.urlopen(req, timeout=10) as response:
    #         return json.loads(response.read())
    # except Exception as e:
    #     log_message(f"API Error: {e}")
    #     return {}
    
    # Dati di test (sostituisci la chiamata API reale qui sopra quando sei pronto)
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
    # Recupera i Secrets da GitHub Actions
    telegram_token = os.environ.get("TELEGRAM_TOKEN", "")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    # Inserisci qui l'URL della tua API
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
    
    # 1. Suddivide i match della giornata tra conclusi e da giocare
    for match in matches:
        match_time = match.get("time", "")
        if current_date not in match_time:
            continue
            
        status = match.get("status", "")
        if status == "ended":
            finished_matches.append(match)
        else:
            upcoming_matches.append(match)

    # 2. Costruisce lo storico di oggi (Daily Form & H2H)
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
            
        matchup_key = tuple(sorted([home_player, away_player]))
        if matchup_key not in played_today:
            played_today[matchup_key] = []
        
        played_today[matchup_key].append({
            "winner": winner,
            "score": f"{home_score}-{away_score}",
            "time": match_time.split(" ")[1]
        })

    # 3. Analizza i match in programma e invia alert su Telegram
    log_message(f"Analyzing upcoming matches for {current_date}...")
    
    for match in upcoming_matches:
        p1 = match["home"]["name"]
        p2 = match["away"]["name"]
        match_time = match.get("time", "").split(" ")[1]
        
        rec_1 = daily_stats.get(p1, {"wins": 0, "losses": 0})
        rec_2 = daily_stats.get(p2, {"wins": 0, "losses": 0})
        
        matchup_key = tuple(sorted([p1, p2]))
        
        # Prepara il report testuale
        report = (
            f"🏓 *TT ELITE SERIES - MATCH RADAR*\n"
            f"⏰ *Time:* {match_time}\n"
            f"🆚 *{p1} vs {p2}*\n\n"
            f"📊 *Daily Form:*\n"
            f"▪️ {p1}: {rec_1['wins']}W - {rec_1['losses']}L\n"
            f"▪️ {p2}: {rec_2['wins']}W - {rec_2['losses']}L\n"
        )
        
        # Aggiunge l'avviso se si sono già scontrati oggi
        if matchup_key in played_today:
            report += "\n⚠️ *SAME-DAY REMATCH DETECTED!*\n"
            for previous in played_today[matchup_key]:
                report += f"➡️ Previous today: {previous['winner']} won ({previous['score']}) at {previous['time']}\n"
        else:
            report += "\n✅ First meeting today."

        print("-" * 30)
        print(report)
        
        # Invia a Telegram solo se ci sono match imminenti
        send_telegram_alert(telegram_token, telegram_chat_id, report)

if __name__ == "__main__":
    analyze_tt_elite_series()
