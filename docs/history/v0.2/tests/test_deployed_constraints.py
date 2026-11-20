"""A broken deployed MCP fulfillment cannot silently drop learner constraints."""

import pytest
import hashlib
import json
import sys
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from learning_lab.course_mcp import bound_preferences, normalize_days, search_courses


def test_readable_model_weekdays_preserve_constraints_and_invalid_days_fail_closed(monkeypatch):
    for key in ("LAB_PREFERENCES_URL", "LAB_PREFERENCES_PRESET_FILE", "LAB_PREFERENCES_FILE",
                "LAB_REQUIRE_PREFERENCES"):
        monkeypatch.delenv(key, raising=False)
    assert normalize_days("Saturday and Sunday") == [5, 6]
    assert normalize_days("sat, 5") == [5]
    result = search_courses("photography", budget_sgd=50, days="Saturday")
    assert "error" not in result
    assert all(set(row["course"]["weekdays"] or []) <= {5} for row in result["matches"])
    invalid = search_courses("photography", days="someday")
    assert invalid["matches"] == [] and "error" in invalid


async def test_real_stdio_mcp_keeps_readable_weekdays_and_invalid_input_distinct_from_no_match(tmp_path):
    """Real catalogue subprocess, deterministic course fixtures, no model calls."""
    catalogue = tmp_path / "catalogue.json"
    common = {
        "title": "Photography fixture",
        "provider": "Offline test fixture",
        "kind": "community",
        "summary": "A deterministic photography course for the MCP protocol regression.",
        "tags": ["photography"],
        "source_url": "https://example.test/official-course",
        "captured_on": "2026-11-10",
        "price_min_sgd": 50,
        "price_max_sgd": 50,
        "extra_cost_sgd": 0,
        "weekdays": [5],
    }
    catalogue.write_text(json.dumps({"courses": [
        {**common, "id": "SATURDAY"},
        {**common, "id": "MONDAY", "weekdays": [0]},
        {**common, "id": "OVER-BUDGET", "price_min_sgd": 100, "price_max_sgd": 100},
    ]}))
    # MCP inherits its small safe environment, not the host's inference keys or
    # deployed preference callbacks. This server reads only the fixture catalogue.
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "learning_lab.course_mcp"],
        env={"LAB_CATALOGUE_FILE": str(catalogue)},
    )
    arguments = {"goal": "photography", "budget_sgd": 50, "days": "Saturday"}
    native_records = []

    def payload_of(result):
        # Pinned FastMCP can emit a dict as JSON text without structuredContent.
        # Inspect that actual projection without altering the native result.
        return result.structuredContent or json.loads(result.content[0].text)

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=20)) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            assert len(tools) == 3
            assert {tool.name for tool in tools} == {
                "search_courses", "get_course_details", "compare_courses"
            }
            result = await session.call_tool("search_courses", arguments)
            native_records.append({"arguments": dict(arguments), "result": result.model_dump(mode="json")})
            assert arguments["days"] == "Saturday"  # Normalization belongs inside the server.
            assert result.isError is False
            payload = payload_of(result)
            assert "error" not in payload
            assert [row["course"]["id"] for row in payload["matches"]] == ["SATURDAY"]
            assert {row["id"] for row in payload["excluded"]} == {"MONDAY", "OVER-BUDGET"}
            # Preserve the native text projection as well as structured content.
            assert json.loads(result.content[0].text) == payload

            invalid_arguments = {**arguments, "days": "someday"}
            invalid = await session.call_tool("search_courses", invalid_arguments)
            native_records.append({"arguments": invalid_arguments, "result": invalid.model_dump(mode="json")})
            invalid_payload = payload_of(invalid)
            assert invalid.isError or invalid_payload.get("error")
            assert invalid_payload["matches"] == []
            assert "weekday" in invalid_payload["error"].lower()
            assert json.loads(invalid.content[0].text) == invalid_payload

            no_match = await session.call_tool("search_courses", {**arguments, "goal": "boardgames"})
            assert no_match.isError is False
            assert payload_of(no_match)["matches"] == []
            assert "error" not in payload_of(no_match)
    # Keep the received protocol objects intact for any failed-test inspection.
    (tmp_path / "mcp-native-results.json").write_text(json.dumps(native_records, indent=2))


def test_required_deployed_context_fails_closed_when_callback_is_missing(monkeypatch):
    monkeypatch.setenv("LAB_REQUIRE_PREFERENCES", "1")
    monkeypatch.delenv("LAB_PREFERENCES_URL", raising=False)
    monkeypatch.delenv("LAB_PREFERENCES_FILE", raising=False)
    with pytest.raises(ValueError, match="requires its authenticated"):
        bound_preferences({"goal": "photography", "budget_sgd": 500})


def test_frozen_public_preset_preserves_declared_constraints_and_detects_tampering(tmp_path, monkeypatch):
    preset = tmp_path / "preferences.json"
    payload = {"goal": "photography", "budget_sgd": 50, "days": [5]}
    preset.write_text(json.dumps(payload))
    monkeypatch.setenv("LAB_REQUIRE_PREFERENCES", "1")
    monkeypatch.setenv("LAB_PREFERENCES_PRESET_FILE", str(preset))
    monkeypatch.setenv("LAB_PREFERENCES_PRESET_SHA256", hashlib.sha256(preset.read_bytes()).hexdigest())
    monkeypatch.delenv("LAB_PREFERENCES_URL", raising=False)
    result = bound_preferences({"goal": "baking", "budget_sgd": 1000, "days": [0], "planning_area": "Elsewhere"})
    assert result.goal == "photography" and result.budget_sgd == 50 and result.days == [5]
    assert result.planning_area is None
    preset.write_text('{"goal":"baking","budget_sgd":1000}')
    with pytest.raises(ValueError, match="integrity check"):
        bound_preferences({"goal": "photography"})
