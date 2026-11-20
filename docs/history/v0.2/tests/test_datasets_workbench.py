"""Offline corpus queries and genuine Designer SDK execution against a local test provider."""

import asyncio
import copy
import json
import re

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from learning_lab import datasets
from learning_lab.datasets import browse_personas, dataset_catalogue, lock_personas, sample_personas
from learning_lab.designer_schema import PROFILE_SCHEMA, SCENARIO_SCHEMA, validate_json_schema
from learning_lab.inference import Budget
from learning_lab.settings import ROOT
from learning_lab.workbench import (
    DesignerField,
    WorkbenchSpec,
    prepare_workbench,
    resolved_workbench_profiles,
    run_workbench,
    validate_generated_payload,
)


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    monkeypatch.setattr(datasets, "ROOT", tmp_path)
    monkeypatch.setenv("LAB_NGC_PERSONAS_PATH", str(tmp_path / "missing-ngc.parquet"))
    folder = tmp_path / "data/hf/data"
    folder.mkdir(parents=True)
    rows = [
        {
            "uuid": f"source-{index:03}",
            "age": 18 + index,
            "country": "Singapore",
            "planning_area": "Yishun" if index % 2 else "Tampines",
            "occupation": "Fixture tester",
            "education_level": "Fixture education",
            "skills_and_expertise_list": "['Testing']",
            "hobbies_and_interests_list": "['Baking']",
            "career_goals_and_ambitions": f"Fixture goal {index}",
        }
        for index in range(30)
    ]
    pq.write_table(pa.Table.from_pylist(rows[:15]), folder / "a.parquet")
    pq.write_table(pa.Table.from_pylist(rows[15:]), folder / "b.parquet")
    return rows


def test_full_corpus_paging_filtering_and_inspection(corpus):
    catalogue = dataset_catalogue()
    assert catalogue["datasets"][0]["row_count"] == 30
    page = browse_personas({"offset": 20, "limit": 4})
    assert page["total"] == 30 and page["has_more"]
    assert page["records"][0]["source_id"] == "source-020"
    filtered = browse_personas({"age_min": 38, "planning_area": "yishun", "search": "FIXTURE"})
    assert filtered["total"] == 5
    assert all(record["profile"]["age"] >= 38 for record in filtered["records"])
    assert lock_personas("hf-profile-only", ["source-029"])["rows"] == [corpus[-1]]


def test_random_sample_replays_exact_ids_and_fresh_seed_is_recorded(corpus):
    first = sample_personas(count=8, seed=7)
    assert first["source_ids"] == sample_personas(count=8, seed=7)["source_ids"]
    assert len(set(first["source_ids"])) == 8 and first["matched_profiles"] == 30
    assert any(int(value.rsplit("-", 1)[-1]) > 12 for value in first["source_ids"])
    assert first["source_ids"] != sample_personas(count=8, seed=8)["source_ids"]
    assert isinstance(sample_personas()["seed"], int)
    with pytest.raises(ValueError, match="Only"):
        sample_personas(count=4, filters={"age_min": 46})


def test_ngc_readiness_never_substitutes_hf(corpus, tmp_path, monkeypatch):
    metadata = dataset_catalogue()["datasets"][1]
    assert not metadata["ready"] and metadata["country"] == "Singapore"
    with pytest.raises(ValueError, match="not installed"):
        browse_personas({"source": "ngc"})
    path = tmp_path / "sg-extended.parquet"
    pq.write_table(pa.Table.from_pylist(corpus[:1]), path)
    monkeypatch.setenv("LAB_NGC_PERSONAS_PATH", str(path))
    assert not dataset_catalogue()["datasets"][1]["ready"]
    with pytest.raises(ValueError, match="openness"):
        sample_personas(source="ngc")
    extended = {**corpus[0], **{key: 0.5 for key in datasets.OCEAN}}
    pq.write_table(pa.Table.from_pylist([extended]), path)
    assert browse_personas({"source": "ngc"})["records"][0]["profile"] == extended


