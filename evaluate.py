"""Evaluate the navigator on the 15 fixed test questions.

Two different things are measured, because they fail for different reasons:

1. Behaviour - does the system do what the question expects?
   "rag"    -> answered from retrieved context (no refusal)
   "refuse" -> the refusal guard fired
2. Retrieval - for questions that should be answered from a specific page,
   did the correct page come back as the top hit? Questions with no dedicated
   page yet carry "expect_source": null and are excluded from this metric
   rather than scored against a guess.

The retrieval metric is also reported for a flat BM25 baseline (no title
boost), so the effect of the field weighting is visible in one run.

Usage:
    python evaluate.py              # behaviour + retrieval, calls the LLM
    python evaluate.py --no-llm     # retrieval only, no API key needed
    python evaluate.py --quiet      # summary only
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

TARGET = ">= 12 / 15"


def load_questions():
    with open(os.path.join(HERE, "test_questions.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def retrieval_scores(questions):
    """Top-1 accuracy of the submitted retriever vs a flat BM25 baseline."""
    from src import index as index_mod

    index = index_mod.load_index()
    rows, hits, base_hits, scored = [], 0, 0, 0
    for item in questions:
        source = item.get("expect_source")
        if not source:
            continue
        scored += 1
        top = index_mod.retrieve(item["question"], index, top_k=1)
        got = top[0]["source_id"] if top else None
        base = index_mod.retrieve(
            item["question"], index, top_k=1, title_weight=0.0
        )
        base_got = base[0]["source_id"] if base else None
        hits += got == source
        base_hits += base_got == source
        rows.append((item["question"], source, got, base_got))
    return rows, hits, base_hits, scored


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-llm", action="store_true",
                    help="skip generation; measure retrieval only")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    args = ap.parse_args()

    questions = load_questions()
    log = (lambda *a: None) if args.quiet else print

    rows, hits, base_hits, scored = retrieval_scores(questions)
    log("Retrieval top-1 (questions with a known target page):")
    log(f"{'question':<60} {'expected':<24} {'got':<24} {'flat BM25':<24}")
    for question, expected, got, base in rows:
        mark = "ok " if got == expected else "MISS"
        base_mark = "ok " if base == expected else "miss"
        log(f"{question[:58]:<60} {expected:<24} {str(got):<24} {base_mark} {base}")
    log(f"\nRetrieval top-1: {hits}/{scored} with title boost, "
        f"{base_hits}/{scored} flat BM25.\n")

    if args.no_llm:
        print(f"Retrieval top-1 {hits}/{scored} (title boost) vs "
              f"{base_hits}/{scored} (flat BM25). Generation not run.")
        return

    from src import pipeline as pipeline_mod

    passed = 0
    for item in questions:
        q = item["question"]
        expected = item["expected"]
        try:
            res = pipeline_mod.answer(q)
            got = "refuse" if res.get("refused") else "rag"
            ok = got == expected
            passed += ok
            log(f"[{'PASS' if ok else 'FAIL'}] expected={expected} got={got} | {q}")
        except Exception as exc:  # an API error must not hide the other results
            log(f"[ERROR] expected={expected} | {q} -> {exc}")

    print(f"Behaviour: {passed}/{len(questions)} "
          f"(target {TARGET}); retrieval top-1 {hits}/{scored}.")


if __name__ == "__main__":
    main()
