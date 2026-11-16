"""Fetch the real HKU service pages that make up the navigator's corpus.

Replaces the earlier hand-written sample pages with pages fetched live from the
official HKU sites, so every answer the bot gives traces back to a real URL.

Usage:
    python3 scrape.py            # fetch, extract, write data/pages + sources.json
    python3 scrape.py --check    # fetch and report only, write nothing

Design notes:
- stdlib only (urllib + html.parser) so a fresh clone needs no extra packages
  beyond requirements.txt.
- Text extraction prefers <main>/<article> so site navigation and footers do
  not pollute retrieval.
- Polite: sequential requests, short delay, retries with backoff, and pages
  under MIN_CHARS are dropped rather than padded.
"""
import argparse
import html
import json
import os
import re
import sys
import time
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import config

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

MIN_CHARS = 400
MAX_CHARS = 6000
DELAY = 1.0
RETRIES = 3

# Curated seeds: (page id, human title, url). One entry per student-service
# topic the navigator is supposed to answer.
SEEDS = [
    ("library_spaces", "HKU Libraries - Booking a Space or Study Room",
     "https://lib.hku.hk/general/e-form/book-a-space.html"),
    ("library_services", "HKU Libraries - Services Overview",
     "https://lib.hku.hk/"),

    ("cedars_financial", "CEDARS - Financial Assistance",
     "https://www.cedars.hku.hk/ssi/finances"),
    ("cedars_ssi", "CEDARS - Student Support and Inclusion",
     "https://www.cedars.hku.hk/ssi"),
    ("cedars_amenities", "CEDARS - Student Amenities",
     "https://www.cedars.hku.hk/ssi/student-amenities"),
    ("cedars_mind_wellbeing", "CEDARS - Mind and Wellbeing",
     "https://www.cedars.hku.hk/mwb"),
    ("cedars_careers", "CEDARS - Careers and Employability",
     "https://www.cedars.hku.hk/careers"),
    ("cedars_career_coaching", "CEDARS - One-on-One Career Coaching",
     "https://www.cedars.hku.hk/careers/one-on-one-career-coaching"),
    ("cedars_overseas_emergency", "CEDARS - Overseas Emergency Assistance",
     "https://www.cedars.hku.hk/overseasemergencyassistance"),
    ("cedars_cymcc", "CEDARS - Chong Yuet Ming Cultural Centre",
     "https://www.cedars.hku.hk/CYMCC"),

    ("uhs_overview", "University Health Service - Overview",
     "https://www.uhs.hku.hk/"),
    ("uhs_medical", "University Health Service - Medical Services",
     "https://www.uhs.hku.hk/medical/"),
    ("uhs_charges", "University Health Service - Medical Charges",
     "https://www.uhs.hku.hk/medical-charges/"),
    ("uhs_dental", "University Health Service - Dental Appointments",
     "https://www.uhs.hku.hk/dental-appointment/"),
    ("uhs_emergency", "University Health Service - Emergency Services",
     "https://www.uhs.hku.hk/emergency-services/"),
    ("uhs_nursing", "University Health Service - Nursing Services",
     "https://www.uhs.hku.hk/nursing-services/"),
    ("uhs_eligibility", "University Health Service - Eligibility",
     "https://www.uhs.hku.hk/eligibility/"),
    ("uhs_immunization", "University Health Service - Immunization",
     "https://www.uhs.hku.hk/immunization/"),
    ("uhs_dispensary", "University Health Service - Dispensary",
     "https://www.uhs.hku.hk/dispensary/"),

    ("its_wifi", "ITS - HKU Wi-Fi",
     "https://its.hku.hk/services/network-connectivity/wifi/"),
    ("its_vpn", "ITS - HKU VPN",
     "https://its.hku.hk/services/network-connectivity/hkuvpn/"),
    ("its_moodle", "ITS - Moodle (Learning Management System)",
     "https://its.hku.hk/services/teaching-learning/moodle/"),
    ("its_portal_account", "ITS - HKU Portal Account",
     "https://its.hku.hk/services/accounts-mfa/hku-portal-account/"),
    ("its_email", "ITS - Email and Calendar",
     "https://its.hku.hk/services/email-communications/email-and-calendar/"),
    ("its_service_desk", "ITS - Service Desk",
     "https://its.hku.hk/service-desk/"),
    ("its_genai", "ITS - HKU GenAI Platform",
     "https://its.hku.hk/services/ai-as-a-service/hku-genai/"),

    ("hku_current_students", "HKU - Current Students",
     "https://www.hku.hk/en/current-students"),
    ("hku_campus_facilities", "HKU - Campus Facilities",
     "https://www.hku.hk/en/campus-life/campus-facilities"),
    ("hku_fees_scholarships", "HKU - Tuition Fees and Scholarships",
     "https://www.hku.hk/en/admission-aid/tuition-fee-scholarships"),
    ("hku_admission_aid", "HKU - Admissions and Financial Aid",
     "https://www.hku.hk/en/admission-aid"),
    ("its_services_overview", "ITS - Services Overview",
     "https://its.hku.hk/services-main/"),
    ("cedars_mtr_travel", "CEDARS - MTR Student Travel Scheme",
     "https://www.cedars.hku.hk/ssi/mtrstudenttravel"),
    ("lib_collection_development", "HKU Libraries - Collection Development",
     "https://lib.hku.hk/cdd/index.html"),
]

SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside",
             "form", "button", "svg", "iframe"}
BLOCK_TAGS = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6",
              "tr", "section", "article", "main", "td", "blockquote", "pre"}


