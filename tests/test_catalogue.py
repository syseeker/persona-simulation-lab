from datetime import date

import pytest
from pydantic import ValidationError

from learning_lab.catalogue import Preferences, all_courses, search_courses
from learning_lab.course_mcp import compare_courses
from learning_lab.personas import parse_list


def match(**kwargs):
    return search_courses(Preferences(**kwargs), as_of=date(2026, 11, 10))


def ids(result):
    return [m["course"]["id"] for m in result["matches"]]


def test_snapshot_is_sourced_and_both_kinds_are_present():
    courses = all_courses()
    assert len(courses) == len({c.id for c in courses}) == 12
    assert sum(c.kind == "community" for c in courses) == 6
    assert all(c.captured_on and str(c.source_url).startswith("https://") for c in courses)


def test_saturday_photography_under_fifty():
    assert ids(match(goal="photography", budget_sgd=50, days=[5])) == ["CC-001"]


def test_materials_are_counted_toward_budget():
    assert "CC-002" not in ids(match(goal="baking", budget_sgd=120))
    assert "CC-002" in ids(match(goal="baking", budget_sgd=130))


def test_unknown_fee_is_conditional_and_not_free():
    r = match(goal="project management", budget_sgd=0)
    item = next(m for m in r["matches"] if m["course"]["id"] == "SF-005")
    assert item["course"]["price_max_sgd"] is None
    assert any("budget fit is unconfirmed" in s for s in item["confirm"])


def test_conflicting_day_and_unmet_prerequisite_are_excluded():
    assert "CC-001" not in ids(match(goal="photography", days=[1]))
    assert "CC-004" not in ids(match(goal="basic computer", known_skills=[]))
    assert "CC-004" in ids(match(goal="basic computer", known_skills=["basic_computer"]))


def test_closed_intake_is_excluded():
    r = search_courses(Preferences(goal="photography"), as_of=date(2027, 3, 1))
    assert "CC-001" not in ids(r)


def test_sensitive_profile_attributes_are_not_matching_inputs():
    with pytest.raises(ValidationError):
        Preferences(goal="learn", religion="made-up")


def test_no_match_and_bad_days_are_explicit():
    assert match(goal="underwater basket weaving")["matches"] == []
    with pytest.raises(ValueError):
        match(goal="photography", days=[9])


def test_comparison_rejects_duplicate_or_unknown_ids():
    with pytest.raises(ValueError):
        compare_courses(["CC-001", "CC-001"])
    with pytest.raises(ValueError):
        compare_courses(["CC-001", "UNKNOWN"])


def test_source_lists_parse_without_executing_code():
    assert parse_list("['Excel', 'Photography']") == ["Excel", "Photography"]
    with pytest.raises((ValueError, SyntaxError)):
        parse_list("__import__('os').getcwd()")


def test_tool_cannot_relax_explicit_application_constraints(tmp_path, monkeypatch):
    from learning_lab.course_mcp import search_courses

    path = tmp_path / "preferences.json"
    path.write_text(Preferences(goal="baking", budget_sgd=100, days=[5], known_skills=[]).model_dump_json())
    monkeypatch.setenv("LAB_PREFERENCES_FILE", str(path))
    result = search_courses("baking", budget_sgd=10000)
    assert "CC-002" not in ids(result)


def test_run_catalogue_stays_frozen_if_source_changes(tmp_path, monkeypatch):
    from learning_lab import catalogue
    import json

    root = tmp_path / "app"
    (root / "catalogue").mkdir(parents=True)
    source = root / "catalogue/courses.json"
    original = (catalogue.ROOT / "catalogue/courses.json").read_bytes()
    source.write_bytes(original)
    monkeypatch.setattr(catalogue, "ROOT", root)
    snapshot = tmp_path / "run/catalogue.json"
    before = catalogue.freeze_catalogue(snapshot)
    revised = json.loads(original)
    revised["courses"][0]["title"] = "A later catalogue revision"
    source.write_text(json.dumps(revised))
    assert catalogue.freeze_catalogue(snapshot) == before
    assert snapshot.read_bytes() == original


def test_invalid_model_tool_arguments_are_repairable():
    from learning_lab.course_mcp import search_courses

    result = search_courses("photography", days=[7])
    assert result["matches"] == []
    assert "Sunday=6" in result["hint"]
