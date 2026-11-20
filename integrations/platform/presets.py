"""Explicit public deployment fixtures; no persona or private learner records."""

import hashlib
import json


PHOTOGRAPHY = {
    "goal": "photography",
    "budget_sgd": 50,
    "days": [5],
    "planning_area": None,
    "known_skills": None,
    "kind": None,
}
PRESET_IMAGE_PATH = "/workspace/scenarios/photography/preferences.json"


def preset_bytes() -> bytes:
    return (json.dumps(PHOTOGRAPHY, sort_keys=True, separators=(",", ":")) + "\n").encode()


def preset_metadata() -> dict:
    return {
        "preferences_mode": "frozen-public-preset",
        "frozen_preferences": PHOTOGRAPHY,
        "preferences_sha256": hashlib.sha256(preset_bytes()).hexdigest(),
    }
