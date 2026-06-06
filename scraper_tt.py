import requests
import json
import os

def main():
    API_KEY = "247481-2D476S3VQDJuAj"
    
    # Abbiamo aggiunto sport_id=92 (Table Tennis) come richiesto dall'API
    # e mantenuto league_id=29128 (TT Elite Series)
    url = f"https://api.betsapi.com/v1/events/ended?token={API_KEY}&sport_id=92&league_id=29128"
    
    print(f"Chiamata API a: {url}")
    
    try:
        response = requests.get(url)
        print(f"Stato risposta API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            with open("database_h2h.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                
            print("File database_h2h.json creato con i dati corretti.")
        else:
            print(f"Errore HTTP: {response.text}")
            
    except Exception as e:
        print(f"Errore nello script: {e}")

if __name__ == "__main__":
    main()
