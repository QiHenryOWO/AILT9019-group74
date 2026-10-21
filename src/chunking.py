"""Simple character-window chunking with overlap."""


def chunk_text(text, size=500, overlap=80):
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == len(text):
            break
        start = end - overlap
    return chunks
