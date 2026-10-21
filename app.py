"""Single-question demo for the 1-minute Mid-Term recording.

Usage:
    python app.py "How do I book a group study room at the library?"
or just:
    python app.py
and type your question when prompted.
"""
import sys

from src import pipeline as pipeline_mod


def main():
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
    else:
        q = input("Ask a question about HKU student services: ").strip()

    result = pipeline_mod.answer(q)

    print("\n=== QUESTION ===")
    print(q)
    print("\n=== ANSWER ===")
    print(result["answer"])

    if result.get("sources"):
        print("\n=== SOURCES ===")
        for s in result["sources"]:
            print(f"- {s['title']}: {s['url']}")

    if result.get("refused"):
        print("\n[Refusal guard triggered:", ", ".join(result["categories"]), "]")


if __name__ == "__main__":
    main()