def test_lock_rejects_missing_duplicate_and_path_inputs(corpus):
    with pytest.raises(ValueError, match="distinct"):
        lock_personas("hf-profile-only", ["source-000", "source-000"])
    with pytest.raises(ValueError, match="do not exist"):
        lock_personas("hf-profile-only", ["../../.env"])
    with pytest.raises(ValueError):
        browse_personas({"path": "/tmp/anything.parquet"})
    with pytest.raises(ValueError):
        browse_personas({"source": "any-ngc-asset"})


def test_workbench_prepares_immutable_five_row_inputs_and_bounds(corpus):
    prepared = prepare_workbench({"seed": 3})
    assert prepared["record_count"] == 5 and prepared["minimum_generation_calls"] == 5
    assert all(
        datasets.profile_hash(json.loads(row["original_profile_json"])) == row["original_profile_sha256"]
        for row in prepared["seeds"]
    )
    with pytest.raises(ValueError, match="overwrite"):
        prepare_workbench(
            {
                "operation": "columns",
                "fields": [{"name": "age", "type": "integer", "description": "Attempted overwrite"}],
            }
        )
    with pytest.raises(ValueError):
        WorkbenchSpec.model_validate({"operation": "columns"})
    with pytest.raises(ValueError):
        DesignerField(name="__exec__", type="text", description="Invalid")


def example_scenario():
    return {
        "story_title": "Fixture baking story",
        "learning_goal": "Learn baking",
        "prior_familiarity": "beginner",
        "delivery_preference": "in person",
        "budget_sgd": 130,
        "availability": "Saturday",
        "opening_message": "Find a beginner baking class within S$130.",
    }


def example_profile(index=0):
    return {
        "age": 40 + index,
        "country": "Singapore",
        "planning_area": "Woodlands",
        "education_level": "Diploma",
        "occupation": f"Generated fixture {index}",
        "skills_and_expertise_list": ["Coordination"],
        "hobbies_and_interests_list": ["Photography"],
        "career_goals_and_ambitions": "Develop presentation skills",
        "persona": "A new hypothetical learner.",
    }


def test_independent_validation_preserves_parents_and_rejects_changed_hash(corpus):
    prepared = prepare_workbench({"source_ids": ["source-000"]})
    record = {**prepared["seeds"][0], "generated_scenario": example_scenario()}
    result = validate_generated_payload(prepared, [record])
    assert result[0]["profile"] == corpus[0] and result[0]["hypothesis"] is True
    assert result[0]["scenario"]["budget_sgd"] == 130
    bad = copy.deepcopy(record)
    bad["original_profile_json"] = "{}"
    with pytest.raises(ValueError, match="lineage"):
        validate_generated_payload(prepared, [bad])
    bad = copy.deepcopy(record)
    bad["generated_scenario"]["budget_sgd"] = "130"
    with pytest.raises(ValueError, match="type number"):
        validate_generated_payload(prepared, [bad])


def test_all_custom_types_are_validated_and_not_treated_as_source(corpus):
    fields = [
        {"name": "salary", "type": "decimal", "description": "Hypothetical gross monthly SGD", "minimum": 0},
        {"name": "count", "type": "integer", "description": "A hypothetical count"},
        {"name": "active", "type": "boolean", "description": "A hypothetical choice"},
        {"name": "brand", "type": "enum", "description": "A hypothetical brand", "choices": ["A", "B"]},
        {"name": "brands", "type": "text-list", "description": "Hypothetical favourite brands"},
        {"name": "note", "type": "text", "description": "Hypothetical notes {{ not_an_expression }}"},
    ]
    prepared = prepare_workbench({"operation": "columns", "source_ids": ["source-001"], "fields": fields})
    native = {
        **prepared["seeds"][0],
        **{
            "custom_" + field["name"]: {"value": value}
            for field, value in zip(fields, [5000.0, 2, True, "A", ["A"], "x"])
        },
    }
    result = validate_generated_payload(prepared, [native])[0]
    assert result["generated_fields"]["salary"] == 5000 and "salary" not in result["profile"]
    native["custom_count"] = {"value": True}
    with pytest.raises(ValueError, match="integer"):
        validate_generated_payload(prepared, [native])


