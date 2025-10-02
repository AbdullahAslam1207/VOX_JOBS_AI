import httpx
import json
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


API_URL = os.getenv("API_URL")
CITIES = ["lahore", "karachi", "islamabad", "rawalpindi"]

async def fetch_jobs():
    results = {}
    try:
        async with httpx.AsyncClient() as client:
            tasks = []
            for city in CITIES:
                for page in [1, 2]:
                    url = f"{API_URL}?city={city}&countryid=162&page={page}"
                    tasks.append(client.get(url))
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Organize results
            for i, resp in enumerate(responses):
                try:
                    if isinstance(resp, Exception):
                        print(f"Error fetching data for {CITIES[i // 2]}: {resp}")
                        continue
                    if resp.status_code == 200:
                        data = resp.json()
                        city = CITIES[i // 2]  # Each city has 2 pages
                        jobs = data.get("list", [])
                        if city not in results:
                            results[city] = []
                        results[city].extend(jobs)
                    else:
                        print(f"Failed to fetch jobs for {CITIES[i // 2]}: Status {resp.status_code}")
                except Exception as e:
                    print(f"Error processing response for {CITIES[i // 2]}: {e}")

        # Save to JSON file
        file_path = Path("Scraped_Data/jobs_data_mustaqbil.json")
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"An error occurred in fetch_jobs: {e}")

    return {"message": "Jobs fetched and stored in Scraped_Data/jobs_data_mustaqbil.json", "cities": list(results.keys())}