import math
from typing import List, Dict
from openai import OpenAI
from app.config.database import policy_vectors_collection
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"

client = OpenAI(api_key=OPENAI_API_KEY)

def chunk_markdown(md: str, max_chars: int = 1200, overlap: int = 120) -> List[str]:
    if len(md) <= max_chars:
        return [md]
    chunks = []
    i = 0
    while i < len(md):
        chunk = md[i:i+max_chars]
        chunks.append(chunk)
        i += max_chars - overlap
    return chunks

async def index_policies(site_url: str, policies: List[Dict]):
    for p in policies:
        chunks = chunk_markdown(p["content"])
        for idx, ch in enumerate(chunks):
            emb = client.embeddings.create(model=EMBEDDING_MODEL, input=ch).data[0].embedding
            doc = {
                "site": site_url,
                "source_url": p["url"],
                "policy_type": p["policy_type"],
                "section": idx,
                "text": ch,
                "vector": emb,
            }
            await policy_vectors_collection.update_one(
                {"site": site_url, "source_url": p["url"], "section": idx},
                {"$set": doc},
                upsert=True,
            )