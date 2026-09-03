 FrontierAtlas: AI Intelligence Pipeline

A resilient, fault-tolerant data intelligence engine designed to collect, enrich, normalize, and resolve entities across the global AI ecosystem.


 **Research Papers:** Ingests 1,000+ AI papers with live enriched GitHub repository stars.
-**Startups & Products:** Catalogs 1,000 AI organizations and 1,000 products with mapped pricing tiers.
 **24-Hour Signal Ingestion:** Captures fresh AI news and job postings with strict UTC ISO-8601 timestamps.
 **Multi-Tier LLM Fallback:** Automatic resilient failover (Gemini -> Groq) with exponential backoff handling rate limits (429) and token limits (413).
 **Entity Resolution Engine:** RapidFuzz token sorting and rule-based normalization against canonical industry entities.

```text
├── data/
│   ├── research_papers.csv
│   ├── startups.csv
│   ├── products.csv
│   ├── news.csv
│   ├── jobs.csv
│   └── entity_mapping_log.csv
├── src/
│   ├── scrape_papers.py
│   ├── fetch_stars.py
│   ├── scrape_startups.py
│   ├── scrape_products.py
│   ├── scrape_signals.py
│   ├── entity_resolution.py
│   └── llm_orchestrator.py
├── requirements.txt
└── README.md