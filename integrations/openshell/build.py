"""Build a reusable agent/tool image from an allowlisted context, never a persona."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FILES = ('__init__.py', 'settings.py', 'catalogue.py', 'course_mcp.py', 'target.py',
                 'fabric_target.py', 'inference.py', 'outcomes.py', 'evidence.py',
                 'runtime_profiles.py', 'sandbox_runtime.py')


def source_manifest() -> dict:
    files = [ROOT / name for name in ("pyproject.toml", "uv.lock", "integrations/openshell/Dockerfile")]
    files.extend(ROOT / 'src/learning_lab' / name for name in RUNTIME_FILES)
    for name in ("catalogue", "runtime-skills"):
        files.extend(p for p in (ROOT / name).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    return {"version": 1, "files": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(files)},
            "contains_personas": False, "contains_credentials": False}


def build(image: str) -> dict:
    manifest = source_manifest()
    # Do not hand Docker the repository root: ignored data and credentials must
    # never enter its context, even when a user's global ignore rules change.
    with tempfile.TemporaryDirectory(prefix="citizen-agent-image-") as temp:
        context = Path(temp)
        for relative in manifest["files"]:
            target = context / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        (context / "integrations/openshell/image-manifest.json").write_text(json.dumps(manifest))
        subprocess.run(["docker", "build", "--file", str(context / "integrations/openshell/Dockerfile"),
                        "--tag", image, str(context)], check=True)
    image_id = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True).strip()
    return {"image": image, "image_id": image_id, **manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="citizen-learning-advisor:0.3.0")
    args = parser.parse_args()
    print(json.dumps(build(args.image)))
