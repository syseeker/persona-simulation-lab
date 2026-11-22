"""Explicitly export one terminal scenario condition as a sanitized review pack.

Private originals, resolved simulator inputs, prompts, credentials, process
ownership and arbitrary native payloads are never copied to the public pack.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re

from learning_lab.journey import JourneyService, TERMINAL
from learning_lab.settings import ROOT, load_environment


def pick(value, keys):
    return {key: value[key] for key in keys if key in value}


def clean(value):
    if isinstance(value, dict):
        return {
            key: clean(item)
            for key, item in value.items()
            if not re.search(r"password|secret|authorization|api.?key|credential|(?:^|_)token$", key, re.I)
        }
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, str):
        for key, secret in os.environ.items():
            if re.search(r"KEY|TOKEN|SECRET|PASSWORD", key) and len(secret) >= 8:
                value = value.replace(secret, "[REDACTED]")
        value = value.replace(str(ROOT), "[developer-checkout]")
        value = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '[REDACTED_NATIVE_TOKEN]', value)
        return re.sub(r'/home/[^/\s"\']+', "[developer-home]", value)
    return value


def export(run_id, *, note, destination=None):
    load_environment()
    service = JourneyService()
    original = service.folder(run_id)
    state = json.loads((original / "run.json").read_text())
    if (
        state["scenario_id"] not in {'photography', 'boardgames', 'dreamjob'}
        or state["status"] not in TERMINAL
        or not state.get("cleanup_confirmed")
    ):
        raise ValueError("Export only terminal scenario conditions with verified cleanup")
    if state.get('capture_schema'):
        from learning_lab.captures import verify_capture_manifest
        path = original / 'capture-manifest.json'
        if not path.is_file():
            raise ValueError('This capture-enabled run has no capture manifest')
        verify_capture_manifest(original, json.loads(path.read_text()))
    trace = service.trace(run_id)
    scenario_id = state['scenario_id']
    target = destination or ROOT / 'recordings' / scenario_id / run_id
    if target.exists():
        raise ValueError("Recordings are immutable; choose a new condition instead of overwriting one")
    native = original / state["episode_id"]
    files, sources = {}, {}

    def emit(name, value, source=None, *, jsonl=False):
        safe = clean(value)
        files[name] = (
            "\n".join(json.dumps(item, ensure_ascii=False) for item in safe) + "\n"
            if jsonl
            else json.dumps(safe, indent=2, ensure_ascii=False) + "\n"
        )
        if source and source.is_file():
            sources[source.relative_to(original).as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()

    public_run = pick(
        state,
        [
            "schema",
            "run_id",
            "condition_id",
            "episode_id",
            "scenario_id",
            "status",
            "created_at",
            "started_at",
            "ended_at",
            "stage",
            "calls",
            "cleanup_confirmed",
            "configuration",
            "source_revision",
            "source_hashes",
            "catalogue_sha256",
            "native_thread_id",
            "evaluation_passed",
            "evaluation_total",
            "usersim_notice",
            "verification",
            "baseline_status",
            "capture_schema",
            "capture_coverage",
            "error",
        ],
    )
    conversation = [
        pick(row, ["turn", "public_turn", "role", "content", "outcome", "thread_id", "preferences",
                   "response_origin", "response_policy", "application_response_id"])
        for row in trace["conversation"]
    ]
    scopes = [
        pick(
            row,
            [
                "id",
                "uuid",
                "parent_uuid",
                "parent_id",
                "category",
                "name",
                "status",
                "started_at",
                "ended_at",
                "duration_ms",
                "parent_available",
            ],
        )
        for row in trace["relay"]["scopes"]
    ]
    tools = [
        pick(row, ["name", "arguments", "result", "output", "scope_uuid", "status", "evidence_origin"])
        for row in trace["tools"]
    ]
    usage = {
        "calls": trace["usage"]["calls"],
        "records": [
            pick(
                row,
                [
                    "call",
                    "role",
                    "mode",
                    "status",
                    "model",
                    "provider_route",
                    "requested_model",
                    "selected_model",
                    "finish_reason",
                    "output_token_limit",
                    "routing_decision",
                    "error_type",
                    "usage",
                    "latency_ms",
                    "tool_surface",
                    "control_request_id",
                    "thread_id",
                    "transport",
                    "http_status",
                    "provider_error",
                    "logical_request_id",
                    "attempt",
                    "retry_of_call",
                    "retry_status",
                    "retry_delay_seconds",
                    "retry_wait_seconds",
                    "retry_after_seconds",
                    "rate_limit_headers",
                    "rate_limit_header_source",
                ],
            )
            for row in trace["usage"]["records"]
        ],
    }
    source_lock = pick(
        trace["source_lock"] or {},
        ["source", "source_revision", "original_sha256", "kind", "source_url", "conditioning"],
    )
    result = {
        "run": public_run,
        "conversation": conversation,
        "source_lock": source_lock,
        "situation": trace["situation"],
        "usage": usage,
        "evaluation": trace["evaluation"],
        "relay": {
            "scopes": scopes,
            "notices": [
                "Sanitized native projection: payloads/private prompts/local paths omitted; native IDs/parents/status unchanged.",
                "Gateway calls and native model scopes have no verified automatic span join.",
            ],
        },
        "tools": tools,
        "developer_review": trace.get("developer_review"),
    }
    for name, value in [
        ("run.json", public_run),
        ("source-lock.json", source_lock),
        ("situation.json", trace["situation"]),
        ("public-conversation.json", conversation),
        ("usage.json", usage),
        ("evaluation.json", trace["evaluation"]),
        ("catalogue-snapshot.json", json.loads((original / "catalogue-snapshot.json").read_text())),
    ]:
        emit(name, value, original / name)
    emit("native-tools.json", tools)
    emit("relay-scopes.json", result["relay"])
    activations = [
        pick(
            json.loads(line),
            [
                "at",
                "phase",
                "activation_id",
                "role",
                "message_count",
                "tools_enabled",
                "continues_turn",
                "response_role",
                "usage",
            ],
        )
        for line in (original / "usersim-activations.jsonl").read_text().splitlines()
    ]
    emit("usersim-activations.jsonl", activations, original / "usersim-activations.jsonl", jsonl=True)
    if trace.get("developer_review"):
        emit("review-notes.json", trace["developer_review"], original / "review-notes.json")
    for path in [original / 'guardrails-probe.json', native / 'native/guardrails-config.json']:
        if path.is_file():
            emit(path.name, json.loads(path.read_text()), path)
    decisions = native / 'native/guardrails-decisions.jsonl'
    if decisions.is_file():
        emit(decisions.name, [json.loads(line) for line in decisions.read_text().splitlines() if line.strip()],
             decisions, jsonl=True)
    for name, keys in {
        "fabric-config.json": ["schema_version", "metadata", "harness", "runtime", "tools"],
        "fabric-plan.json": ["agent_name", "resolution", "capability_plan", "capabilities"],
        "fabric-doctor.json": ["agent_name", "status", "checks"],
        "runtime-receipt.json": ["ready", "thread_id", "image_manifest"],
        "sandbox-identity.json": ["run_id", "id", "name", "phase", "workspace", "current_policy_version"],
        "effective-policy.json": [
            "active_version",
            "config_revision",
            "hash",
            "policy",
            "policy_source",
            "scope",
            "status",
            "version",
        ],
        "boundary-probes.json": ["probes"],
        "cleanup.json": [
            "run_id",
            "sandbox_name",
            "native_absence_confirmed",
            "runtime_process_exited",
            "native_artifact_sha256",
        ],
    }.items():
        path = next((p for p in [native / "native" / name, native / name] if p.is_file()), None)
        if path:
            emit(
                name,
                {
                    "projection": "Allowlisted native fields; not a byte-for-byte original.",
                    **pick(json.loads(path.read_text()), keys),
                },
                path,
            )
    policy = native / "effective-policy.yaml"
    if policy.is_file():
        files["effective-policy.yaml"] = clean(policy.read_text())
        sources[policy.relative_to(original).as_posix()] = hashlib.sha256(policy.read_bytes()).hexdigest()
    for path in (native / "native").rglob("relay.jsonl"):
        sources[path.relative_to(original).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if scenario_id == 'dreamjob':
        from scripts.retail_review import project
        project(original, emit)
    emit("trace.json", result)
    manifest = {
        "schema": "citizen-recording/v1",
        "run_id": run_id,
        "scenario_id": scenario_id,
        "note": note,
        "projection_notice": "Fixed sanitized recording. Public messages/course facts/selected native fields are published; private context and raw payloads stay outside Git.",
        "files": {name: hashlib.sha256(raw.encode()).hexdigest() for name, raw in sorted(files.items())},
        "original_private_artifact_sha256": sources,
    }
    target.mkdir(parents=True)
    for name, raw in files.items():
        (target / name).write_text(raw)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {
        "directory": target.relative_to(ROOT).as_posix() if target.is_relative_to(ROOT) else str(target),
        "files": len(files),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--note", required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.run_id, note=args.note)))
