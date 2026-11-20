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
RETAIL = {'goal': 'retail sales inventory data analytics visualisation Excel', 'budget_sgd': 3000,
          'days': [5, 6], 'planning_area': None, 'known_skills': None, 'kind': None}


def preset_bytes(scenario_id='photography') -> bytes:
    if scenario_id not in {'photography', 'dreamjob'}:
        raise ValueError('Choose an implemented public managed preset')
    return (json.dumps(PHOTOGRAPHY if scenario_id == 'photography' else RETAIL, sort_keys=True, separators=(",", ":")) + "\n").encode()


def preset_metadata(scenario_id='photography') -> dict:
    return {
        "preferences_mode": "frozen-public-preset",
        "frozen_preferences": PHOTOGRAPHY if scenario_id == 'photography' else RETAIL,
        "preferences_sha256": hashlib.sha256(preset_bytes(scenario_id)).hexdigest(),
    }
