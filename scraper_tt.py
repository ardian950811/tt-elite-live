import requests
import json
import time

def fetch_upcoming_matches():
    api_key = "247481-2D476S3VQDJuAj"
    url = f"https://api.betsapi.com/v1/events/upcoming?token={api_key}&sport_id=92&league_id=29128"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open("upcoming.json", "w", encoding="utf-8") as file_object:
                json.dump(response.json(), file_object, indent=4)
            print("upcoming.json successfully saved.")
    except Exception as error_message:
        print(f"Error fetching upcoming matches: {error_message}")

def fetch_ended_history():
    api_key = "247481-2D476S3VQDJuAj"
    all_historical_results = []
    
    # Fetching the last 10 pages to build a deep history (approx 500 matches)
    for page_number in range(1, 11):
        url = f"https://api.betsapi.com/v1/events/ended?token={api_key}&sport_id=92&league_id=29128&page={page_number}"
        print(f"Fetching history page {page_number}...")
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and data['results']:
                    all_historical_results.extend(data['results'])
                else:
                    break # No more pages available
            else:
                break
        except Exception as error_message:
            print(f"Error on page {page_number}: {error_message}")
            break
            
        time.sleep(1) # 1 second delay to respect API rate limits
        
    # Save the combined dataset
    final_dataset = {"results": all_historical_results}
    with open("ended.json", "w", encoding="utf-8") as file_object:
        json.dump(final_dataset, file_object, indent=4)
    print(f"ended.json successfully saved with {len(all_historical_results)} total historical matches.")

if __name__ == "__main__":
    fetch_upcoming_matches()
    fetch_ended_history()
