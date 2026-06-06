import requests
import json
import os

def main():
    API_KEY = "247481-2D476S3VQDJuAj"
    # URL ufficiale
    url = f"https://api.betsapi.com/v1/events/tt/list?token={API_KEY}&sport_id=29128"
    
    print("--- INIZIO SCRIPT ---")
    
    response = requests.get(url)
    print(f"Stato risposta API: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Definiamo il percorso esatto nella cartella dove viene eseguito lo script
        # Usiamo os.getcwd() per vedere dove siamo
        cartella_corrente = os.getcwd()
        file_path = os.path.join(cartella_corrente, "database_h2h.json")
        
        print(f"Sto salvando il file in: {file_path}")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        if os.path.exists(file_path):
            print("CONFERMA: Il file esiste ed è stato scritto.")
        else:
            print("ERRORE CRITICO: Il file non è stato scritto.")
            
    else:
        print(f"Errore API: {response.text}")

if __name__ == "__main__":
    main()
