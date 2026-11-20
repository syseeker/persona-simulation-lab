"""Shared closed JSON schemas for Designer previews; no SDK import in the main worker."""

from __future__ import annotations

import math


def generated_record_schema(field: dict) -> dict:
    kind = field["type"]
    schema = {
        "text": {"type": "string", "minLength": 1, "maxLength": 2000},
        "integer": {"type": "integer"},
        "decimal": {"type": "number"},
        "boolean": {"type": "boolean"},
        "enum": {"type": "string", "enum": field.get("choices", [])},
        "text-list": {
            "type": "array",
            "items": {"type": "string", "minLength": 1, "maxLength": 100},
            "maxItems": 10,
        },
    }[kind].copy()
    schema["description"] = field["description"]
    for key in ("minimum", "maximum"):
        if field.get(key) is not None:
            schema[key] = field[key]
    return schema


def _closed(properties: dict) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


SCENARIO_SCHEMA = _closed(
    {
        "story_title": {"type": "string", "minLength": 1, "maxLength": 100},
        "learning_goal": {"type": "string", "minLength": 1, "maxLength": 1000},
        "prior_familiarity": {"type": "string", "enum": ["beginner", "some experience", "experienced"]},
        "delivery_preference": {"type": "string", "enum": ["in person", "online", "either"]},
        "budget_sgd": {"type": "number", "minimum": 0, "maximum": 50000},
        "availability": {"type": "string", "minLength": 1, "maxLength": 200},
        "opening_message": {
            "type": "string",
            "minLength": 1,
            "maxLength": 2000,
            "description": "The simulated LEARNER's first-person request to the advisor, e.g. 'I want to learn baking within S$130. Can you help me find a class?' Never an advisor greeting, recommendation, answer, or message addressing the learner by name.",
        },
    }
)

PROFILE_SCHEMA = _closed(
    {
        "age": {"type": "integer", "minimum": 18, "maximum": 108},
        "country": {"type": "string", "enum": ["Singapore"]},
        "planning_area": {"type": "string", "minLength": 1, "maxLength": 100},
        "education_level": {"type": "string", "minLength": 1, "maxLength": 200},
        "occupation": {"type": "string", "minLength": 1, "maxLength": 200},
        "skills_and_expertise_list": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10,
            "items": {"type": "string", "minLength": 1, "maxLength": 100},
        },
        "hobbies_and_interests_list": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10,
            "items": {"type": "string", "minLength": 1, "maxLength": 100},
        },
        "career_goals_and_ambitions": {"type": "string", "minLength": 1, "maxLength": 1000},
        "persona": {"type": "string", "minLength": 1, "maxLength": 2000},
    }
)


def validate_json_schema(value, schema: dict, path="generated") -> None:
    """Validate the deliberately small schema vocabulary authored by this application.

    Data Designer/provider validation runs first. This independent check prevents
    malformed native output crossing back into the worker after a subprocess run.
    """
    kind = schema["type"]
    valid = {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "boolean": lambda: isinstance(value, bool),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda: isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value),
    }[kind]()
    if not valid:
        raise ValueError(f"{path} must have type {kind}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path} must be one of the configured choices")
    if kind == "object":
        if set(schema["required"]) - set(value):
            raise ValueError(f"{path} is missing required fields")
        if schema.get("additionalProperties") is False and set(value) - set(schema["properties"]):
            raise ValueError(f"{path} contains unexpected fields")
        for key, child in value.items():
            validate_json_schema(child, schema["properties"][key], f"{path}.{key}")
    if kind in {"array", "string"}:
        prefix = "Items" if kind == "array" else "Length"
        if len(value) < schema.get("min" + prefix, 0) or len(value) > schema.get("max" + prefix, 100_000):
            raise ValueError(f"{path} is outside the configured length bounds")
        if kind == "array":
            for index, child in enumerate(value):
                validate_json_schema(child, schema["items"], f"{path}[{index}]")
    if kind in {"integer", "number"}:
        if value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            raise ValueError(f"{path} is outside the configured numeric bounds")
