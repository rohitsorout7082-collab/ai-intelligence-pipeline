import os
import time
import json
import asyncio
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class StartupSchema(BaseModel):
    entityName: str
    employeeCount: Optional[int] = 0
    pricingModel: Optional[str] = "FREE"

def chunk_text(text: str, max_chars: int = 4000) -> str:
    return text[:max_chars] if len(text) > max_chars else text

async def call_gemini_flash(payload: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")
    
    from google import genai
    client = genai.Client(api_key=api_key)
    prompt = f"Extract startup entity details in strict JSON (keys: entityName, employeeCount, pricingModel) from text:\n{payload}"
    
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt
    )
    return response.text

async def call_groq_fallback(payload: str):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")
        
    from groq import Groq
    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Extract entity details in strict JSON format."},
            {"role": "user", "content": payload}
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

async def extract_with_resilient_fallback(raw_html: str, retries: int = 2):
    safe_text = chunk_text(raw_html)
    backoff = 1.0

    for attempt in range(retries):
       
        try:
            return await call_gemini_flash(safe_text)
        except Exception as e:
            print(f"[!] Tier 1 (Gemini) failed: {e}. Falling back to Tier 2...")

        
        try:
            return await call_groq_fallback(safe_text)
        except Exception as e:
            print(f"[!] Tier 2 (Groq) failed: {e}")

        await asyncio.sleep(backoff)
        backoff *= 2.0

    return json.dumps({"status": "failed_all_tiers"})

if __name__ == "__main__":
    test_html = "<div><h1>OpenAI</h1><p>AI research organization with 500+ employees.</p></div>"
    print("[*] Testing Multi-Tier LLM Orchestrator...")
    result = asyncio.run(extract_with_resilient_fallback(test_html))
    print(" Extraction Pipeline Output:")
    print(result)