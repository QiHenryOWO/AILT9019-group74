"""Build and load the BM25 retrieval index over the curated corpus.

No embedding API is used: retrieval is lexical (BM25), which is fast, offline,
and good enough for a small curated set of HKU service pages.

Each stored doc record: {tokens, tf, len, source_id, title, url, text}
The index also stores idf, avgdl, and N.
"""
import json
import math
import os
import pickle
import re

import config

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tf(tokens):
    counts = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    return counts

K1, B = 1.5, 0.75
TITLE_WEIGHT = 2.0  # title matches count double the body field


def tokenize(text):
    return _TOKEN_RE.findall((text or "").lower())


def build_index():
    with open(config.SOURCES_JSON, "r", encoding="utf-8") as f:
        sources = json.load(f)

    docs = []
    df = {}
    for s in sources:
        path = os.path.join(config.PAGES_DIR, s["file"])
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        # Drop the sample-disclaimer header line for cleaner matching.
        if text.startswith("[SAMPLE"):
            text = text.split("\n", 1)[-1]
        tokens = tokenize(text)
        tf = _tf(tokens)
        docs.append(
            {
                "tokens": tokens,
                "tf": tf,
                "len": len(tokens),
                "source_id": s["id"],
                "title": s["title"],
                "title_tokens": tokenize(s["title"]),
                "title_tf": _tf(tokenize(s["title"])),
                "url": s["url"],
                "text": text,
            }
        )
        for t in tf:
            df[t] = df.get(t, 0) + 1

    n = len(docs)
    avgdl = sum(d["len"] for d in docs) / max(n, 1)
    idf = {
        t: math.log(1 + (n - dft + 0.5) / (dft + 0.5)) for t, dft in df.items()
    }

    index = {"docs": docs, "idf": idf, "avgdl": avgdl, "N": n}
    with open(config.INDEX_PATH, "wb") as f:
        pickle.dump(index, f)
    return index


def load_index():
    if not os.path.exists(config.INDEX_PATH):
        return build_index()
    with open(config.INDEX_PATH, "rb") as f:
        return pickle.load(f)


def _bm25(tf, dl, avgdl, idf, terms):
    score = 0.0
    for t in terms:
        f = tf.get(t, 0)
        if f:
            score += idf.get(t, 0.0) * (f * (K1 + 1)) / (
                f + K1 * (1 - B + B * dl / avgdl)
            )
    return score


def retrieve(query, index, top_k=3, title_weight=TITLE_WEIGHT):
    """BM25 over body text plus a title boost; return top_k docs.

    The curated titles ("CEDARS - Financial Assistance") carry the topic the
    question is about, while body text is diluted by page furniture that
    survives HTML extraction. Scoring the title field separately and adding it
    with TITLE_WEIGHT made retrieval noticeably more precise than a single
    flat field (see the retrieval table in the report).
    """
    qtokens = tokenize(query)
    if not qtokens:
        return []
    terms = set(qtokens)
    idf = index["idf"]
    avgdl = index["avgdl"]
    ranked = []
    for d in index["docs"]:
        body = _bm25(d["tf"], d["len"], avgdl, idf, terms)
        title_tokens = d.get("title_tokens") or tokenize(d.get("title", ""))
        title_tf = d.get("title_tf")
        if title_tf is None:
            title_tf = {}
            for t in title_tokens:
                title_tf[t] = title_tf.get(t, 0) + 1
        title = title_weight * _bm25(
            title_tf, max(len(title_tokens), 1), avgdl, idf, terms
        )
        score = body + title
        if score > 0:
            ranked.append((score, d))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in ranked[:top_k]]
