"""Run the 15 test questions and report pass count.

A question passes if its actual behaviour matches the expected behaviour:
- "rag"   -> the pipeline answers using retrieved context (no refusal)
- "refuse"-> the refusal guard triggers

Target for the Mid-Term Check: >= 12 / 15 passing.

Usage:
    python evaluate.py
"""
import json
import os

from src import pipeline as pipeline_mod

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    with open(os.path.join(HERE, "test_questions.json"), "r", encoding="utf-8") as f:
        questions = json.load(f)

    passed = 0
    for item in questions:
        q = item["question"]
        expected = item["expected"]
        try:
            res = pipeline_mod.answer(q)
            got = "refuse" if res.get("refused") else "rag"
            ok = got == expected
            if ok:
                passed += 1
            print(f"[{'PASS' if ok else 'FAIL'}] expected={expected} got={got} | {q}")
        except Exception as e:  # API/network error should not crash the whole run
            print(f"[ERROR] expected={expected} | {q} -> {e}")

    print(f"\nPassed {passed}/{len(questions)}")
    print("Mid-Term target: >= 12/15")


if __name__ == "__main__":
    main()
