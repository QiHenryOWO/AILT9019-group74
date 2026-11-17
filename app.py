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

    try:
        result = pipeline_mod.answer(q)
    except RuntimeError as exc:  # missing key: explain, do not dump a traceback
        print(f"\nCannot answer: {exc}")
        return 1
    except Exception as exc:  # network or API failure: say what failed
        print(f"\nThe model call failed ({type(exc).__name__}: {exc}).")
        print("Retrieval and the offline checks still work: "
              "python evaluate.py --no-llm")
        return 1

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
