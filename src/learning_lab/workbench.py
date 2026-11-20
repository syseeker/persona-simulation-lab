"""UI/CLI-ready source-seeded Data Designer jobs in the isolated 0.10 environment."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import uuid
from typing import Literal

from pydantic import Field, FiniteFloat, model_validator
from aiohttp import web
import httpx

from .catalogue import StrictModel
from .datasets import PersonaSource, canonical_json, lock_personas, profile_hash, sample_personas
from .settings import ROOT, model_id

FieldType = Literal["text", "integer", "decimal", "boolean", "enum", "text-list"]
RESERVED = {
    "uuid",
    "source_id",
    "source",
    "source_revision",
    "original_profile_json",
    "original_profile_sha256",
    "profile",
    "generated",
    "lineage",
    "kind",
    "hypothesis",
    "generation_index",
    "generated_id",
    "scenario",
}


class DesignerField(StrictModel):
    name: str = Field(min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_]*$")
    type: FieldType
    description: str = Field(min_length=1, max_length=1200)
    minimum: FiniteFloat | None = None
    maximum: FiniteFloat | None = None
    choices: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def safe_definition(self):
        if self.name in RESERVED or self.name.startswith("original_"):
            raise ValueError("Choose a new column name outside the reserved provenance fields")
        if self.type == "enum" and (not self.choices or len(self.choices) != len(set(self.choices))):
            raise ValueError("An enum needs distinct nonempty choices")
        if self.type != "enum" and self.choices:
            raise ValueError("Choices apply only to enum fields")
        if any(not choice.strip() or len(choice) > 100 for choice in self.choices):
            raise ValueError("Enum choices must contain one to one hundred characters")
        if (self.minimum is not None or self.maximum is not None) and self.type not in {"integer", "decimal"}:
            raise ValueError("Bounds apply only to numeric fields")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("Minimum must not exceed maximum")
        return self


class WorkbenchSpec(StrictModel):
    operation: Literal["scenarios", "columns", "profiles"] = "scenarios"
    source: PersonaSource = "hf-profile-only"
    source_ids: list[str] = Field(default_factory=list, max_length=20)
    fields: list[DesignerField] = Field(default_factory=list, max_length=8)
    count: int = Field(default=5, ge=1, le=20)
    seed: int | None = Field(default=None, ge=0, le=2**63 - 1)

    @model_validator(mode="after")
    def unique_fields(self):
        if len({field.name for field in self.fields}) != len(self.fields):
            raise ValueError("Custom column names must be distinct")
        if self.operation == "columns" and not self.fields:
            raise ValueError("Add at least one custom column")
        return self


def prepare_workbench(spec: WorkbenchSpec | dict) -> dict:
    """Freeze selected source rows and validate inputs; no inference or filesystem writes."""
    spec = spec if isinstance(spec, WorkbenchSpec) else WorkbenchSpec.model_validate(spec)
    locked = (
        lock_personas(spec.source, spec.source_ids)
        if spec.source_ids
        else sample_personas(spec.source, spec.count, spec.seed)
    )
    source_columns = {key for record in locked["records"] for key in record["profile"]}
    collision = source_columns & {field.name for field in spec.fields}
    if collision:
        raise ValueError("Custom fields cannot overwrite original columns: " + ", ".join(sorted(collision)))
    count = spec.count if spec.operation == "profiles" else min(spec.count, len(locked["records"]))
    seeds = []
    for index in range(count):
        record = locked["records"][index % len(locked["records"])]
        seeds.append(
            {
                "source_id": record["source_id"],
                "source_distribution": spec.source,
                "source_dataset": locked["dataset"],
                "source_revision": locked["source_revision"],
                "original_profile_json": canonical_json(record["profile"]),
                "original_profile_sha256": record["original_profile_sha256"],
                "generation_index": index,
                "field_instructions_json": canonical_json([field.model_dump() for field in spec.fields]),
            }
        )
    return {
        "version": 1,
        "pipeline": "source-seeded-designer-v2",
        "spec": spec.model_dump(),
        "locked_inputs": locked,
        "seeds": seeds,
        "record_count": count,
        "minimum_generation_calls": count * (len(spec.fields) + (spec.operation != "columns")),
        "notice": "Generated fields, scenarios and new profiles are hypothetical, not additional source facts.",
    }


def validate_generated_payload(prepared: dict, records: list[dict]) -> list[dict]:
    """Validate subprocess output again before exposing derived rows or using them in UserSim."""
    from .designer_schema import generated_record_schema, validate_json_schema

    spec = WorkbenchSpec.model_validate(prepared["spec"])
    seeds = prepared["seeds"]
    if len(records) != len(seeds):
        raise ValueError(f"Designer returned {len(records)} of {len(seeds)} requested records")
    output = []
    for index, record in enumerate(records):
        seed = seeds[index]
        if any(
            record.get(key) != seed[key]
            for key in (
                "source_id",
                "source_revision",
                "original_profile_json",
                "original_profile_sha256",
                "generation_index",
            )
        ):
            raise ValueError("Designer changed source lineage or reordered source records")
        original = json.loads(seed["original_profile_json"])
        if profile_hash(original) != seed["original_profile_sha256"]:
            raise ValueError("Original profile hash verification failed")
        generated = {}
        for field in spec.fields:
            value = record.get("custom_" + field.name)
            if isinstance(value, str):
                value = json.loads(value)
            validate_json_schema(
                value,
                {
                    "type": "object",
                    "properties": {"value": generated_record_schema(field.model_dump())},
                    "required": ["value"],
                    "additionalProperties": False,
                },
            )
            generated[field.name] = value["value"]
        scenario = None
        if spec.operation != "columns":
            column = "generated_profile" if spec.operation == "profiles" else "generated_scenario"
            scenario = record.get(column)
            if isinstance(scenario, str):
                scenario = json.loads(scenario)
            from .designer_schema import PROFILE_SCHEMA, SCENARIO_SCHEMA

            validate_json_schema(
                scenario, PROFILE_SCHEMA if spec.operation == "profiles" else SCENARIO_SCHEMA
            )
            if spec.operation == "profiles" and all(
                scenario.get(key) == original.get(key) for key in scenario
            ):
                raise ValueError("Generated profile duplicates its seed profile")
        generated_id = str(uuid.uuid4())
        item = {
            "generated_id": generated_id,
            "kind": "generated-profile" if spec.operation == "profiles" else "enriched-source",
            "hypothesis": True,
            "source_id": seed["source_id"],
            "original_profile_json": seed["original_profile_json"],
            "original_profile_sha256": seed["original_profile_sha256"],
            "profile": {**scenario, "uuid": "designer-" + generated_id}
            if spec.operation == "profiles"
            else original,
            "generated_fields": generated,
            "scenario": scenario if spec.operation == "scenarios" else None,
            "lineage": {
                key: seed[key]
                for key in (
                    "source_id",
                    "source_distribution",
                    "source_dataset",
                    "source_revision",
                    "original_profile_sha256",
                )
            },
        }
        output.append(item)
    generated_profiles = [
        canonical_json({k: v for k, v in item["profile"].items() if k != "uuid"})
        for item in output
        if item["kind"] == "generated-profile"
    ]
    if len(generated_profiles) != len(set(generated_profiles)):
        raise ValueError("Designer generated duplicate profiles in this preview")
    return output


def resolved_workbench_profiles(result: dict, source_ids: list[str] | None = None) -> dict:
    """Expose saved derived inputs to simulation without another generation call.

    Selection IDs are the profile UUIDs displayed in the result table (or the
    generated_id). Original parent IDs remain in each record's lineage.
    """
    if result.get("status") not in {"completed", "completed_with_warnings"} or not result.get("records"):
        raise ValueError("Choose a completed generated dataset with saved rows")
    from .designer_schema import PROFILE_SCHEMA, SCENARIO_SCHEMA, validate_json_schema

    records = result["records"]
    if not isinstance(records, list) or len(records) > 20:
        raise ValueError("The saved generated dataset has an invalid record count")
    for record in records:
        original = json.loads(record["original_profile_json"])
        lineage = record["lineage"]
        digest = profile_hash(original)
        if (
            digest != record["original_profile_sha256"]
            or digest != lineage["original_profile_sha256"]
            or record["source_id"] != original.get("uuid")
            or record["source_id"] != lineage["source_id"]
            or record.get("hypothesis") is not True
        ):
            raise ValueError("Saved Designer source lineage or original-profile hash is invalid")
        if record["kind"] == "generated-profile":
            profile = dict(record["profile"])
            if profile.pop("uuid", None) != "designer-" + record["generated_id"]:
                raise ValueError("A generated profile must retain its separate Designer identity")
            validate_json_schema(profile, PROFILE_SCHEMA)
        elif record["kind"] == "enriched-source":
            if record["profile"] != original:
                raise ValueError("A saved overlay cannot replace or modify its original profile")
        else:
            raise ValueError("Unknown saved Designer record kind")
        if record.get("scenario") is not None:
            validate_json_schema(record["scenario"], SCENARIO_SCHEMA)
    if source_ids:
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Choose distinct generated profile IDs")
        selected = []
        for identifier in source_ids:
            matches = [
                record
                for record in records
                if identifier in {record["generated_id"], record["profile"]["uuid"]}
            ]
            if len(matches) != 1:
                raise ValueError("A selected profile does not identify exactly one generated row")
            selected.append(matches[0])
        records = selected
    if len({record["generated_id"] for record in records}) != len(records):
        raise ValueError("Choose distinct saved Designer rows, including when using identifier aliases")
    is_generated = all(record["kind"] == "generated-profile" for record in records)
    if any(record["kind"] == "generated-profile" for record in records) != is_generated:
        raise ValueError("A dataset cannot mix generated profiles with original profile overlays")
    overlays = {}
    for record in records:
        if record.get("scenario") or record.get("generated_fields"):
            overlays[record["profile"]["uuid"]] = {
                **(record.get("scenario") or {}),
                "generated_fields": record.get("generated_fields", {}),
                "hypothesis": True,
                "overlay_id": record["generated_id"],
                "pipeline_version": "source-seeded-designer-v2",
                "scenario": record.get("scenario"),
                "original_profile_sha256": record["original_profile_sha256"],
            }
    return {
        "rows": [json.loads(canonical_json(record["profile"])) for record in records],
        "source_ids": [record["profile"]["uuid"] for record in records],
        "source_distribution": "generated-designer"
        if is_generated
        else records[0]["lineage"]["source_distribution"],
        "source_dataset": "NeMo Data Designer source-seeded profiles"
        if is_generated
        else records[0]["lineage"]["source_dataset"],
        "source_revision": result["config_sha256"]
        if is_generated
        else records[0]["lineage"]["source_revision"],
        "overlays": overlays,
        "lineage": {record["profile"]["uuid"]: record["lineage"] for record in records},
        "inference_calls": 0,
    }


async def run_workbench(spec: WorkbenchSpec | dict, folder: Path, gateway) -> dict:
    """Run an explicit preview through the supplied bounded gateway (no direct provider access)."""
    prepared = await asyncio.to_thread(prepare_workbench, spec)
    folder.mkdir(parents=True, exist_ok=True)
    request = folder / "designer-request.json"
    request.write_text(json.dumps(prepared, indent=2))
    if gateway.mode != "live":
        result = {
            "status": "validated_offline",
            "mode": "demo",
            "records": [],
            "prepared": prepared,
            "inference_calls": 0,
            "notice": "Inputs validated only. Real Data Designer LLM generation requires live mode.",
        }
        (folder / "designer-result.json").write_text(json.dumps(result, indent=2))
        return result
    python = ROOT / "integrations/designer/.venv/bin/python"
    if not python.exists():
        raise ValueError("Install the isolated Data Designer 0.10 environment first")
    if prepared["minimum_generation_calls"] > gateway.budget.limit - gateway.budget.calls:
        raise ValueError("The requested preview exceeds the remaining model-call budget")
    output = folder / "designer-native.json"
    # Filter credential names before adding the single per-job loopback key.
    # An explicit old provider list would miss new proxy/deployment tokens.
    env = {
        key: value
        for key, value in os.environ.items()
        if not re.search(r"KEY|TOKEN|SECRET|PASSWORD", key, flags=re.I)
    }
    env.update(LAB_DESIGNER_GATEWAY_KEY=gateway.key, LAB_DESIGNER_MODEL=model_id("designer"))
    before = gateway.budget.calls
    async with designer_endpoint(gateway) as endpoint:
        env["LAB_DESIGNER_GATEWAY_URL"] = endpoint
        process = await asyncio.create_subprocess_exec(
            str(python),
            str(ROOT / "integrations/designer/learning_preferences.py"),
            "--request",
            str(request),
            "--output",
            str(output),
            cwd=ROOT,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
        except BaseException:
            process.kill()
            await process.wait()
            raise
    # Native diagnostics remain local; a bounded generic browser error links to artifacts.
    diagnostic = (stdout + b"\n" + stderr).decode(errors="replace").replace(gateway.key, "[redacted]")
    (folder / "designer.log").write_text(diagnostic)
    if process.returncode:
        raise RuntimeError("Data Designer preview failed; inspect the saved designer.log and gateway usage")
    payload = json.loads(output.read_text())
    records = validate_generated_payload(prepared, payload["records"])
    result = {
        "version": 1,
        "status": "completed_with_warnings" if payload.get("warnings") else "completed",
        "mode": "live",
        "engine": "NeMo Data Designer 0.10.0",
        "operation": prepared["spec"]["operation"],
        "records": records,
        "record_count": len(records),
        "inference_calls": gateway.budget.calls - before,
        "model": env["LAB_DESIGNER_MODEL"],
        "config_sha256": hashlib.sha256((folder / "designer-config.json").read_bytes()).hexdigest(),
        "artifacts": [
            "designer-request.json",
            "designer-config.json",
            "designer-native.json",
            "designer.log",
        ],
        "notice": prepared["notice"],
        "warnings": payload.get("warnings", []),
    }
    (folder / "designer-result.json").write_text(json.dumps(result, indent=2))
    return result


@asynccontextmanager
async def designer_endpoint(gateway):
    """Role-aware admission bridge with terminal errors that the SDK cannot retry.

    Designer 0.10's public RunConfig disables generation restarts but does not
    expose native HTTP transport retry controls. Returning terminal HTTP 400
    avoids transport retries without monkeypatching the installed SDK. Actual
    model attempts still go through the application's shared gateway.
    """

    async def handle(request):
        if request.headers.get("Authorization") != "Bearer " + gateway.key:
            return web.json_response({"error": {"message": "Unauthorized"}}, status=401)
        try:
            payload = await request.json()
            if payload.get("stream"):
                raise ValueError("Designer streaming is disabled")
            return web.json_response(await gateway.complete(payload, role="designer"))
        except (ValueError, RuntimeError, OSError, httpx.HTTPError):
            return web.json_response(
                {"error": {"message": "Designer model request failed; inspect saved usage"}}, status=400
            )

    app = web.Application(client_max_size=1024 * 1024)
    app.router.add_post("/v1/chat/completions", handle)
    runner = web.AppRunner(app, access_log=None, shutdown_timeout=3)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        yield f"http://127.0.0.1:{runner.addresses[0][1]}/v1"
    finally:
        await runner.cleanup()
