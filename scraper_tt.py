import cloudscraper
from bs4 import BeautifulSoup
import json

def main():
    # Cloudscraper simula un browser reale per superare il blocco
    scraper = cloudscraper.create_scraper()
    url = "https://it.betsapi.com/table-tennis/l/29128/tt-elite-series"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    try:
        response = scraper.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Errore: Sito non raggiungibile (Status {response.status_code})")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Questa parte è delicata: dobbiamo trovare dove sono le partite
        # BetsAPI solitamente usa tabelle o div specifici.
        match_list = []
        
        # ESEMPIO: Cerchiamo le righe dei match (va adattato ispezionando la pagina)
        for row in soup.select('tr'): # 'tr' sono le righe di una tabella
            cols = row.find_all('td')
            if len(cols) > 2:
                # Supponiamo che i nomi siano nella colonna 2
                match_text = cols[1].text.strip()
                if " vs " in match_text:
                    g1, g2 = match_text.split(" vs ")
                    match_list.append({
                        "g1": g1.strip(),
                        "g2": g2.strip(),
                        "vincitore": g1.strip(), # Qui dovresti aggiungere logica per leggere il risultato
                        "punti_totali": 70 # Valore segnaposto
                    })
        
        # Salva i dati trovati
        with open("database_h2h.json", "w", encoding="utf-8") as f:
            json.dump(match_list, f, indent=4)
            
    except Exception as e:
        print(f"Errore critico: {e}")

if __name__ == "__main__":
    main()
