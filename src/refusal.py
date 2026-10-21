"""Rule-based guard that refuses medical, mental-health, legal and emergency
advice. This is a simple, transparent keyword check; the LLM is also instructed
never to give such advice. The guard is intentionally conservative for
safety-critical categories."""

# Specific symptom / advice terms only (NOT the bare words "medical",
# "emergency" or "urgent", so that questions like "what services does UHS
# offer" or "emergency loan" are not wrongly refused).
KEYWORDS = {
    "medical": [
        "symptom", "pain", "fever", "sick", "ill", "diagnos", "medication",
        "prescription", "injury", "bleed", "chest pain", "headache", "covid",
        "virus", "medicine", "treatment", "cure",
    ],
    "mental_health": [
        "suicide", "kill myself", "self-harm", "harm myself", "depres",
        "anxiet", "panic", "crisis", "overwhelm", "end my life",
        "ending my life", "want to die", "no reason to live", "end it all",
    ],
    "legal": [
        "lawyer", "lawsuit", "sue", "legal advice", "contract law",
        "legal right", "court",
    ],
    "emergency": [
        "999", "ambulance", "unconscious", "faint", "dying",
    ],
}

HOTLINE = (
    "I am not able to give medical, mental-health, legal, or emergency advice.\n"
    "For an emergency, call 999 (Hong Kong) or go to the nearest A&E.\n"
    "For mental-health support, contact the UHS Counselling Service "
    "(https://www.uhs.hku.hk/counselling/) or the Samaritans 24h hotline at 2389 2222.\n"
    "For other health concerns, book a UHS appointment at https://www.uhs.hku.hk/.\n"
    "For legal matters, consult a qualified professional."
)


def check_refusal(query):
    q = (query or "").lower()
    hits = [cat for cat, kws in KEYWORDS.items() if any(k in q for k in kws)]
    return (len(hits) > 0, hits)
