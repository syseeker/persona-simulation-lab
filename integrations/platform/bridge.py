"""One bounded JSON request to the public Helix Agents SDK, never a shell proxy."""

from __future__ import annotations

import asyncio
from contextlib import redirect_stdout
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import re
import sys
from uuid import UUID


ROOT = Path(__file__).resolve().parents[2]
PINS = {"nemo-helix": "0.10.0", "nemo-fabric": "0.6.1", "nemo-relay": "0.11.0"}
NAME = re.compile(r"[a-z][a-z0-9.-]{1,62}\Z")


def versions() -> dict:
    result = {}
    for package in PINS:
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = None
    return result


def clean(value):
    """Strip account/auth data and redact known local credentials even in logs."""
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    elif hasattr(value, "to_dict"):
        value = value.to_dict()
    if isinstance(value, dict):
        return {
            k: clean(v)
            for k, v in value.items()
            if k not in {"auth_context", "api_key", "access_token", "password", "token", "secret"}
        }
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, str):
        for name, secret in os.environ.items():
            if re.search(r"TOKEN|KEY|SECRET|PASSWORD", name) and len(secret) >= 8:
                value = value.replace(secret, "[REDACTED]")
        return value
    return value


def name_of(arguments: dict, key: str = "name") -> str:
    value = arguments.get(key, "")
    if not isinstance(value, str) or not NAME.fullmatch(value) or "--" in value or value.endswith("-"):
        raise ValueError(f"Invalid {key}; use an explicit lowercase resource name")
    return value


def session_identity(arguments: dict) -> str:
    value = arguments.get("name", arguments.get("session_id", ""))
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", value):
        raise ValueError("Invalid Platform session identity")
    return value


def recovery_receipt(arguments: dict) -> Path:
    """Accept only a server-selected job receipt beneath the local runs tree."""
    value = arguments.get("receipt_path")
    if not isinstance(value, str):
        raise ValueError("Recovery requires its server-owned job receipt path")
    path = Path(value)
    base = ROOT / "runs" / "platform-jobs"
    if not path.is_absolute() or path.parent.parent != base or path.name != "recovery-receipt.json":
        raise ValueError("Recovery receipt must belong to a Platform job")
    try:
        identity = UUID(path.parent.name)
    except ValueError as exc:
        raise ValueError("Recovery receipt requires a canonical Platform job identity") from exc
    if str(identity) != path.parent.name:
        raise ValueError("Recovery receipt requires a canonical Platform job identity")
    if any(part.is_symlink() for part in (ROOT / "runs", base, path.parent, path)):
        raise ValueError("Recovery receipt paths cannot contain symlinks")
    if path.resolve(strict=False) != path:
        raise ValueError("Recovery receipt path must be canonical")
    return path


def annotate_intake_correlation(evidence: dict, deployment_config: dict) -> None:
    """Explain a pinned Hermes correlation gap without attributing other traces."""
    harness = deployment_config.get("harnesses", {}).get(deployment_config.get("default_harness"), {})
    if (
        PINS["nemo-fabric"] != "0.6.1"
        or harness.get("kind") != "hermes"
        or evidence.get("status") != "no_records_observed"
    ):
        return
    evidence["correlation"] = {
        "status": "unsupported",
        "adapter_id": "nvidia.fabric.hermes",
        "fabric_version": PINS["nemo-fabric"],
        "expected_platform_session_uuid": evidence["session_identity"]["session_uuid"],
        "native_relay_session_uuid": None,
        "reason": (
            "The pinned Hermes adapter does not forward relay_session_root into its native Relay "
            "scope. Its independently generated Relay session UUID has no verified identity "
            "bridge to this Platform session. Empty session-filtered results do not establish "
            "that the exporter is disabled. Other workspace traces are not attributed by "
            "timestamp, agent name or conversation content."
        ),
    }


