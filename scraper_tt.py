import requests
import json
import os

def main():
    API_KEY = "247481-2D476S3VQDJuAj"
    # Usiamo l'endpoint per la lista degli eventi
    url = f"https://api.betsapi.com/v1/events/tt/list?token={API_KEY}&sport_id=29128"
    
    print(f"Tentativo di connessione a: {url}")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            # Percorso assoluto per sicurezza
            file_path = "database_h2h.json"
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            
            if os.path.exists(file_path):
                print(f"File creato con successo: {os.path.abspath(file_path)}")
            else:
                print("Errore: Il file non è stato creato!")
        else:
            print(f"Errore API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Errore nello script: {e}")

if __name__ == "__main__":
    main()
