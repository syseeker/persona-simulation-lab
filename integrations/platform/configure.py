"""Real Helix resource setup; callers supply endpoints, secrets stay in env.

Creating these resources does not establish deployment readiness. The default
OpenShell path uses a frozen public preset and native encrypted credential store;
dynamic context uses process-env secrets in the separately named Docker environment.
The external OpenShell provider environment is retained as an unverified option.
"""

import os
from urllib.parse import urlsplit


ALIASES = ["lab-advisor-fixed", "lab-advisor-routed", "lab-support"]


def endpoint(value: str, *, remote: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError("Provide the application bridge URL reachable from the selected Platform")
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or (remote and parsed.scheme != "https")
    ):
        raise ValueError("Bridge URLs need explicit HTTP(S), no credentials/query; remote needs HTTPS")
    return value.rstrip("/")


async def configure(client, args: dict) -> dict:
    from presets import PRESET_IMAGE_PATH, preset_metadata
    from nemo_helix_plugin.agents.types import (
        CreateEnvironmentRequest,
        EnvironmentSpecInline,
        McpFulfillment,
    )
    from nemo_helix_plugin.client.errors import NotFoundError
    from nemo_helix_plugin.models.client import AsyncModelsClient
    from nemo_helix_plugin.models.types import CreateModelProviderRequest
    from nemo_helix_plugin.secrets.client import AsyncSecretsClient
    from nemo_helix_plugin.secrets.types import HelixSecretCreateRequest
    from nemo_helix_plugin.workspaces.client import AsyncWorkspacesClient
    from nemo_helix_plugin.workspaces.types import CreateWorkspaceRequest

    remote = args.get("target") == "remote"
    provider_url = endpoint(args.get("provider_url"), remote=remote)
    preferences_url = endpoint(args.get("preferences_url"), remote=remote)
    if urlsplit(preferences_url).path != "/v1/lab/preferences":
        raise ValueError("Preferences callback must use exactly /v1/lab/preferences")
    key = os.getenv("LAB_DEPLOYMENT_GATEWAY_KEY", "")
    preferences_key = os.getenv("LAB_DEPLOYMENT_PREFERENCES_TOKEN", "")
    if min(len(key), len(preferences_key)) < 24 or key == preferences_key:
        raise ValueError(
            "Set separate deployment provider and preferences secrets, at least 24 characters each"
        )
    workspace = client.workspace
    workspaces = AsyncWorkspacesClient.from_client(client)
    secrets = AsyncSecretsClient.from_client(client)
    models = AsyncModelsClient.from_client(client)
    created = []
    try:
        await workspaces.get_workspace(name=workspace)
    except NotFoundError:
        await workspaces.create_workspace(
            body=CreateWorkspaceRequest(name=workspace, description="Citizen application learning lab")
        )
        created.append("workspace")
    # Keep existing secret values private. Never overwrite a shared secret as an
    # implicit repair; a changed local key requires an explicit rotation.
    for name, value in (("lab-admission-key", key), ("lab-preferences-token", preferences_key)):
        try:
            await secrets.get_secret(name=name)
        except NotFoundError:
            await secrets.create_secret(
                body=HelixSecretCreateRequest(name=name, value=value, description="Learning lab only")
            )
            created.append("secret:" + name)
    provider_name = "lab-admission"
    try:
        provider = (await models.get_provider(name=provider_name)).data()
        if (
            provider.host_url.rstrip("/") != provider_url
            or set(provider.enabled_models or []) != set(ALIASES)
            or provider.api_key_secret_name not in {"lab-admission-key", f"{workspace}/lab-admission-key"}
        ):
            raise ValueError(
                "Existing lab-admission provider differs; explicitly reconcile it before continuing"
            )
    except NotFoundError:
        provider = (
            await models.create_provider(
                body=CreateModelProviderRequest(
                    name=provider_name,
                    host_url=provider_url,
                    # Models API resolves this field within its request's
                    # workspace; a qualified name becomes a literal slash path.
                    api_key_secret_name="lab-admission-key",
                    enabled_models=ALIASES,
                    description="Exclusive workload budget bridge, then LiteLLM and optional Switchyard",
                )
            )
        ).data()
        created.append("provider:" + provider_name)
    environments = []
    for mode in ("docker", "openshell"):
        name = "lab-catalogue-context-" + mode
        mcp = McpFulfillment(
            url="/workspace/.venv/bin/learning-lab-courses",
            env={
                "LAB_PREFERENCES_URL": preferences_url,
                "LAB_REQUIRE_PREFERENCES": "1",
                "LAB_PREFERENCES_TOKEN": "${LAB_CONTEXT_TOKEN}",
            },
        )
        settings = {}
        if mode == "docker":
            mcp.secrets = {"LAB_CONTEXT_TOKEN": f"{workspace}/lab-preferences-token"}
        else:
            settings = {
                "openshell": {
                    "providers": {
                        "lab-preferences": {
                            "profile": "lab-preferences",
                            "credentials": {"LAB_CONTEXT_TOKEN": f"{workspace}/lab-preferences-token"},
                        }
                    }
                }
            }
        body = CreateEnvironmentRequest(
            name=name,
            description=f"Read-only trusted workload context ({mode})",
            environment_spec=EnvironmentSpecInline(mcp={"catalogue": mcp}, settings=settings),
        )
        try:
            stored = (await client.get_environment(name=name)).data()
            if stored.environment_spec != body.environment_spec:
                raise ValueError(f"Existing {name} environment differs; reconcile it explicitly")
        except NotFoundError:
            await client.create_environment(body=body)
            created.append("environment:" + name)
        environments.append(f"{workspace}/{name}")
    metadata = preset_metadata()
    preset_name = "lab-catalogue-preset"
    body = CreateEnvironmentRequest(
        name=preset_name,
        description="Frozen public Saturday photography story; native OpenShell encrypted credential store",
        environment_spec=EnvironmentSpecInline(
            metadata=metadata,
            mcp={
                "catalogue": McpFulfillment(
                    url="/workspace/.venv/bin/learning-lab-courses",
                    env={
                        "LAB_PREFERENCES_PRESET_FILE": PRESET_IMAGE_PATH,
                        "LAB_PREFERENCES_PRESET_SHA256": metadata["preferences_sha256"],
                        "LAB_REQUIRE_PREFERENCES": "1",
                    },
                )
            },
        ),
    )
    try:
        stored = (await client.get_environment(name=preset_name)).data()
        if stored.environment_spec != body.environment_spec:
            raise ValueError("Existing lab-catalogue-preset differs; reconcile it explicitly")
    except NotFoundError:
        await client.create_environment(body=body)
        created.append("environment:" + preset_name)
    environments.append(f"{workspace}/{preset_name}")
    return {
        "configured": True,
        "created": created,
        "workspace": workspace,
        "provider": provider_name,
        "provider_status": str(provider.status),
        "model_aliases": ALIASES,
        "environments": environments,
        "default_environments": {
            "docker": f"{workspace}/lab-catalogue-context-docker",
            "openshell": f"{workspace}/{preset_name}",
        },
        "openshell_preset": metadata,
        "inference_calls": 0,
        "ready": False,
        "next": "Observe provider model discovery, then verify the selected runtime and catalogue context. OpenShell defaults to the public frozen preset.",
    }