class Extractor(HTMLParser):
    """Collect visible text, preferring <main>/<article> when present."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.chunks = []
        self.main_chunks = []
        self.has_main = False

    def handle_starttag(self, tag, attrs):
        if tag in ("main", "article"):
            self.has_main = True
        if tag in BLOCK_TAGS:
            self._emit("\n")
        if tag not in ("br", "img", "meta", "link", "input", "hr"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS:
            self._emit("\n")
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if any(t in SKIP_TAGS for t in self.stack):
            return
        if not data.strip():
            self._emit(" ")
            return
        self._emit(data)
        if any(t in ("main", "article") for t in self.stack):
            self.main_chunks.append(data)

    def _emit(self, s):
        self.chunks.append(s)

    def text(self):
        raw = "".join(self.chunks)
        if self.has_main and len("".join(self.main_chunks)) > MIN_CHARS:
            raw = " ".join(self.main_chunks)
        return clean(raw)


def clean(raw):
    raw = html.unescape(raw)
    raw = raw.replace("\u00a0", " ").replace("\u200b", "")
    raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
    lines = []
    for line in raw.split("\n"):
        line = line.strip()
        # Drop pure-navigation noise: very short fragments without punctuation.
        if len(line) < 3:
            continue
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _ssl_context():
    """Use certifi's CA bundle when available (macOS python.org builds lack one)."""
    import ssl

    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _get(url, timeout):
    """Prefer requests (better TLS + header handling); fall back to urllib."""
    try:
        import requests
    except ImportError:
        return None
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text, resp.url


def fetch(url, timeout=25):
    last = None
    ctx = _ssl_context()
    for attempt in range(RETRIES):
        try:
            got = _get(url, timeout)
            if got is not None:
                return got
            req = Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
            with urlopen(req, timeout=timeout, context=ctx) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read().decode(charset, errors="replace"), resp.geturl()
        except Exception as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise last


def prune_boilerplate(pages, min_pages=3, short=70):
    """Drop site-wide menu lines that survive extraction.

    A line under `short` characters that shows up on `min_pages` or more pages
    is site navigation (CEDARS repeats its whole menu inside <main>), not
    content, and it dilutes BM25 scores.
    """
    counts = {}
    for _, _, _, text in pages:
        for line in set(text.splitlines()):
            if len(line) < short:
                counts[line] = counts.get(line, 0) + 1
    nav = {line for line, n in counts.items() if n >= min_pages}

    pruned = []
    for page_id, title, url, text in pages:
        kept = [line for line in text.splitlines() if line not in nav]
        # Trim leading navigation remnants up to the first substantial paragraph.
        while kept and len(kept[0]) < 60:
            kept.pop(0)
        pruned.append((page_id, title, url, "\n".join(kept).strip()))
    return pruned


def dedupe_key(text):
    return re.sub(r"\W+", "", text.lower())[:2000]


def build(check_only=False):
    existing = {}
    if os.path.isdir(config.PAGES_DIR):
        for name in os.listdir(config.PAGES_DIR):
            if name.endswith(".txt"):
                path = os.path.join(config.PAGES_DIR, name)
                with open(path, encoding="utf-8") as fh:
                    existing[dedupe_key(fh.read())] = name

    collected, skipped = [], []
    for page_id, title, url in SEEDS:
        try:
            page, final_url = fetch(url)
        except Exception as exc:  # network/HTTP failure: record and move on
            skipped.append((page_id, f"fetch failed: {type(exc).__name__}"))
            print(f"[SKIP] {page_id:<26} fetch failed: {type(exc).__name__}")
            continue

        parser = Extractor()
        parser.feed(page)
        text = clean(parser.text())[:MAX_CHARS]

        if len(text) < MIN_CHARS:
            skipped.append((page_id, f"too little text ({len(text)} chars)"))
            print(f"[SKIP] {page_id:<26} too little text ({len(text)} chars)")
            continue

        key = dedupe_key(text)
        if key in existing and existing[key] != f"{page_id}.txt":
            skipped.append((page_id, f"duplicate of {existing[key]}"))
            print(f"[SKIP] {page_id:<26} duplicate of {existing[key]}")
            continue

        collected.append((page_id, title, final_url, text))
        print(f"[OK]   {page_id:<26} {len(text):>5} chars  {final_url}")
        time.sleep(DELAY)

    sources = []
    if not check_only and collected:
        collected = prune_boilerplate(collected)
        os.makedirs(config.PAGES_DIR, exist_ok=True)
        for page_id, title, final_url, text in collected:
            with open(os.path.join(config.PAGES_DIR, f"{page_id}.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(text)
            sources.append({"id": page_id, "title": title, "url": final_url,
                            "file": f"{page_id}.txt"})
    else:
        sources = [{"id": i, "title": t, "url": u, "file": f"{i}.txt"}
                   for i, t, u, _ in collected]

    if check_only:
        print(f"\n{len(sources)} readable, {len(skipped)} skipped (dry run).")
        return sources, skipped

    with open(config.SOURCES_JSON, "w", encoding="utf-8") as fh:
        json.dump(sources, fh, indent=2, ensure_ascii=False)
    print(f"\nWrote {len(sources)} pages -> {config.PAGES_DIR}")
    print(f"Wrote manifest -> {config.SOURCES_JSON}")
    if skipped:
        print(f"Skipped {len(skipped)}: " + ", ".join(f"{i}" for i, _ in skipped))
    return sources, skipped


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    args = ap.parse_args()
    got, miss = build(check_only=args.check)
    sys.exit(0 if got else 1)