async def execute(client, operation: str, args: dict) -> dict:
    # Imports intentionally happen only in the isolated process.
    from nemo_helix_plugin.agents.types import (
        CreateAgentDeploymentRequest,
        CreateSessionRequest,
        InvokeAgentRequest,
        RegisterAgentRequest,
    )

    if operation == "configure":
        from configure import configure

        return await configure(client, args)

    if operation == "package":
        harness, image = args.get("harness"), args.get("image")
        if harness not in {"deepagents", "hermes"}:
            raise ValueError("Choose deepagents or hermes")
        if not isinstance(image, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_./:@-]{1,220}", image):
            raise ValueError("Provide an explicit safe local image reference")
        if not isinstance(args.get("build", False), bool):
            raise ValueError("build must be a boolean")
        command = [
            sys.executable,
            str(ROOT / "integrations/platform/package_agent.py"),
            "--harness",
            harness,
            "--image",
            image,
        ]
        if args.get("build"):
            command.append("--build")
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), 840)
        except BaseException:
            if process.returncode is None:
                process.kill()
            await process.wait()
            raise
        if process.returncode:
            raise ValueError(
                "Agent image preparation failed: " + clean(stderr.decode(errors="replace")[-1200:])
            )
        output = json.loads(stdout.decode().strip().splitlines()[-1])
        bundle = ROOT / "integrations/platform/.bundle" / harness
        output["manifest"] = json.loads((bundle / "source-manifest.json").read_text())
        output["agent_config"] = str(bundle / "agent.yaml")
        output["image"] = image
        return output
    if operation == "status":
        from nemo_helix_plugin.client.errors import NotFoundError
        from nemo_helix_plugin.models.client import AsyncModelsClient

        page = await client.list_deployments()
        deployments = []
        async for deployment in page.items():
            deployments.append(clean(deployment))
            if len(deployments) >= 50:
                break
        try:
            provider = (await AsyncModelsClient.from_client(client).get_provider(name="lab-admission")).data()
            state = getattr(provider.status, "value", str(provider.status))
            provider_status = {
                "name": provider.name,
                "status": state,
                "served_models": clean(provider.served_models),
            }
        except NotFoundError:
            provider_status = {"name": "lab-admission", "status": "unconfigured", "served_models": []}
        return {
            "ready": True,
            "versions": versions(),
            "deployments": deployments,
            "model_provider": provider_status,
            "capability_note": "Reachability does not establish model, sandbox or trace readiness.",
        }
    if operation == "register":
        harness = args.get("harness")
        if harness not in {"deepagents", "hermes"}:
            raise ValueError("Choose the previously packaged deepagents or hermes bundle")
        name = name_of(args) if args.get("name") else f"singapore-learning-advisor-{harness}"
        config_path = ROOT / "integrations/platform/.bundle" / harness / "agent.yaml"
        if not config_path.is_file():
            raise ValueError("Package the selected agent bundle before registration")
        import yaml
        from nemo_agents_plugin.agent_config import AgentConfig
        from nemo_agents_plugin.agent_config_formats import validate_agent_config
        from nemo_agents_plugin.fabric.translator import translate_agent_config
        from nemo_agents_plugin.entities import ethos_fileset_name
        from nemo_fabric import Fabric
        from nemo_helix_plugin.files.client import AsyncFilesClient
        from nemo_helix_plugin.files.types import CreateFilesetRequest
        from nemo_helix_plugin.client.errors import NotFoundError

        config = yaml.safe_load(config_path.read_text())
        if config.get("name") != name:
            raise ValueError("The explicit registration name must match agent.yaml")
        selected = AgentConfig.model_validate(config)
        translated = translate_agent_config(selected)
        if harness == "hermes":
            interpreter = ROOT / "integrations/hermes/.venv/bin/python"
        else:
            interpreter = Path(sys.executable)
        if not interpreter.is_file():
            raise ValueError("Install the selected harness environment before registration preflight")
        os.environ["ADAPTER_PYTHON"] = str(interpreter)
        fabric = Fabric()
        fabric.plan(translated, base_dir=config_path.parent)
        # Image-only executables do not exist on the host. Diagnose an explicit
        # host projection of the same catalogue module; keep registered config
        # unchanged, and require separate actual image/deployment readiness.
        host_config = selected.model_copy(deep=True)
        host_server = host_config.mcp.servers["catalogue"]
        host_server.url = str(ROOT / ".venv/bin/learning-lab-courses")
        host_server.args = []
        host_server.env = {"LAB_CATALOGUE_FILE": str(ROOT / "catalogue/courses.json")}
        doctor = await fabric.doctor(translate_agent_config(host_config), base_dir=config_path.parent)
        if doctor.status == "fail":
            raise ValueError("Fabric preflight failed; registration was not attempted")
        # Native deployment stages supporting skill text from the Files service
        # even when the same file is installed in the image. Match the maintained
        # CLI's default <agent>-ethos convention, with a much smaller allowlist.
        files = AsyncFilesClient.from_client(client)
        fileset = ethos_fileset_name(name)
        source_files = ("agent.yaml", "skills/course-advisor/SKILL.md", "source-manifest.json")
        source_contents = {}
        for relative in source_files:
            source = config_path.parent / relative
            if not source.is_file() or source.is_symlink() or source.stat().st_size > 128 * 1024:
                raise ValueError("Packaged source must contain bounded regular allowlisted text files")
            source_contents[relative] = source.read_bytes()
        try:
            observed = (await client.get_agent(name=name)).data()
        except NotFoundError:
            observed = None
        if observed is not None:
            expected_config = validate_agent_config("nemo-agents-spec-v1", config)
            if observed.config_format != "nemo-agents-spec-v1" or observed.config != expected_config:
                raise ValueError(
                    "Registered configuration differs; review and remove its deployments/registration before replacing it"
                )
            try:
                listing = (await files.list_files(name=fileset)).data()
                present = {item.path.lstrip("/") for item in listing.data}
                if present != set(source_files):
                    raise ValueError("Registered source files differ from the selected bundle")
                for relative, content in source_contents.items():
                    response = await files.download_file(name=fileset, path=relative)
                    if await response.read() != content:
                        raise ValueError("Registered source files differ from the selected bundle")
            except (NotFoundError, ValueError) as exc:
                raise ValueError(
                    "Registered source differs; review and remove its deployments/registration before replacing it"
                ) from exc
            return {
                "agent": clean(observed),
                "registered": True,
                "registration_reused": True,
                "source_fileset": f"{client.workspace}/{fileset}",
                "source_files": list(source_files),
                "host_contract_check": clean(doctor),
                "image_readiness_verified": False,
            }
        await files.create_fileset(
            body=CreateFilesetRequest(
                name=fileset, description="Packaged learning-lab agent and course skill"
            ),
            exist_ok=True,
        )
        for relative, content in source_contents.items():
            await files.upload_file(name=fileset, path=relative, content=content)
        response = await client.register_agent(
            body=RegisterAgentRequest(
                name=name,
                config=config,
                config_format="nemo-agents-spec-v1",
                description=config.get("description", ""),
            )
        )
        created = response.data()
        observed = (await client.get_agent(name=name)).data()
        return {
            "agent": clean(observed),
            "registered": bool(created),
            "registration_reused": False,
            "host_contract_check": clean(doctor),
            "source_fileset": f"{client.workspace}/{fileset}",
            "source_files": list(source_files),
            "image_readiness_verified": False,
            "bundle_delivery": "Supporting code and skills must be installed in the selected image.",
        }
    if operation == "agent":
        return {"agent": clean((await client.get_agent(name=name_of(args))).data())}
    if operation == "deploy":
        image = args.get("image")
        if not isinstance(image, str) or not image or any(c.isspace() for c in image):
            raise ValueError("Provide the exact previously built and accessible image reference")
        mode = args.get("mode", "openshell")
        if mode not in {"openshell", "docker"}:
            raise ValueError("This lab supports explicit openshell or docker Platform deployment")
        default_environment = (
            "lab-catalogue-preset" if mode == "openshell" else "lab-catalogue-context-docker"
        )
        environment = args.get("environment") or f"{client.workspace}/{default_environment}"
        if environment is not None and not isinstance(environment, str):
            raise ValueError("Select a stored workspace-qualified AgentEnvironment")
        body = CreateAgentDeploymentRequest(
            agent=name_of(args, "agent"),
            name=name_of(args),
            deployment_mode=mode,
            image=image,
            environment=environment,
        )
        deployment = (await client.create_deployment(body=body)).data()
        return {
            "deployment": clean(deployment),
            "ready": deployment.status == "running",
            "next": "Poll deployment status; no inference has been performed.",
        }
    if operation == "deployment":
        result = (await client.get_deployment(name=name_of(args))).data()
        return {"deployment": clean(result), "ready": result.status == "running"}
    if operation == "logs":
        tail = args.get("tail", 100)
        if not isinstance(tail, int) or not 1 <= tail <= 500:
            raise ValueError("Log tail must be 1 through 500")
        result = {
            "logs": clean(
                (
                    await client.get_deployment_logs(
                        name=name_of(args),
                        query_params={"tail": tail},
                    )
                ).data()
            )
        }
        if args.get("session_id"):
            from session_drain import resolve_session, session_identity as native_session_identity
            from nemo_helix_plugin.intake.client import AsyncIntakeClient
            from nemo_helix_plugin.client.errors import NemoClientError

            session = await resolve_session(client, session_identity({"session_id": args["session_id"]}))
            deployment = (await client.get_deployment(name=name_of(args))).data()
            if session.deployment_id not in {deployment.id, deployment.entity_id} - {None, ""}:
                raise ValueError("Platform session does not belong to the requested deployment")
            identities = native_session_identity(session)
            native_uuid = identities["session_uuid"]
            intake = AsyncIntakeClient.from_client(client)
            evidence = {
                "source": "native-helix-intake",
                "session_identity": identities,
                "status": "no_records_observed",
                "traces": [],
                "spans": [],
                "limit_per_kind": 100,
                "truncated": False,
                "raw_relay_file_exported": False,
            }
            try:
                for key, method in (("traces", intake.list_traces), ("spans", intake.list_spans)):
                    page = await method(
                        query_params={
                            "filter": {"session_id": native_uuid},
                            "mode": "detailed",
                            "page_size": 100,
                        }
                    )
                    async for record in page.items():
                        if record.session_id != native_uuid:
                            raise ValueError("Intake returned a record outside the selected session")
                        evidence[key].append(clean(record))
                        if len(evidence[key]) >= 100:
                            evidence["truncated"] = True
                            break
                if evidence["traces"] or evidence["spans"]:
                    evidence["status"] = "observed"
            except NemoClientError as exc:
                evidence["status"] = "unavailable"
                evidence["error"] = f"Intake read failed ({type(exc).__name__})"
            deployment_config = deployment.config if isinstance(deployment.config, dict) else {}
            annotate_intake_correlation(evidence, deployment_config)
            result["intake"] = evidence
        return result
    if operation == "sessions_create":
        from session_drain import session_identity as native_session_identity

        deployment = (await client.get_deployment(name=name_of(args, "deployment"))).data()
        if deployment.status != "running":
            raise ValueError("Wait for the named deployment to reach running")
        identity = deployment.id or deployment.entity_id
        if not identity:
            raise ValueError("Deployment response omitted its immutable identity")
        # Validate the immutable deployment snapshot before creating a session.
        config = deployment.config if isinstance(deployment.config, dict) else {}
        harness_name = config.get("default_harness")
        harness = config.get("harnesses", {}).get(harness_name, {})
        if harness.get("kind") not in {"deepagents", "hermes"}:
            raise ValueError("Deployment snapshot must identify a supported Deep Agents or Hermes harness")
        environment_metadata = config.get("environment", {}).get("metadata", {})
        catalogue_env = config.get("mcp", {}).get("servers", {}).get("catalogue", {}).get("env", {})
        preferences_mode = environment_metadata.get("preferences_mode")
        if (
            preferences_mode is None
            and catalogue_env.get("LAB_PREFERENCES_URL")
            and catalogue_env.get("LAB_REQUIRE_PREFERENCES") == "1"
        ):
            preferences_mode = "trusted-callback"
        session = (
            await client.create_session(
                body=CreateSessionRequest(
                    deployment_id=identity,
                    name=name_of(args) if args.get("name") else None,
                )
            )
        ).data()
        return {
            "session": clean(session),
            "session_identity": native_session_identity(session),
            "deployment": {
                "id": identity,
                "name": deployment.name,
                "agent": deployment.agent,
                "harness": harness_name,
                "harness_kind": harness.get("kind"),
                "adapter_id": harness.get("adapter_id") or config.get("harness", {}).get("adapter_id"),
                "preferences_mode": preferences_mode,
                "frozen_preferences": environment_metadata.get("frozen_preferences"),
                "preferences_sha256": environment_metadata.get("preferences_sha256"),
            },
        }
    if operation == "invoke":
        from session_drain import resolve_session, session_identity as native_session_identity

        text, session_id = args.get("input"), args.get("session_id")
        if not isinstance(text, str) or not 1 <= len(text) <= 12000:
            raise ValueError("Input must contain 1 through 12000 characters")
        if not isinstance(session_id, str) or not 1 <= len(session_id) <= 100:
            raise ValueError("Create a Platform session before invoking an episode")
        session = await resolve_session(client, session_id)
        deployment_name = name_of(args, "deployment")
        deployment = (await client.get_deployment(name=deployment_name)).data()
        deployment_ids = {deployment.id, deployment.entity_id} - {None, ""}
        if not session.deployment_id or session.deployment_id not in deployment_ids:
            raise ValueError("Platform session does not belong to the requested deployment")
        identities = native_session_identity(session)
        scoped = client.with_options(
            headers={"X-Nemo-Session-Id": identities["header_identity"]}, timeout=150
        )
        result = (
            await scoped.invoke_deployment(
                name=deployment_name,
                body=InvokeAgentRequest(messages=[{"role": "user", "content": text}], stream=False),
            )
        ).data()
        return {
            "response": clean(result),
            "session_id": identities["resource_name"],
            "session_identity": identities,
        }
    if operation == "sessions_close":
        from session_drain import close_session

        return clean(
            await close_session(
                client,
                session_identity(args),
                required_runtime_cleanup=args.get("require_runtime_drain", False),
            )
        )
    if operation == "sessions_recover":
        from native_cleanup import recover_session

        return clean(
            await recover_session(client, session_identity(args), receipt_path=recovery_receipt(args))
        )
    if operation == "undeploy":
        await client.delete_deployment(name=name_of(args))
        return {
            "deletion_requested": True,
            "name": args["name"],
            "note": "Deletion is asynchronous. Reconcile absence before reporting sandbox removal.",
        }
    if operation == "delete_agent":
        await client.delete_agent(name=name_of(args))
        return {"registration_deleted": True, "name": args["name"], "image_retained": True}
    raise ValueError("Unsupported Platform operation")


