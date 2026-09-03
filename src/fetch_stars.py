import asyncio
import aiohttp
import pandas as pd
import re
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
INPUT_CSV = "data/research_papers.csv"
OUTPUT_CSV = "data/research_papers.csv"
CONCURRENCY_LIMIT = 10

def parse_repo_owner_name(url: str):
    if not url or pd.isna(url):
        return None
    match = re.search(r"github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)", str(url))
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None

async def fetch_github_stars(session: aiohttp.ClientSession, repo_path: str, sem: asyncio.Semaphore) -> int:
    if not repo_path:
        return 0
    
    url = f"https://api.github.com/repos/{repo_path}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Intelligence-Pipeline-Crawler"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async with sem:
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("stargazers_count", 0)
                elif resp.status == 404:
                    return 0
                elif resp.status in (403, 429):
                    print(f"[!] Rate limit hit for {repo_path}. Defaulting to 0.")
                    return 0
                return 0
        except Exception:
            return 0

async def main():
    if not os.path.exists(INPUT_CSV):
        print(f"[!] Error: {INPUT_CSV} nahi mila. Pehle scrape_papers.py run karein.")
        return

    print(f"[*] Reading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)

    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, row in df.iterrows():
            repo_path = parse_repo_owner_name(row.get("content.github_url", ""))
            if repo_path:
                tasks.append((idx, fetch_github_stars(session, repo_path, sem)))

        print(f"[*] Fetching live stars for {len(tasks)} GitHub repos...")
        results = await asyncio.gather(*(task[1] for task in tasks))

        for (idx, _), stars in zip(tasks, results):
            df.at[idx, "content.github_stars"] = stars

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[✓] Completed! Updated {OUTPUT_CSV} with live GitHub stars.")

if __name__ == "__main__":
    asyncio.run(main())