"""Validate the lab routing inventory without printing or contacting providers."""

import os
from pathlib import Path
import yaml


def validate(config: dict, environment: dict[str, str]) -> dict:
    groups = {}
    for item in config["model_list"]:
        groups.setdefault(item["model_name"], []).append(item["litellm_params"])
    expected = {"lab-advisor-fixed": 1, "lab-support": 1, "lab-advisor-routed": 2}
    if {k: len(v) for k, v in groups.items()} != expected:
        raise ValueError("Require one fixed advisor, one support and two ordered routed deployments")
    resolved = {}
    for group, models in groups.items():
        resolved[group] = []
        for model in models:
            for field in ("model", "api_base", "api_key"):
                variable = model[field].removeprefix("os.environ/")
                if not environment.get(variable):
                    raise ValueError(f"Set {variable}; no provider call was attempted")
            model_id = environment[model["model"].removeprefix("os.environ/")]
            if "/" not in model_id or not model_id.split("/", 1)[1].strip():
                raise ValueError(
                    "Proxy model IDs need both a LiteLLM provider prefix and a nonempty model name"
                )
            resolved[group].append(model_id)
    if len(set(resolved["lab-advisor-routed"])) != 2:
        raise ValueError("Switchyard needs two distinct model IDs; use fixed routing for one model")
    if len(environment.get("LAB_PROXY_API_KEY", "")) < 24:
        raise ValueError("LAB_PROXY_API_KEY must contain at least 24 characters")
    if config["router_settings"].get("num_retries") != 0 or config["router_settings"].get("fallbacks"):
        raise ValueError("Hidden retries/fallbacks would bypass the lab inference budget")
    return {"valid": True, "groups": expected, "policy": "stage", "inference_calls": 0}


if __name__ == "__main__":
    from dotenv import load_dotenv

    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    print(validate(yaml.safe_load(Path(__file__).with_name("litellm.yaml").read_text()), dict(os.environ)))
