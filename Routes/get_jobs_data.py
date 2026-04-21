import requests
import json

def fetch_and_save_jobs():
    url = "https://21g0pfhj-8000.inc1.devtunnels.ms/CRUD/Get_jobs"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error if request fails

        data = response.json()
        
        # Remove duplicates based on job_link, keeping only the first occurrence
        seen_links = set()
        unique_jobs = []
        duplicate_count = 0
        
        for job in data:
            job_link = job.get('job_link')
            if job_link and job_link not in seen_links:
                seen_links.add(job_link)
                unique_jobs.append(job)
            elif job_link:
                duplicate_count += 1
        
        print(f"📊 Total jobs fetched: {len(data)}")
        print(f"🔍 Duplicates removed: {duplicate_count}")
        print(f"✅ Unique jobs to save: {len(unique_jobs)}")

        with open("Scraped_Data/all_jobs_data.json", "w", encoding="utf-8") as f:
            json.dump(unique_jobs, f, indent=4, ensure_ascii=False)
        
        print("✅ Data successfully saved to jobs_data.json")
        return {
            "Status": "Data fetched and saved successfully",
            "total_jobs": len(data),
            "duplicates_removed": duplicate_count,
            "unique_jobs_saved": len(unique_jobs)
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return {"Status":"Api request failed"}
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON response")
        return {"Status":"Failed to parse JSON response"}
