"""The advisor owns real tools; UserSim only receives its final public reply."""

from __future__ import annotations

from contextlib import AsyncExitStack
import json
from pathlib import Path
import sys
import uuid

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.agents.middleware import AgentMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from .catalogue import Preferences, freeze_catalogue
from .course_mcp import TOOL_NAMES
from .inference import Gateway
from .settings import ROOT

ALLOWED_TOOLS = set(TOOL_NAMES)


class ReadOnlyTools(AgentMiddleware):
    """Apply the allowlist both to model exposure and to attempted execution."""

    async def awrap_model_call(self, request, handler):
        tools = [t for t in request.tools if getattr(t, "name", None) in ALLOWED_TOOLS]
        return await handler(request.override(tools=tools))

    async def awrap_tool_call(self, request, handler):
        if request.tool_call["name"] not in ALLOWED_TOOLS:
            raise ValueError("This advisor only has read-only course tools")
        return await handler(request)


def system_prompt(strategy: str) -> str:
    skill = (ROOT / "runtime-skills/course-advisor/SKILL.md").read_text().split("---", 2)[-1]
    instruction = (
        "Offer a concise shortlist and state the unresolved constraints."
        if strategy == "concise"
        else "Ask one useful clarification when key constraints are missing, then recommend suitable options. "
        "Before answering, check course IDs and official links. Separate the listed fee, known extras "
        "and unknown costs. When extra_cost_sgd is null, explicitly say extras are unknown; "
        "never describe the listed amount as a confirmed total or say there are no extra fees."
    )
    return f"You are a Singapore learning and community-class advisor. Keep replies under 180 words, list at most three courses, and include official links. Use short paragraphs or bullets. {instruction}\n{skill}"


class DirectTarget:
    def __init__(
        self,
        gateway: Gateway,
        workspace: Path,
        model: str,
        strategy="concise",
        relay=False,
        catalogue_path=None,
    ):
        self.gateway, self.workspace, self.model = gateway, workspace, model
        self.strategy, self.relay = strategy, relay
        self.stack = AsyncExitStack()
        self.thread_id = str(uuid.uuid4())
        self.agent = None
        self.catalogue_path = catalogue_path or workspace.parent / "catalogue-snapshot.json"

    async def __aenter__(self):
        try:
            return await self._start()
        except BaseException:
            await self.stack.aclose()
            raise

    async def _start(self):
        self.workspace.mkdir(parents=True, exist_ok=True)
        freeze_catalogue(self.catalogue_path)
        client = MultiServerMCPClient(
            {
                "catalogue": {
                    "transport": "stdio",
                    "command": sys.executable,
                    "args": ["-m", "learning_lab.course_mcp"],
                    "cwd": str(ROOT),
                    "env": {
                        "LAB_PREFERENCES_FILE": str(self.workspace.parent / "preferences.json"),
                        "LAB_CATALOGUE_FILE": str(self.catalogue_path),
                    },
                }
            }
        )
        session = await self.stack.enter_async_context(client.session("catalogue"))
        tools = await load_mcp_tools(session)
        for tool in tools:
            tool.handle_tool_error = True
        names = {tool.name for tool in tools}
        if names != ALLOWED_TOOLS:
            raise ValueError(f"Unexpected MCP tool surface: {sorted(names)}")
        kwargs = dict(
            model=ChatOpenAI(
                model=self.model,
                base_url=self.gateway.url,
                api_key=self.gateway.key,
                max_tokens=1024,
                max_retries=0,
                temperature=0,
                reasoning_effort="none",
            ),
            tools=tools,
            system_prompt=system_prompt(self.strategy),
            middleware=[ReadOnlyTools()],
            subagents=[],
            checkpointer=InMemorySaver(),
            backend=FilesystemBackend(root_dir=str(self.workspace), virtual_mode=True),
            name="learning-advisor",
        )
        if self.relay:
            from nemo_relay.integrations.deepagents import add_nemo_relay_integration

            kwargs = add_nemo_relay_integration(kwargs)
        self.agent = create_deep_agent(**kwargs)
        return self

    async def reply(self, message: str, preferences: Preferences | None = None) -> dict:
        self.gateway.tool_rounds = 0
        path = self.workspace.parent / "preferences.json"
        if preferences:
            path.write_text(preferences.model_dump_json())
        else:
            path.unlink(missing_ok=True)
        content = message
        if preferences is not None:
            content += "\nLAB_PREFERENCES=" + preferences.model_dump_json(exclude_none=True)
        config = {"configurable": {"thread_id": self.thread_id}, "recursion_limit": 24}
        before = len((await self.agent.aget_state(config)).values.get("messages", []))
        if self.relay:
            import nemo_relay
            from nemo_relay.integrations.deepagents import NemoRelayDeepAgentsCallbackHandler

            config["callbacks"] = [NemoRelayDeepAgentsCallbackHandler()]
            with nemo_relay.scope.scope("course-advisor-request", nemo_relay.ScopeType.Agent):
                result = await self.agent.ainvoke(
                    {"messages": [{"role": "user", "content": content}]}, config
                )
            await nemo_relay.subscribers.flush_async()
        else:
            result = await self.agent.ainvoke({"messages": [{"role": "user", "content": content}]}, config)
        new = result["messages"][before:]
        (self.workspace.parent / "target-history.json").write_text(
            json.dumps(
                [
                    {"role": m.type, "content": m.content, "tool_calls": getattr(m, "tool_calls", None)}
                    for m in result["messages"]
                ],
                indent=2,
                default=str,
            )
        )
        output = result["messages"][-1]
        if output.type != "ai" or not output.content:
            raise RuntimeError(
                "The model returned no final answer; inspect the token budget and model configuration"
            )
        return {
            "content": output.content,
            "tools": [{"name": m.name, "content": m.content} for m in new if m.type == "tool"],
            "thread_id": self.thread_id,
        }

    async def __aexit__(self, *exc):
        await self.stack.aclose()


def relay_config(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    config = folder / "plugins.toml"
    config.write_text(
        """version = 1
[[components]]
kind = "observability"
enabled = true
[components.config]
version = 4
enable_full_payloads = false
[components.config.atof]
enabled = true
[[components.config.atof.sinks]]
type = "file"
output_directory = """
        + json.dumps(str(folder))
        + """
filename = "relay.jsonl"
mode = "append"
"""
    )
    return config


def relay_evidence(folder: Path, provider_verified=False) -> dict:
    path = folder / "relay.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    starts = {e.get("uuid"): e for e in events if e.get("scope_category") == "start"}
    pairs = [
        e
        for e in events
        if e.get("scope_category") == "end"
        and e.get("uuid") in starts
        and e.get("category") == starts[e["uuid"]].get("category")
    ]
    return {
        "events": len(events),
        "paired_categories": sorted({e.get("category") for e in pairs}),
        "file": str(path.relative_to(ROOT)),
        "provider_verified": provider_verified,
    }
