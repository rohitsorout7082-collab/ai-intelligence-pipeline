import asyncio
import aiohttp
import xml.etree.ElementTree as ET
import re
import pandas as pd
from datetime import datetime

ARXIV_URL = "http://export.arxiv.org/api/query"
TOTAL_PAPERS = 1000
BATCH_SIZE = 100

def extract_github_url(text: str) -> str:
    if not text:
        return ""
    match = re.search(r"https?://github\.com/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)", text)
    if match:
        return f"https://github.com/{match.group(1)}/{match.group(2)}"
    return ""

async def fetch_batch(session: aiohttp.ClientSession, start: int, max_results: int):
    params = {
        "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    async with session.get(ARXIV_URL, params=params) as resp:
        if resp.status == 200:
            return await resp.text()
        return None

def parse_arxiv_xml(xml_data: str):
    root = ET.fromstring(xml_data)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom"
    }
    
    records = []
    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        published = entry.find("atom:published", ns).text.strip()
        
        authors = [a.find("atom:name", ns).text.strip() for a in entry.findall("atom:author", ns)]
        paper_url = entry.find("atom:id", ns).text.strip()
        
        github_url = extract_github_url(summary)
        
        records.append({
            "schemaVersion": "1.0",
            "recordType": "RESEARCH_PAPER",
            "content.title": title,
            "content.authors": ", ".join(authors),
            "content.paper_url": paper_url,
            "content.github_url": github_url,
            "content.github_stars": 0,
            "content.published_date": published,
            "collectedAt": datetime.utcnow().isoformat() + "Z"
        })
    return records

async def main():
    print(f"[*] Starting collection of {TOTAL_PAPERS} AI Research Papers...")
    all_papers = []
    
    async with aiohttp.ClientSession() as session:
        for start_idx in range(0, TOTAL_PAPERS, BATCH_SIZE):
            print(f"[*] Fetching records {start_idx} to {start_idx + BATCH_SIZE}...")
            xml_text = await fetch_batch(session, start_idx, BATCH_SIZE)
            if xml_text:
                batch_records = parse_arxiv_xml(xml_text)
                all_papers.extend(batch_records)
            await asyncio.sleep(2)  # Respect ArXiv rate limits
            
    df = pd.DataFrame(all_papers[:TOTAL_PAPERS])
    output_path = "data/research_papers.csv"
    df.to_csv(output_path, index=False)
    print(f" Successfully collected and saved {len(df)} papers to {output_path}!")

if __name__ == "__main__":
    asyncio.run(main())