def test_generated_profiles_use_new_identity_and_reuse_without_inference(corpus):
    prepared = prepare_workbench({"operation": "profiles", "source_ids": ["source-001"], "count": 2})
    records = validate_generated_payload(
        prepared,
        [
            {**seed, "generated_profile": example_profile(index)}
            for index, seed in enumerate(prepared["seeds"])
        ],
    )
    selection = resolved_workbench_profiles(
        {"status": "completed", "records": records, "config_sha256": "config"}
    )
    assert selection["source_distribution"] == "generated-designer"
    assert selection["rows"][0]["uuid"].startswith("designer-")
    assert selection["rows"][0]["uuid"] != corpus[1]["uuid"] and selection["inference_calls"] == 0
    assert records[0]["lineage"]["source_id"] == corpus[1]["uuid"]


def test_saved_overlay_reuse_verifies_original_profile_and_alias_identity(corpus):
    prepared = prepare_workbench({"source_ids": ["source-001"]})
    records = validate_generated_payload(
        prepared, [{**prepared["seeds"][0], "generated_scenario": example_scenario()}]
    )
    saved = {"status": "completed", "records": records, "config_sha256": "fixture-config"}
    selected = resolved_workbench_profiles(saved)
    assert selected["overlays"]["source-001"]["scenario"] == example_scenario()
    with pytest.raises(ValueError, match="distinct saved Designer"):
        resolved_workbench_profiles(saved, [records[0]["generated_id"], "source-001"])
    changed = copy.deepcopy(saved)
    changed["records"][0]["profile"]["age"] += 1
    with pytest.raises(ValueError, match="original profile"):
        resolved_workbench_profiles(changed)
    changed = copy.deepcopy(saved)
    changed["records"][0]["lineage"]["original_profile_sha256"] = "tampered"
    with pytest.raises(ValueError, match="lineage"):
        resolved_workbench_profiles(changed)


async def test_approved_designer_scenario_replaces_named_story_in_actual_offline_target(corpus, tmp_path):
    from learning_lab.inference import Gateway
    from learning_lab.simulation import run_experiment

    prepared = prepare_workbench({"source_ids": ["source-001"]})
    records = validate_generated_payload(
        prepared, [{**prepared["seeds"][0], "generated_scenario": example_scenario()}]
    )
    selected = resolved_workbench_profiles(
        {"status": "completed", "records": records, "config_sha256": "fixture"}
    )
    events = []

    async def save(event):
        events.append(event)

    async with Gateway(Budget(4), "demo").serving() as gateway:
        await run_experiment(
            {
                "mode": "demo",
                "source": "hf-profile-only",
                "personas": 1,
                "engine": "direct",
                "strategies": ["concise"],
                "story_id": "photography",
            },
            tmp_path / "run",
            gateway,
            save,
            profiles_selection=selected,
        )
    user = next(event for event in events if event.get("role") == "user")
    answer = next(event for event in events if event.get("role") == "assistant")
    assert "baking" in user["content"].lower()
    assert answer["preferences"]["goal"] == "Learn baking" and answer["preferences"]["budget_sgd"] == 130
    assert answer["preferences"]["days"] is None  # Text availability is not inferred into trusted weekdays.
    assert "CC-002" in answer["content"] and "CC-001" not in answer["content"]
    assert records[0]["profile"] == corpus[1] and records[0]["scenario"] == example_scenario()


async def test_offline_workbench_does_not_pretend_generation(corpus, tmp_path):
    class OfflineGateway:
        mode = "demo"

    result = await run_workbench({"seed": 7}, tmp_path / "job", OfflineGateway())
    assert result["status"] == "validated_offline" and not result["records"]
    assert result["inference_calls"] == 0


