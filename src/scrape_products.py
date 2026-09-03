import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TOTAL_TARGET = 1000
OUTPUT_CSV = "data/products.csv"
PER_PAGE = 100

def infer_pricing_model(description: str, license_info: dict) -> str:
    desc = (description or "").lower()
    if any(word in desc for word in ["enterprise", "commercial", "saas", "b2b"]):
        return "ENTERPRISE"
    elif any(word in desc for word in ["pro", "paid", "subscription", "credits"]):
        return "PAID"
    elif any(word in desc for word in ["freemium", "free tier", "cloud"]):
        return "FREEMIUM"
    return "FREE"

async def fetch_ai_products(session: aiohttp.ClientSession, page: int):
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "topic:ai topic:llm stars:>50",
        "sort": "stars",
        "order": "desc",
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
        print(f"[!] Network error on page {page}: {e}")
        return []

async def main():
    print(f"[*] Fetching {TOTAL_TARGET} AI Products...")
    os.makedirs("data", exist_ok=True)
    products = []

    async with aiohttp.ClientSession() as session:
        for page in range(1, 11):  # 10 pages * 100 = 1000 products
            print(f"[*] Fetching page {page}/10...")
            items = await fetch_ai_products(session, page)
            if not items:
                break

            for item in items:
                prod_name = item.get("name", "")
                owner_name = item.get("owner", {}).get("login", "")
                url = item.get("html_url", "")
                description = item.get("description", "")
                license_info = item.get("license") or {}

                pricing = infer_pricing_model(description, license_info)

                record = {
                    "schemaVersion": "1.0",
                    "recordType": "PRODUCT",
                    "source.name": "AI Product Index",
                    "source.url": url,
                    "content.startupName": owner_name,
                    "content.pricingModel": pricing,
                    "collectedAt": datetime.utcnow().isoformat() + "Z"
                }
                products.append(record)

                if len(products) >= TOTAL_TARGET:
                    break

            await asyncio.sleep(1.2)

    df = pd.DataFrame(products[:TOTAL_TARGET])
    df.to_csv(OUTPUT_CSV, index=False)
    print(f" Successfully saved {len(df)} products to {OUTPUT_CSV}!")

if __name__ == "__main__":
    asyncio.run(main())
