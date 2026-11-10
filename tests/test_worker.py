import json
import subprocess
import sys

from learning_lab.settings import ROOT


def test_worker_rejects_malformed_requests_then_serves_status():
    requests = ["not-json", json.dumps({"version": 1, "id": "test", "method": "status", "params": {}})]
    result = subprocess.run(
        [sys.executable, "-m", "learning_lab.worker"],
        input="\n".join(requests) + "\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        timeout=25,
    )
    assert result.returncode == 0, result.stderr[-1000:]
    lines = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(lines) == 2 and lines[0]["error"]["code"] == "invalid_request"
    assert lines[1]["id"] == "test" and lines[1]["result"]["catalogue_count"] == 12
    assert "NVIDIA_API_KEY" not in result.stdout
