import requests
import json

def fetch_and_save_jobs():
    url = "https://hmmpwkwg-8000.asse.devtunnels.ms/CRUD/Get_jobs"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error if request fails

        data = response.json()

        with open("Scraped_Data/all_jobs_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print("✅ Data successfully saved to jobs_data.json")
        return {"Status":"Data fetched and saved successfully"}

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return {"Status":"Api request failed"}
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON response")
        return {"Status":"Failed to parse JSON response"}
