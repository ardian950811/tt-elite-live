import requests
import json

def main():
    # La tua chiave API
    API_KEY = "247481-2D476S3VQDJuAj"
    
    # URL per ottenere i match (Eventi) - Esempio per TT Elite Series
    # Abbiamo tolto il limite di "finta navigazione", ora usiamo solo il token
    url = f"https://api.betsapi.com/v1/events/tt/list?token={API_KEY}&sport_id=29128"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Salviamo il file JSON grezzo per ora
            with open("database_h2h.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print("Dati API scaricati correttamente.")
        else:
            print(f"Errore API: {response.status_code}")
    except Exception as e:
        print(f"Errore nel collegamento API: {e}")

if __name__ == "__main__":
    main()
  
