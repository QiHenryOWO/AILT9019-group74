"""End-to-end pipeline: refusal guard -> BM25 retrieve -> grounded answer.

Design notes (per the proposal's "does not" boundary):
- Refuses medical / mental-health / legal / emergency advice and returns
  official contacts only (no triage).
- Answers are grounded in retrieved context; the LLM must cite sources and
  must say when it lacks information instead of guessing.
"""
from . import index as index_mod
from . import refusal as refusal_mod
from .client import get_client
from .index import retrieve
import config

MAX_CONTEXT_CHARS = 1500

SYSTEM_PROMPT = (
    "You are the HKU Student Service Information Navigator. "
    "Answer the student's question using ONLY the provided context excerpts. "
    "Every factual claim must be grounded in the context. "
    "If the context does not contain the answer, say you do not have that "
    "information and point the student to the relevant HKU office using its URL. "
    "Never give medical, mental-health, legal, or emergency advice. "
    "At the end, list the sources you used as 'Sources:' followed by each "
    "title and URL. Keep the answer concise and friendly."
)

def answer(query):
    refused, cats = refusal_mod.check_refusal(query)
    if refused:
        return {
            "query": query,
            "answer": refusal_mod.HOTLINE,
            "sources": [],
            "refused": True,
            "categories": cats,
        }

    index = index_mod.load_index()
    top = retrieve(query, index, top_k=3)
    if top:
        # Cap each passage: a full page dilutes the answer and slows generation
        # (measured median 10.7s with whole pages, see report section 3).
        context = "\n\n".join(
            f"[Source: {d['title']} | {d['url']}]\n{d['text'][:MAX_CONTEXT_CHARS]}"
            for d in top
        )
    else:
        context = "(No relevant HKU service information was found in the index.)"

    client = get_client()
    user_msg = f"Context:\n{context}\n\nQuestion: {query}"
    resp = client.chat.completions.create(
        model=config.CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=400,
    )
    text = resp.choices[0].message.content

    return {
        "query": query,
        "answer": text,
        "sources": [{"title": d["title"], "url": d["url"]} for d in top],
        "refused": False,
        "categories": [],
    }
