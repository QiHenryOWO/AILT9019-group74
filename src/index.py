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

K1, B = 1.5, 0.75


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
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        docs.append(
            {
                "tokens": tokens,
                "tf": tf,
                "len": len(tokens),
                "source_id": s["id"],
                "title": s["title"],
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


def retrieve(query, index, top_k=3):
    """BM25 scoring of all docs against the query; return top_k docs."""
    qtokens = tokenize(query)
    if not qtokens:
        return []
    idf = index["idf"]
    avgdl = index["avgdl"]
    ranked = []
    for d in index["docs"]:
        score = 0.0
        tf = d["tf"]
        dl = d["len"]
        for t in set(qtokens):
            if t in tf:
                f = tf[t]
                score += idf.get(t, 0.0) * (f * (K1 + 1)) / (
                    f + K1 * (1 - B + B * dl / avgdl)
                )
        if score > 0:
            ranked.append((score, d))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in ranked[:top_k]]
