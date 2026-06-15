import os
import sys
import json
import time
import requests
from datetime import datetime

def log_message(msg):
    print(f"[*] {msg}")

def fetch_api_data():
    api_key = "247481-2D476S3VQDJuAj"
    sport_id = "92"
    league_id = "29128"
    all_matches = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    log_message("Fetching upcoming matches...")
    url_up = f"https://api.betsapi.com/v1/events/upcoming?token={api_key}&sport_id={sport_id}&league_id={league_id}"
    try:
        res = requests.get(url_up, headers=headers, timeout=15)
        if res.status_code == 200: all_matches.extend(res.json().get('results', []))
    except: pass

    log_message("Fetching recently ended matches...")
    url_end = f"https://api.betsapi.com/v1/events/ended?token={api_key}&sport_id={sport_id}&league_id={league_id}"
    try:
        res = requests.get(url_end, headers=headers, timeout=15)
        if res.status_code == 200: all_matches.extend(res.json().get('results', []))
    except: pass

    return {"results": all_matches}

def analyze_tt_elite_series():
    api_response = fetch_api_data()
    matches = api_response.get("results", [])
    
    if not matches:
        sys.exit(0)

    player_today_form = {}
    h2h_data = {}
    upcoming_list = []
    current_timestamp = time.time()

    for match in matches:
        status = match.get("time_status", "")
        match_time = int(match.get("time", 0))
        p1 = match.get("home", {}).get("name", "")
        p2 = match.get("away", {}).get("name", "")
        ss = match.get("ss", "")

        if status == "3" and (current_timestamp - match_time < 86400):
            if not p1 or not p2 or not ss or '-' not in ss or ss == "0-0": continue
            try:
                s1, s2 = map(int, ss.split('-'))
                time_str = datetime.fromtimestamp(match_time).strftime('%H:%M')
                if p1 not in player_today_form: player_today_form[p1] = []
                if p2 not in player_today_form: player_today_form[p2] = []
                if s1 > s2:
                    player_today_form[p1].append({'res': 'V', 'opp': p2, 'score': ss, 'time': time_str})
                    player_today_form[p2].append({'res': 'R', 'opp': p1, 'score': ss, 'time': time_str})
                else:
                    player_today_form[p1].append({'res': 'R', 'opp': p2, 'score': ss, 'time': time_str})
                    player_today_form[p2].append({'res': 'V', 'opp': p1, 'score': ss, 'time': time_str})
            except: continue

        if status == "3" and p1 and p2 and ss and ss != "0-0" and '-' in ss:
            matchup_key = "-vs-".join(sorted([p1, p2]))
            if matchup_key not in h2h_data:
                h2h_data[matchup_key] = {"matches": [], "p1_wins": 0, "p2_wins": 0, "total_pts": 0, "match_count_with_sets": 0}
            try:
                s1, s2 = map(int, ss.split('-'))
                pts_match = 0
                if "scores" in match and match["scores"]:
                    for set_score in match["scores"]:
                        pts_match += int(set_score.get("home", 0)) + int(set_score.get("away", 0))
                if pts_match == 0: pts_match = int((s1 + s2) * 18.5)
                date_str = datetime.fromtimestamp(match_time).strftime('%d/%m/%Y')
                sorted_players = sorted([p1, p2])
                h2h_data[matchup_key]["matches"].append({"date": date_str, "home": p1, "away": p2, "score": ss, "pts": pts_match})
                if (p1 if s1 > s2 else p2) == sorted_players[0]: h2h_data[matchup_key]["p1_wins"] += 1
                else: h2h_data[matchup_key]["p2_wins"] += 1
                h2h_data[matchup_key]["total_pts"] += pts_match
                h2h_data[matchup_key]["match_count_with_sets"] += 1
            except: continue
        elif status == "0":
            upcoming_list.append(match)

    upcoming_analyzed = []
    for match in upcoming_list:
        p1, p2 = match.get("home", {}).get("name", ""), match.get("away", {}).get("name", "")
        time_str = datetime.fromtimestamp(int(match.get("time", 0))).strftime('%H:%M')
        matchup_key = "-vs-".join(sorted([p1, p2]))
        h2h_info = h2h_data.get(matchup_key, {"matches": [], "p1_wins": 0, "p2_wins": 0, "total_pts": 0, "match_count_with_sets": 0})
        total_h2h = h2h_info["p1_wins"] + h2h_info["p2_wins"]
        avg_pts = round(h2h_info["total_pts"] / h2h_info["match_count_with_sets"], 1) if h2h_info["match_count_with_sets"] > 0 else 0.0
        odds_home = float(match.get("odds", {}).get("main", {}).get("home_od", 1.85))
        odds_away = float(match.get("odds", {}).get("main", {}).get("away_od", 1.85))
        sorted_players = sorted([p1, p2])
        p1_win_prob = (h2h_info["p1_wins"] / total_h2h) if total_h2h > 0 else 0.5
        p2_win_prob = (h2h_info["p2_wins"] / total_h2h) if total_h2h > 0 else 0.5
        is_value_home = (odds_home * p1_win_prob) > 1.05 if p1 == sorted_players[0] else (odds_home * p2_win_prob) > 1.05
        is_value_away = (odds_away * p2_win_prob) > 1.05 if p2 == sorted_players[0] else (odds_away * p1_win_prob) > 1.05

        upcoming_analyzed.append({
            "time": time_str, "home": p1, "away": p2, "odds_home": odds_home, "odds_away": odds_away,
            "value_home": is_value_home, "value_away": is_value_away, "avg_points": avg_pts,
            "h2h_matches_count": len(h2h_info["matches"]), "h2h_history": h2h_info["matches"][:10],
            "p1_name": sorted_players[0], "p2_name": sorted_players[1], "p1_wins": h2h_info["p1_wins"], "p2_wins": h2h_info["p2_wins"]
        })

    with open("today_form.json", "w", encoding="utf-8") as f: json.dump(player_today_form, f, indent=4)
    with open("upcoming.json", "w", encoding="utf-8") as f: json.dump({"results": upcoming_analyzed}, f, indent=4)
    log_message("Data saved successfully.")

if __name__ == "__main__":
    analyze_tt_elite_series()
