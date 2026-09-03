import asyncio
import aiohttp
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
from email.utils import parsedate_to_datetime

NEWS_OUTPUT_CSV = "data/news.csv"
JOBS_OUTPUT_CSV = "data/jobs.csv"


NEWS_FEEDS = [
    {"source": "MIT Technology Review AI", "url": "https://www.technologyreview.com/feed/"},
    {"source": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"source": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"source": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"source": "Wired AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss"}
]


JOB_FEEDS = [
    {"source": "HackerNews Who is Hiring", "url": "https://news.ycombinator.com/rss"},
    {"source": "WeWorkRemotely AI", "url": "https://weworkremotely.com/categories/machine-learning.rss"},
    {"source": "Remotive Tech", "url": "https://remotive.com/job/rss"}
]

def parse_rfc_date(date_str: str) -> datetime:
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except Exception:
        return None

async def fetch_feed(session: aiohttp.ClientSession, source_meta: dict):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Signal-Crawler"}
    try:
        async with session.get(source_meta["url"], headers=headers, timeout=15) as resp:
            if resp.status == 200:
                text = await resp.text()
                return source_meta["source"], text
            return source_meta["source"], None
    except Exception as e:
        print(f"[!] Error fetching {source_meta['source']}: {e}")
        return source_meta["source"], None

def process_news_xml(source_name: str, xml_content: str, cutoff_time: datetime):
    records = []
    if not xml_content:
        return records
    try:
        root = ET.fromstring(xml_content)
    except Exception:
        return records

    
    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date_str = item.findtext("pubDate", "")
        dt = parse_rfc_date(pub_date_str)

        if dt and dt >= cutoff_time:
            records.append({
                "schemaVersion": "1.0",
                "recordType": "NEWS",
                "source.name": source_name,
                "source.url": link,
                "content.title": title,
                "content.published_date": dt.isoformat(),
                "collectedAt": datetime.now(timezone.utc).isoformat()
            })
    return records

def process_job_xml(source_name: str, xml_content: str, cutoff_time: datetime):
    records = []
    if not xml_content:
        return records
    try:
        root = ET.fromstring(xml_content)
    except Exception:
        return records

    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date_str = item.findtext("pubDate", "")
        dt = parse_rfc_date(pub_date_str)

     
        if dt and dt >= cutoff_time:
            is_ai_related = any(k in title.lower() for k in ["ai", "machine learning", "engineer", "data", "deep learning"])
            if is_ai_related:
                company = title.split("is hiring")[0].strip() if "is hiring" in title else source_name
                records.append({
                    "schemaVersion": "1.0",
                    "recordType": "JOB",
                    "content.company": company[:50],
                    "content.date": dt.isoformat(),
                    "content.is_remote": True,
                    "content.role_family": "Engineering",
                    "source.url": link,
                    "collectedAt": datetime.now(timezone.utc).isoformat()
                })
    return records

async def main():
    print("[*] Starting 24-Hour Fresh Signal Ingestion (News & Jobs)...")
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

    all_news = []
    all_jobs = []

    async with aiohttp.ClientSession() as session:
      
        news_tasks = [fetch_feed(session, meta) for meta in NEWS_FEEDS]
        news_results = await asyncio.gather(*news_tasks)
        for src_name, content in news_results:
            if content:
                news_items = process_news_xml(src_name, content, cutoff_time)
                all_news.extend(news_items)

       
        job_tasks = [fetch_feed(session, meta) for meta in JOB_FEEDS]
        job_results = await asyncio.gather(*job_tasks)
        for src_name, content in job_results:
            if content:
                job_items = process_job_xml(src_name, content, cutoff_time)
                all_jobs.extend(job_items)

    os.makedirs("data", exist_ok=True)
    pd.DataFrame(all_news).to_csv(NEWS_OUTPUT_CSV, index=False)
    pd.DataFrame(all_jobs).to_csv(JOBS_OUTPUT_CSV, index=False)
    print(f"Successfully captured {len(all_news)} fresh news articles -> {NEWS_OUTPUT_CSV}")
    print(f"Successfully captured {len(all_jobs)} fresh AI jobs -> {JOBS_OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(main())
