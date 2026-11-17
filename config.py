"""Central configuration for the HKU Student Service Information Navigator.

Loads credentials and settings from a local .env file (gitignored).
Never hardcode the API key in source.

Retrieval uses lexical (BM25) search over the curated index, so NO embedding
model is required. Generation uses a flash chat model on the sponsored
Alibaba Cloud Bailian endpoint.
"""
import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BAILIAN_API_KEY", "")
BASE_URL = os.getenv(
    "BAILIAN_BASE_URL",
    "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)
# Flash model available on the sponsored plan. Change if the Ed post lists another.
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen3.8-flash")

# config.py lives in the project root (code/), so data/ is one level below it.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PAGES_DIR = os.path.join(DATA_DIR, "pages")
SOURCES_JSON = os.path.join(DATA_DIR, "sources.json")
INDEX_PATH = os.path.join(DATA_DIR, "index.pkl")

def require_api_key():
    """Return the key, or explain how to set it.

    Deliberately not checked at import time: the offline parts of this project
    (indexing, retrieval evaluation, the unit tests) must run on a fresh clone
    with no credentials, so a marker can verify the pipeline without a key.
    """
    if not API_KEY or API_KEY == "your_group_api_key_here":
        raise RuntimeError(
            "BAILIAN_API_KEY is not set. Copy .env.example to .env and add your "
            "group key. Offline checks need no key: python ingest.py, "
            "python evaluate.py --no-llm, python -m unittest discover -s tests"
        )
    return API_KEY
