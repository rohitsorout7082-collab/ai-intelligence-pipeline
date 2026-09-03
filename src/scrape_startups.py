import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TOTAL_TARGET = 1000
OUTPUT_CSV = "data/startups.csv"
PER_PAGE = 100

async def fetch_ai_orgs(session: aiohttp.ClientSession, page: int):
    url = "https://api.github.com/search/users"
    params = {
        "q": "type:org ai in:name,description",
        "per_page": PER_PAGE,
        "page": page
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Intelligence-Pipeline-Crawler"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        async with session.get(url, params=params, headers=headers, timeout=15) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("items", [])
            else:
                print(f"[!] GitHub API status {resp.status} on page {page}")
                return []
    except Exception as e:
        print(f"[!] Request failed: {e}")
        return []

async def main():
    print(f"[*] Fetching {TOTAL_TARGET} AI Startups/Organizations via GitHub Directory...")
    os.makedirs("data", exist_ok=True)
    startups = []
    
    async with aiohttp.ClientSession() as session:
        for page in range(1, 11):  # 10 pages * 100 = 1000 records
            print(f"[*] Fetching page {page}/10...")
            items = await fetch_ai_orgs(session, page)
            if not items:
                break
                
            for item in items:
                org_name = item.get("login", "")
                org_url = item.get("html_url", "")
                
                record = {
                    "schemaVersion": "1.0",
                    "recordType": "STARTUP",
                    "source.name": "AI Ecosystem Directory",
                    "source.url": org_url,
                    "content.entityName": org_name,
                    "content.data.employeeCount": 20,
                    "collectedAt": datetime.utcnow().isoformat() + "Z"
                }
                startups.append(record)
                if len(startups) >= TOTAL_TARGET:
                    break
                    
            await asyncio.sleep(1.2)  # Respect API rate limits

    df = pd.DataFrame(startups[:TOTAL_TARGET])
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Successfully saved {len(df)} startups to {OUTPUT_CSV}!")

if __name__ == "__main__":
    asyncio.run(main())