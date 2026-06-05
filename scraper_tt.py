import json
import urllib.request

def main():
    # URL mirato alla sezione TT Elite di Scores24 (endpoint interno)
    url = "https://scores24.live/api/v2/table-tennis/matches"
    
    # Header che simulano un browser reale
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://scores24.live/",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            dati = json.loads(response.read().decode('utf-8'))
            
            # Qui filtriamo solo i match della TT Elite
            matches_elite = [m for m in dati if "TT Elite" in m.get("tournament_name", "")]
            
            # Salviamo il risultato per il debug iniziale
            with open("database_h2h.json", "w", encoding="utf-8") as f:
                json.dump(matches_elite, f, indent=4)
            
            print(f"Successo! Salvati {len(matches_elite)} match.")
            
    except Exception as e:
        print(f"Errore di connessione: {e}")

if __name__ == "__main__":
    main()
