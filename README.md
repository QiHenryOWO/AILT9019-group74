# HKU Student Service Information Navigator

A Retrieval-Augmented Generation (RAG) tool that answers HKU students' questions
about campus services (library, CEDARS, UHS, IT, Careers, Registry, Moodle, ...)
using a curated index of public HKU service pages. Answers are **grounded in
retrieved context with citations**, and the system **refuses medical, mental-health,
legal, and emergency advice** (returning official contacts only).

This is the must-have core workflow built for the AILT9019 Mid-Term Check.

## Group / API key note

- Sponsored by the course via Alibaba Cloud Bailian (Group 74). The group API key
  lives in `.env` (gitignored). **Never commit `.env` and never share the key
  outside the group.**
- The sponsored plan exposes **chat models only (flash models)** and **no embedding
  model**, so retrieval uses **lexical BM25 search** instead of vector embeddings.
  This keeps the pipeline dependency-light and fully offline for retrieval.

## Architecture

```
question
  -> refusal guard (rule-based)          -> if flagged: return official contacts
  -> BM25 retrieve top-k chunks          (offline, no API)
  -> flash LLM generates grounded answer -> answer + cited Sources
```

- `src/index.py`   – build/load the BM25 index over `data/pages/*.txt`
- `src/refusal.py` – keyword guard for medical / mental-health / legal / emergency
- `src/pipeline.py`– orchestrates refusal -> retrieve -> generate
- `src/client.py` – Alibaba Cloud Bailian OpenAI-compatible client
- `ingest.py`      – build the index (offline)
- `app.py`         – single-question demo (used for the 1-minute recording)
- `evaluate.py`    – run the 15 test questions, report pass count
- `test_questions.json` – 10 RAG questions + 5 refusal questions

## Setup

Requires Python 3.10+.

```bash
pip install -r requirements.txt
cp .env.example .env        # then make sure BAILIAN_API_KEY is set (see note below)
```

> The repo's local `.env` already contains the group key, but it is gitignored so
> it will never be pushed. If you clone this elsewhere, copy `.env.example` to
> `.env` and paste the group key from the teaching-team email.

## Build the index and run

```bash
python ingest.py                       # builds data/index.pkl (offline, fast)
python app.py "How do I book a group study room at the library?"
python evaluate.py                     # target: >= 12 / 15 passing
```

## Mid-Term Check demo (1-minute screen recording)

Record `app.py` running ONE test case, e.g.:

```bash
python app.py "How do I book a group study room at the library?"
```

This shows the full pipeline live: **input (question) -> processing (BM25 retrieve
+ LLM generate) -> output (grounded answer with cited Sources)**. A refusal case
(`python app.py "I feel like ending my life"`) is also a strong demo of the
"does not" safety boundary. Ensure no API key or personal data is visible on screen.

## Safety boundary ("does not")

The refusal guard returns official contacts only for medical / mental-health /
legal / emergency queries and never gives triage or advice. The LLM is also
instructed never to give such advice.

## Limitations (be honest in the status sheet)

- Queries are matched in **English**; Chinese/ mixed-language matching is a
  should-have extension (lexical tokenisation is English-oriented).
- The corpus in `data/pages/` is **curated SAMPLE text** with real HKU URLs. Before
  final submission, replace it with live-fetched content from the same pages.
- Retrieval is lexical (BM25), not semantic; for higher recall, a future version
  could add an external embedding model if the plan allows.

## File structure

```
code/
  config.py
  ingest.py          # build BM25 index
  app.py             # single-question demo
  evaluate.py        # 15-question evaluator
  requirements.txt
  README.md
  .env / .env.example
  .gitignore
  src/
    client.py        # Bailian client
    index.py         # BM25 index
    refusal.py       # safety guard
    pipeline.py      # end-to-end
  data/
    sources.json
    pages/*.txt      # curated corpus
    index.pkl        # generated (gitignored)
  test_questions.json
```

## Automated Tests

The project includes a unit test suite covering text chunking, safety refusal logic, and document retrieval. These tests help verify that individual components behave as expected and reduce the risk of regressions when the code is changed.

### What the Tests Cover

- **Text Chunking (`test_chunking.py`):** Tests that text is split into chunks correctly, including chunk overlap, short text, long text, empty input, and whitespace handling.
- **Safety Refusal (`test_refusal.py`):** Tests that medical, mental-health, legal, and emergency queries trigger the intended refusal behavior, while ordinary university service questions and emergency loan queries are not incorrectly refused.
- **Document Retrieval (`test_retrieval.py`):** Tests text tokenization, including lowercasing and punctuation removal, as well as retrieval relevance, document ranking, result limits, and handling of empty or unrelated queries.

### Running the Tests

Ensure the project dependencies are installed and the virtual environment is activated. From the project root, run:

```bash
python -m unittest discover -s tests -v
```

The command discovers and runs the tests in the `tests/` directory and displays the result of each test. A successful run ends with `OK`.

The unit tests are designed to check individual components and do not replace the end-to-end evaluation.

### Unit Tests vs. System Evaluation

The unit test suite checks specific component behaviors. The separate `evaluate.py` script evaluates the integrated system using the project's evaluation questions. Run it independently:

```bash
python evaluate.py
```

The project's evaluation target is at least 12 out of 15 questions passing. The unit test results do not automatically affect the evaluation score.

