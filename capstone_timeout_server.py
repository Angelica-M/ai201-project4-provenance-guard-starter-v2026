#!/usr/bin/env python3
"""Local-only fixture that injects slow inference for timeout acceptance tests."""

import time

import detector
from app import app


def delayed_perplexity(text: str) -> float:
    time.sleep(3.2)
    return 45.0


detector.perplexity = delayed_perplexity


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001, debug=False, threaded=True)
