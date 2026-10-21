"""Thin wrapper around the Alibaba Cloud Bailian OpenAI-compatible API.

The teaching team sponsors a group key with an OpenAI-style base URL.
We use the official openai SDK pointed at that base URL so the code is
easy to read and the model names stay configurable via .env.
"""
from openai import OpenAI

import config

_CLIENT = None


def get_client():
    global _CLIENT
    if _CLIENT is None:
        # Sequential calls only (no high concurrency) to avoid key suspension.
        _CLIENT = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)
    return _CLIENT