@pytest.mark.skipif(
    not (ROOT / "integrations/designer/.venv/bin/python").exists(),
    reason="Install isolated Data Designer 0.10 environment",
)
@pytest.mark.parametrize(
    "operation,count,custom",
    [("scenarios", 1, True), ("profiles", 2, False), ("columns", 1, True), ("scenarios", 5, False)],
)
async def test_real_designer_sdk_uses_only_local_mock_gateway_and_custom_schema(
    corpus, tmp_path, monkeypatch, operation, count, custom
):
    monkeypatch.setenv("LAB_PROXY_API_KEY", "fixture-secret-not-for-child")
    monkeypatch.setenv("LAB_DEPLOYMENT_GATEWAY_KEY", "fixture-secret-not-for-child")
    monkeypatch.setenv("LAB_PREFERENCES_TOKEN", "fixture-secret-not-for-child")
    real_create = asyncio.create_subprocess_exec

    async def inspect_child(*args, **kwargs):
        environment = kwargs["env"]
        credential_names = {
            name for name in environment if re.search(r"KEY|TOKEN|SECRET|PASSWORD", name, re.I)
        }
        assert credential_names == {"LAB_DESIGNER_GATEWAY_KEY"}
        assert environment["LAB_DESIGNER_GATEWAY_KEY"] == "local-test-credential-only"
        return await real_create(*args, **kwargs)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", inspect_child)

    class LocalMockGateway:
        # Live here exercises the SDK branch; the provider below is a local fixture, never NVIDIA.
        mode = "live"
        key = "local-test-credential-only"
        budget = Budget(20)

        async def complete(self, payload, role):
            await self.budget.admit(role, "offline-sdk-test")
            assert role == "designer"
            # Installed Designer uses a schema-aware prompt/parser recipe rather
            # than requiring provider-native response_format support.
            prompt = json.dumps(payload["messages"])
            assert "source-00" in prompt
            if operation == "profiles":
                content = example_profile(self.budget.calls)
            elif "story_title" in prompt:
                content = example_scenario()
            else:
                content = {"value": 5100}
            return {
                "id": "offline-designer-fixture",
                "object": "chat.completion",
                "created": 0,
                "model": payload["model"],
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": json.dumps(content)},
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            }

    gateway = LocalMockGateway()
    fields = (
        [
            {
                "name": "salary",
                "type": "integer",
                "description": "Hypothetical last gross monthly salary in SGD",
                "minimum": 0,
            }
        ]
        if custom
        else []
    )
    result = await run_workbench(
        {
            "operation": operation,
            "count": count,
            "source_ids": [f"source-{index:03}" for index in range(2, 2 + count)],
            "fields": fields,
        },
        tmp_path / "job",
        gateway,
    )
    assert result["status"] == ("completed_with_warnings" if count == 1 else "completed")
    assert result["inference_calls"] == count * (int(operation != "columns") + int(custom))
    if count == 1:
        assert result["warnings"][0]["stage"] == "profiling"
    if custom:
        assert result["records"][0]["generated_fields"]["salary"] == 5100
    config = (tmp_path / "job/designer-config.json").read_text()
    assert "llm-structured" in config and gateway.key not in config
    assert gateway.key not in (tmp_path / "job/designer.log").read_text()
    if operation != "profiles":
        assert result["records"][0]["profile"] == corpus[2]
    else:
        assert isinstance(result["records"][0]["profile"]["skills_and_expertise_list"], list)


def test_closed_schemas_reject_extra_fields_and_nan():
    validate_json_schema(example_profile(), PROFILE_SCHEMA)
    with pytest.raises(ValueError, match="unexpected"):
        validate_json_schema({**example_scenario(), "citizenship": "invented"}, SCENARIO_SCHEMA)
    with pytest.raises(ValueError):
        DesignerField(name="income", type="decimal", description="Income", minimum=float("nan"))
