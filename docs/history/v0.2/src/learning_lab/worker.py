"""Versioned JSON-lines worker. Stdout is reserved for protocol responses."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Literal

from pydantic import Field, ValidationError

from .catalogue import StrictModel, all_courses
from .service import ChatSpec, LabService, RunSpec


class Request(StrictModel):
    version: Literal[1] = 1
    id: str = Field(min_length=1, max_length=80)
    method: Literal[
        "status",
        "catalogue",
        "chat",
        "runs",
        "start_run",
        "get_run",
        "get_trace",
        "cancel_run",
        "evaluate_run",
        "stories", "sources", "source", "get_evidence", "get_artifact",
        "dataset_catalogue", "browse_personas", "sample_personas", "lock_personas",
        "start_workbench", "get_workbench", "cancel_workbench", "list_workbench",
        "runtime_profiles", "platform_action",
        "shutdown",
    ]
    params: dict = Field(default_factory=dict)


async def serve():
    protocol = sys.stdout
    sys.stdout = sys.stderr
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING, force=True)
    service = LabService()
    try:
        while True:
            line = await asyncio.to_thread(sys.stdin.readline, 1024 * 1024 + 1)
            if not line:
                break
            request_id = None
            try:
                if len(line) > 1024 * 1024:
                    raise ValueError("Worker message exceeds 1 MiB")
                raw = json.loads(line)
                request_id = raw.get("id") if isinstance(raw, dict) else None
                request = Request.model_validate(raw)
                request_id = request.id
                match request.method:
                    case "status":
                        result = service.status()
                    case "catalogue":
                        result = [c.model_dump(mode="json") for c in all_courses()]
                    case "chat":
                        result = await service.chat(ChatSpec.model_validate(request.params))
                    case "runs":
                        result = service.list_runs(request.params.get("mode"))
                    case "start_run":
                        result = await service.start_run(RunSpec.model_validate(request.params))
                    case "get_run":
                        result = service.get_run(request.params["run_id"])
                    case "get_trace":
                        result = service.get_trace(request.params["run_id"], request.params["episode_id"])
                    case "cancel_run":
                        result = await service.cancel(request.params["run_id"])
                    case "evaluate_run":
                        result = await service.evaluate_run(request.params["run_id"])
                    case "stories":
                        from .stories import list_stories
                        result = list_stories()
                    case "sources":
                        from .source_index import integration_sources
                        result = integration_sources()
                    case "source":
                        from .source_index import source_excerpt
                        result = source_excerpt(request.params["id"])
                    case "get_evidence":
                        result = service.get_evidence(**request.params)
                    case "get_artifact":
                        result = service.get_artifact(**request.params)
                    case "dataset_catalogue":
                        result = service.dataset_catalogue()
                    case "browse_personas":
                        result = service.browse_personas(request.params)
                    case "sample_personas":
                        result = service.sample_personas(request.params)
                    case "lock_personas":
                        from .datasets import lock_personas
                        result = lock_personas(**request.params)
                    case "start_workbench":
                        result = await service.start_workbench(request.params)
                    case "get_workbench":
                        result = service.get_workbench(request.params["job_id"])
                    case "cancel_workbench":
                        result = await service.cancel_workbench(request.params["job_id"])
                    case "list_workbench":
                        result = service.list_workbench()
                    case "runtime_profiles":
                        from .runtime_profiles import runtime_profiles
                        result = runtime_profiles()
                    case "platform_action":
                        result = await service.platform_action(request.params)
                    case "shutdown":
                        break
                response = {"version": 1, "id": request_id, "result": result}
            except (ValueError, ValidationError, KeyError) as exc:
                response = {
                    "version": 1,
                    "id": request_id,
                    "error": {"code": "invalid_request", "message": str(exc)[:700]},
                }
            except Exception as exc:
                logging.exception("Worker operation failed")
                response = {
                    "version": 1,
                    "id": request_id,
                    "error": {
                        "code": "operation_failed",
                        "message": f"{type(exc).__name__}: {str(exc)[:600]}",
                    },
                }
            protocol.write(json.dumps(response, default=str) + "\n")
            protocol.flush()
    finally:
        await service.close()


def main():
    asyncio.run(serve())


if __name__ == "__main__":
    main()
