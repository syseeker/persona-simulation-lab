"""Named teaching scenarios, separate from the original synthetic persona data."""

STORIES = {
    "photography": {
        "id": "photography", "title": "A first photography class",
        "question": "Find a beginner photography class for a Saturday, within S$50 before funding.",
        "preferences": {"goal": "photography", "budget_sgd": 50, "days": [5]},
        "lesson": "Follow one sourced recommendation from the learner's request through MCP and the model.",
        "expected": "Recommend only supported listings, preserving unknown extras and funding eligibility.",
    },
    "baking": {
        "id": "baking", "title": "A budget that includes materials",
        "question": "I want a baking class with a total budget of S$120, including known materials.",
        "preferences": {"goal": "baking", "budget_sgd": 120},
        "lesson": "Inspect exclusions and change one explicit budget constraint to S$130.",
        "expected": "Include known material fees; a published base fee alone does not prove budget fit.",
    },
    "boardgames": {
        "id": "boardgames", "title": "When the catalogue has no answer",
        "question": "Hello, I want to learn how to play board games.",
        "preferences": {"goal": "board games"},
        "lesson": "An honest no-match response is useful application behaviour.",
        "expected": "Explain that this snapshot has no board-game class; do not substitute game design or invent one.",
    },
    'dreamjob': {
        'id': 'dreamjob', 'title': 'Learn retail analysis with staged disclosure',
        'question': "In this hypothetical situation you work in retail and want sales/inventory-analysis skills. Ask about SMU Academy's SCTP Advanced Certificate in Data Communications and Visualisation for Business Analyst: its content, duration and full fee. Do not disclose salary, spending budget or weekend constraint in the opening.",
        'preferences': {'goal': 'retail sales inventory data analytics visualisation Excel'},
        'lesson': 'Separate original traits, Designer hypotheses, public disclosure, controlled routing and managed operations.',
        'expected': 'Use published facts; salary is not a budget or funding proof. Preserve unknown timetable/eligibility and avoid employer endorsement or job guarantees.',
    },
    "profile-goal": {
        "id": "profile-goal", "title": "Explore the selected learner's goal",
        "question": None, "preferences": None,
        "lesson": "Let UserSim express the selected profile's professional ambitions or interests.",
        "expected": "Respect the selected profile and labelled scenario; preserve catalogue limits.",
    },
}


def story(story_id: str) -> dict:
    if story_id not in STORIES:
        raise ValueError("Unknown learning story")
    return STORIES[story_id]


def list_stories() -> list[dict]:
    return list(STORIES.values())
