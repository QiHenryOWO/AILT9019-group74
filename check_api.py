"""One-line health check for the sponsored model endpoint.

The credits on the group plan expire during the submission week, so check the
endpoint right before recording a demo rather than discovering it is gone
halfway through.

Usage:
    python3 check_api.py
Exit code 0 = the model answered, 1 = it did not (expired, throttled, offline).
"""
import sys
import time

from src import client
import config


def main():
    started = time.time()
    try:
        resp = client.get_client().chat.completions.create(
            model=config.CHAT_MODEL,
            messages=[{"role": "user", "content": "Reply with exactly: ok"}],
            max_tokens=5,
            timeout=30,
        )
    except Exception as exc:
        print(f"DOWN  {type(exc).__name__}: {exc}")
        print("Retrieval still works offline: python3 evaluate.py --no-llm")
        return 1
    elapsed = time.time() - started
    reply = (resp.choices[0].message.content or "").strip()
    print(f"UP    {config.CHAT_MODEL} answered in {elapsed:.1f}s -> {reply!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