async def run(request: dict) -> dict:
    if request.get("version") != 1:
        raise ValueError("Unsupported Platform bridge protocol")
    observed = versions()
    if observed != PINS:
        raise ValueError(f"Platform environment version mismatch: observed {observed}; required {PINS}")
    from nemo_helix_plugin.agents.client import AsyncAgentsClient
    from nemo_helix_plugin.client.types import RetryPolicy

    platform = request["platform"]
    token_name = platform.get("token_env")
    token = os.getenv(token_name) if token_name else None
    if request["operation"] != "package" and token_name and not token:
        raise ValueError("The selected Platform credential is missing")
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with AsyncAgentsClient(
        base_url=platform["base_url"],
        workspace=platform["workspace"],
        default_headers=headers,
        retry=RetryPolicy(max_retries=0),
        timeout=15,
    ) as client:
        args = {**request.get("arguments", {}), "target": platform.get("target", "local")}
        return await execute(client, request["operation"], args)


def main():
    try:
        request = json.loads(sys.stdin.buffer.read(128 * 1024 + 1))
        with redirect_stdout(sys.stderr):
            result = asyncio.run(run(request))
        response = {"ok": True, "result": clean(result)}
        code = 0
    except Exception as exc:
        # SDK exception strings can include request credentials or remote bodies.
        from nemo_helix_plugin.client.errors import NemoHTTPError

        if isinstance(exc, NemoHTTPError):
            # Keep only structured human-readable errors; never echo submitted
            # values, request headers, arbitrary bodies or validation 'input'.
            body = exc.body if isinstance(exc.body, dict) else {}
            detail = body.get("detail")
            if isinstance(detail, dict):
                detail = {
                    key: detail[key]
                    for key in ("error", "code", "message")
                    if isinstance(detail.get(key), str)
                }
            elif not isinstance(detail, str):
                detail = {
                    key: body[key] for key in ("error", "code", "message") if isinstance(body.get(key), str)
                }
            safe = f"{type(exc).__name__} HTTP{exc.status_code}: " + (
                json.dumps(clean(detail)) if detail else "Platform rejected the operation"
            )
        else:
            safe = (
                str(exc)
                if isinstance(exc, (ValueError, FileNotFoundError))
                else f"{type(exc).__name__}: Platform operation failed; inspect its deployment and service logs"
            )
        response, code = {"ok": False, "error": clean(safe[:1200])}, 1
    print(json.dumps(response))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
