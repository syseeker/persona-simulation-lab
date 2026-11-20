import copy
import hashlib
import json

import pytest

from learning_lab.catalogue import Preferences
from learning_lab.enrichment import apply_overlays, generate_overlays
from learning_lab.evaluation import run_helix, score_response
from learning_lab.settings import ROOT


def test_reply_checks_detect_missing_sources_and_unsupported_assurances():
    checks = score_response(
        "Choose CC-999 at https://example.org/x; you are eligible for funding; no extra fees.",
        Preferences(goal="photography"),
    )
    assert not checks["catalogue_grounding"]
    assert not checks["constraint_compliance"]
    assert not checks["eligibility_caution"]
    assert not checks["fee_caution"]


@pytest.mark.skipif(
    not (ROOT / "integrations/helix/.venv/bin/python").exists(),
    reason="Install the isolated Helix environment",
)
async def test_helix_scores_a_real_pass_and_failure(tmp_path):
    rows = [{"output": "true", "expected": "true"}, {"output": "false", "expected": "true"}]
    source = tmp_path / "criteria.json"
    source.write_text(json.dumps(rows))
    result = await run_helix(source, tmp_path / "result.json")
    assert result["summary"]["default"] == {"criteria": 2, "passed": 1}
    assert len(json.loads((tmp_path / "result.json").read_text())["row_scores"]) == 2


@pytest.mark.skipif(
    not (ROOT / "integrations/designer/.venv/bin/python").exists(),
    reason="Install the isolated Data Designer environment",
)
async def test_designer_preserves_source_and_labels_hypotheses(tmp_path, monkeypatch):
    original = {"uuid": "fabricated-fixture", "persona": "A fabricated test learner"}
    original_json = json.dumps(original, sort_keys=True)
    seed = tmp_path / "seed.jsonl"
    seed.write_text(
        json.dumps(
            {
                "source_id": original["uuid"],
                "source_revision": "fixture",
                "original_profile_json": original_json,
                "original_profile_sha256": hashlib.sha256(original_json.encode()).hexdigest(),
            }
        )
        + "\n"
    )
    monkeypatch.setenv("LAB_SEED_PATH", str(seed))
    overlays = await generate_overlays(tmp_path / "overlays.json", 1)
    assert overlays["records"][0]["hypothesis"] is True
    row = {"persona": original, "trajectory_id": "original-input"}
    enriched = apply_overlays([row], overlays)[0]
    assert enriched["persona"] == original and "learning_overlay" not in row
    assert enriched["trajectory_id"] != row["trajectory_id"]
    corrupted = copy.deepcopy(overlays)
    corrupted["records"][0]["original_profile_json"] = "{}"
    with pytest.raises(ValueError):
        apply_overlays([row], corrupted)


@pytest.mark.skipif(
    not (ROOT / "integrations/designer/.venv/bin/python").exists(),
    reason="Install the isolated Data Designer environment",
)
async def test_legacy_sampler_enriches_exact_random_profiles_instead_of_old_review_panel(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("LAB_SEED_PATH", str(tmp_path / "must-not-use-old-panel.jsonl"))
    rows = [
        {
            "persona": {"uuid": f"new-random-fixture-{index}", "age": 30 + index},
            "trajectory_id": f"trajectory-{index}",
            "source_revision": "fixture-revision",
        }
        for index in range(2)
    ]
    overlays = await generate_overlays(tmp_path / "overlays.json", 2, resolved_rows=rows)
    enriched = apply_overlays(rows, overlays)
    assert [row["persona"] for row in enriched] == [row["persona"] for row in rows]
    assert {item["source_id"] for item in overlays["records"]} == {row["persona"]["uuid"] for row in rows}
    assert all(row["learning_overlay"]["hypothesis"] for row in enriched)
