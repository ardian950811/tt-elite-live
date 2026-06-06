import requests
import json
import os

def main():
    # Chiave API
    API_KEY = "247481-2D476S3VQDJuAj"
    
    # Questo è l'endpoint corretto per il Table Tennis (lista eventi)
    url = f"https://api.betsapi.com/v1/events/tt/list?token={API_KEY}"
    
    print(f"Chiamata API in corso a: {url}")
    
    try:
        response = requests.get(url)
        print(f"Stato risposta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Salvataggio
            with open("database_h2h.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print("Successo: file database_h2h.json creato.")
            
        else:
            # Se fallisce ancora, stampiamo il messaggio di errore completo
            print(f"Errore API ricevuto: {response.text}")
            
    except Exception as e:
        print(f"Errore nello script: {e}")

if __name__ == "__main__":
    main()
