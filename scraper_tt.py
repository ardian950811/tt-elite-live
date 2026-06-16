import os
import json
import time
import requests
from datetime import datetime

def log_msg(msg):
    print(f"[*] {msg}")

def run_tracker_scraper():
    api_key = "247481-2D476S3VQDJuAj"
    sport_id = "92"        # Tennis Tavolo
    league_id = "29128"    # TT Elite Series
    
    # Gestione Cache per risparmiare i token sui dettagli dei set
    cache_file = "match_cache.json"
    score_cache = {}
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            try: score_cache = json.load(f)
            except: score_cache = {}

    # 1. Recupero dei Prossimi Match (Pagine 1-3 per copertura completa)
    log_msg("Recupero dei prossimi match in programma...")
    upcoming_matches = []
    for page in range(1, 4):
        url = f"https://api.betsapi.com/v1/events/upcoming?token={api_key}&sport_id={sport_id}&league_id={league_id}&page={page}"
        try:
            res = requests.get(url, timeout=20).json()
            if 'results' in res and res['results']:
                upcoming_matches.extend(res['results'])
            else:
                break
        except Exception as e:
            log_msg(f"Errore pagina upcoming {page}: {e}")
            break
        time.sleep(1)

    # 2. Recupero dei Match Terminati OGGI (Stato di forma in tempo reale)
    log_msg("Recupero dei match terminati oggi...")
    today_ended = []
    today_str = datetime.utcnow().strftime('%Y%m%d')
    url_ended = f"https://api.betsapi.com/v1/events/ended?token={api_key}&sport_id={sport_id}&league_id={league_id}&day={today_str}"
    try:
        res_ended = requests.get(url_ended, timeout=20).json()
        if 'results' in res_ended and res_ended['results']:
            today_ended = res_ended['results']
    except Exception as e:
        log_msg(f"Errore match terminati oggi: {e}")

    # 3. Elaborazione dello Stato di Forma Odierno (Vinte e Perse del giorno stesso)
    player_today_form = {}
    for match in today_ended:
        p1 = match.get('home', {}).get('name')
        p2 = match.get('away', {}).get('name')
        ss = match.get('ss', '')
        if not p1 or not p2 or not ss or '-' not in ss or ss == "0-0": 
            continue
        
        try:
            s1, s2 = map(int, ss.split('-'))
            t_str = datetime.fromtimestamp(int(match.get('time', 0))).strftime('%H:%M')
            
            if p1 not in player_today_form: player_today_form[p1] = []
            if p2 not in player_today_form: player_today_form[p2] = []
            
            if s1 > s2:
                player_today_form[p1].append({'res': 'V', 'opp': p2, 'score': ss, 'time': t_str})
                player_today_form[p2].append({'res': 'R', 'opp': p1, 'score': ss, 'time': t_str})
            else:
                player_today_form[p1].append({'res': 'R', 'opp': p2, 'score': ss, 'time': t_str})
                player_today_form[p2].append({'res': 'V', 'opp': p1, 'score': ss, 'time': t_str})
        except:
            continue

    # 4. Elaborazione degli Ultimi 20 H2H per ogni match futuro
    final_upcoming_list = []
    
    for match in upcoming_matches:
        event_id = match['id']
        p1_name = match['home']['name']
        p2_name = match['away']['name']
        match_time = datetime.fromtimestamp(int(match.get('time', 0))).strftime('%H:%M')
        
        log_msg(f"Analisi H2H profonda (Fino a 20 match): {p1_name} vs {p2_name}")
        h2h_list = []
        seen_ids = set()
        
        # Inserisci prima i match disputati oggi (se presenti) per aggiornare gli H2H real-time
        for t_match in today_ended:
            t_p1 = t_match.get('home', {}).get('name', '')
            t_p2 = t_match.get('away', {}).get('name', '')
            t_id = t_match.get('id')
            if ((t_p1 == p1_name and t_p2 == p2_name) or (t_p1 == p2_name and t_p2 == p1_name)):
                if t_id not in seen_ids:
                    if 'scores' in t_match: score_cache[t_id] = t_match['scores']
                    h2h_list.append(t_match)
                    seen_ids.add(t_id)

        # Chiamata alla cronologia storica degli scontri diretti
        url_h2h = f"https://api.betsapi.com/v1/event/history?token={api_key}&event_id={event_id}"
        try:
            h2h_res = requests.get(url_h2h, timeout=20).json()
            if 'results' in h2h_res and 'h2h' in h2h_res['results']:
                for past in h2h_res['results']['h2h']:
                    past_id = past['id']
                    if past_id in seen_ids: continue
                    if len(h2h_list) >= 20: break  # Limite richiesto di 20 match
                    
                    # Recupero punteggi set per media punti
                    if 'scores' not in past:
                        if past_id in score_cache:
                            past['scores'] = score_cache[past_id]
                        else:
                            url_view = f"https://api.betsapi.com/v1/event/view?token={api_key}&event_id={past_id}"
                            try:
                                v_res = requests.get(url_view, timeout=15).json()
                                if 'results' in v_res and len(v_res['results']) > 0:
                                    past['scores'] = v_res['results'][0].get('scores', [])
                                    score_cache[past_id] = past['scores']
                            except: pass
                            time.sleep(0.5)
                            
                    h2h_list.append(past)
                    seen_ids.add(past_id)
        except Exception as e:
            log_msg(f"Errore storico H2H per evento {event_id}: {e}")

        # Calcolo metriche aggregate sugli ultimi 20 match storici reali
        p1_wins = 0
        p2_wins = 0
        total_points_all_matches = 0
        valid_points_count = 0
        
        for h_match in h2h_list:
            h_p1 = h_match.get('home', {}).get('name', '')
            h_ss = h_match.get('ss', '')
            if not h_ss or '-' not in h_ss or h_ss == "0-0": continue
            
            try:
                sh, sa = map(int, h_ss.split('-'))
                # Verifica vincitore relativo dello scontro diretto
                if sh > sa:
                    if h_p1 == p1_name: p1_wins += 1
                    else: p2_wins += 1
                else:
                    if h_p1 == p1_name: p2_wins += 1
                    else: p1_wins += 1
                
                # Somma dei punti reali fatti nei singoli set
                match_pts = 0
                if 'scores' in h_match and h_match['scores']:
                    for s_set in h_match['scores']:
                        match_pts += int(s_set.get('home', 0)) + int(s_set.get('away', 0))
                if match_pts == 0:
                    match_pts = int((sh + sa) * 18.5) # Fallback matematico prudente
                
                total_points_all_matches += match_pts
                valid_points_count += 1
            except:
                continue

        avg_points = round(total_points_all_matches / valid_points_count, 1) if valid_points_count > 0 else 0.0
        
        # Estrazione quote automatiche BetsAPI come base iniziale
        odds_home = float(match.get('odds', {}).get('main', {}).get('home_od', 1.85))
        odds_away = float(match.get('odds', {}).get('main', {}).get('away_od', 1.85))

        final_upcoming_list.append({
            "id": event_id,
            "time": match_time,
            "home": p1_name,
            "away": p2_name,
            "p1_wins": p1_wins,
            "p2_wins": p2_wins,
            "total_h2h_count": len(h2h_list),
            "avg_points": avg_points,
            "api_odds_home": odds_home,
            "api_odds_away": odds_away
        })
        time.sleep(0.5)

    # Salvataggio file unico e compatto per l'interfaccia HTML
    output_data = {
        "upcoming": final_upcoming_list,
        "today_form": player_today_form
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
        
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(score_cache, f, indent=4)
        
    log_msg("Elaborazione dati completata. File 'data.json' pronto per la dashboard.")

if __name__ == "__main__":
    run_tracker_scraper()
