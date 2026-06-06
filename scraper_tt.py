import requests
import json
import sys

def fetch_and_save_data(endpoint_type):
    api_key = "247481-2D476S3VQDJuAj"
    sport_id = "92"
    league_id = "29128"
    
    url = f"https://api.betsapi.com/v1/events/{endpoint_type}?token={api_key}&sport_id={sport_id}&league_id={league_id}"
    print(f"Fetching {endpoint_type} data from: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Response status code for {endpoint_type}: {response.status_code}")
        
        if response.status_code == 200:
            api_data = response.json()
            output_filename = f"{endpoint_type}.json"
            
            with open(output_filename, "w", encoding="utf-8") as file_object:
                json.dump(api_data, file_object, indent=4)
            print(f"Successfully saved data to {output_filename}")
        else:
            print(f"Error response from API for {endpoint_type}: {response.text}")
    except Exception as error_message:
        print(f"Exception occurred during execution for {endpoint_type}: {error_message}")

if __name__ == "__main__":
    fetch_and_save_data("ended")
    fetch_and_save_data("upcoming")
