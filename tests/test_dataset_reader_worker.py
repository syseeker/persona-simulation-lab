"""The read-only worker never starts the execution service or recovers saved runs."""

import io
import json
import sys

import pytest

from learning_lab import datasets, worker


@pytest.mark.asyncio
async def test_data_worker_isolates_browsing_from_execution_and_saved_run_recovery(monkeypatch):
    calls = []

    def execution_service_must_not_start():
        raise AssertionError("Read-only browsing started the execution service")

    def catalogue():
        calls.append("metadata")
        return {"datasets": [], "inference_calls": 0}

    monkeypatch.setattr(worker, "LabService", execution_service_must_not_start)
    monkeypatch.setattr(datasets, "dataset_catalogue", catalogue)
    monkeypatch.setattr(worker.logging, "basicConfig", lambda **kwargs: None)
    requests = [{"version": 1, "id": str(index), "method": method, "params": {}}
                for index, method in enumerate(("dataset_catalogue", "status", "chat", "start_run",
                                                 "start_workbench", "platform_action", "dataset_catalogue"))]
    output = io.StringIO()
    monkeypatch.setattr(sys, "stdin", io.StringIO("".join(json.dumps(item) + "\n" for item in requests)))
    monkeypatch.setattr(sys, "stdout", output)
    await worker.serve(datasets_only=True)
    replies = [json.loads(line) for line in output.getvalue().splitlines()]
    assert len(replies) == len(requests)
    assert calls == ["metadata", "metadata"]
    assert replies[0]["result"]["inference_calls"] == replies[-1]["result"]["inference_calls"] == 0
    assert all("only reads installed datasets" in reply["error"]["message"] for reply in replies[1:-1])
