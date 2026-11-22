"""Prepare or build a reproducible, minimal Helix/OpenShell agent bundle.

By default prepares source and Dockerfile only. --build builds a local image;
publishing is always a separate explicit operator action.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from presets import preset_bytes, preset_metadata


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
HERMES_COMMIT = "b200f5bc60e31588ba2cb60e288029c4a54ba5fa"
GENERATED_FILES = {
    "agent.yaml",
    "pyproject.toml",
    "Dockerfile",
    ".dockerignore",
    "source-manifest.json",
    "install_hermes.py",
    "patch_mcp_context.py",
    "catalogue/courses.json",
    "skills/course-advisor/SKILL.md",
    "scenarios/photography/preferences.json",
    "scenarios/photography/preferences.sha256",
    "src/learning_lab/__init__.py",
    "src/learning_lab/catalogue.py",
    "src/learning_lab/course_mcp.py",
    "src/learning_lab/evidence.py",
    "src/learning_lab/settings.py",
    "src/learning_lab/retail_policy.py",
}


def prepare_bundle(harness: str, scenario_id='photography') -> Path:
    if harness not in {"deepagents", "hermes"}:
        raise ValueError("Choose deepagents or hermes")
    if scenario_id not in {'photography', 'dreamjob'} or scenario_id == 'dreamjob' and harness != 'deepagents':
        raise ValueError('Choose the photography or retail Deep Agents managed preset')
    target = HERE / '.bundle' / (harness if scenario_id == 'photography' else 'dreamjob-' + harness)
    allowed = GENERATED_FILES | (
        {"hermes-managed/config.yaml", "hermes-python.sh"} if harness == "hermes" else set()
    )
    allowed |= {'scenarios/dreamjob/preferences.json', 'scenarios/dreamjob/preferences.sha256'}
    if target.is_symlink() or target.parent.is_symlink():
        raise ValueError("Generated image bundle paths cannot be symbolic links")
    if target.exists():
        for path in target.rglob("*"):
            if path.is_symlink() or (path.is_file() and path.relative_to(target).as_posix() not in allowed):
                raise ValueError(
                    "Generated image bundle has unexpected files; move them outside before packaging"
                )
    package = target / "src/learning_lab"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text("")
    # Copy an explicit allowlist; never copy .env, personas, runs or the root
    # dependency manifest (which would pull UserSim into the Platform image).
    copied = {}
    for name in ("catalogue.py", "course_mcp.py", "evidence.py", "settings.py", *(['retail_policy.py'] if scenario_id == 'dreamjob' else [])):
        source = ROOT / "src/learning_lab" / name
        shutil.copyfile(source, package / name)
        copied[f"src/learning_lab/{name}"] = hashlib.sha256(source.read_bytes()).hexdigest()
    catalogue = target / "catalogue"
    catalogue.mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "catalogue/courses.json", catalogue / "courses.json")
    if scenario_id == 'dreamjob':
        sys.path.insert(0, str(ROOT / 'src'))
        from learning_lab.catalogue import Course
        combined = json.loads((catalogue / 'courses.json').read_text())
        supplement = json.loads((ROOT / 'catalogue/retail-supplement.json').read_text())
        combined['courses'] += [Course.model_validate(row).model_dump(mode='json') for row in supplement['courses']]
        combined['notice'] = 'Mixed dated sources: inspect each course captured_on; Scenario 3 adds the verified SMU listing.'
        (catalogue / 'courses.json').write_text(json.dumps(combined, indent=2) + '\n')
    skill = target / "skills/course-advisor"
    skill.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "runtime-skills/course-advisor/SKILL.md", skill / "SKILL.md")
    preset = target / 'scenarios' / scenario_id
    preset.mkdir(parents=True, exist_ok=True)
    (preset / "preferences.json").write_bytes(preset_bytes(scenario_id))
    (preset / "preferences.sha256").write_text(preset_metadata(scenario_id)["preferences_sha256"] + "\n")
    if harness == "hermes":
        managed = target / "hermes-managed"
        managed.mkdir(exist_ok=True)
        managed_source = ROOT / "integrations/hermes/managed/config.yaml"
        shutil.copyfile(managed_source, managed / "config.yaml")
        copied["hermes-managed/config.yaml"] = hashlib.sha256(managed_source.read_bytes()).hexdigest()
        launcher = HERE / "hermes_python.sh"
        shutil.copyfile(launcher, target / "hermes-python.sh")
        copied["hermes-python.sh"] = hashlib.sha256(launcher.read_bytes()).hexdigest()
    # The shared settings module resolves ROOT to /workspace in the installed
    # source image. Explicit LAB_CATALOGUE_FILE below fixes the data boundary.
    project = """[project]
name = "learning-lab-deployed-catalogue"
version = "0.2.0"
requires-python = ">=3.12,<3.13"
dependencies = [
 "pydantic==2.14.3", "mcp==1.30.0", "python-dotenv==1.2.4", "httpx==0.28.1",
 "nemo-fabric==0.6.1", "nemo-fabric-runtime==0.6.1",
 "nemo-fabric-adapter-contract==0.6.1", "nemo-fabric-adapters-common==0.6.1",
 "nemo-fabric-adapters-deepagents==0.6.1", "nemo-fabric-adapters-hermes==0.6.1",
 "nemo-relay==0.11.0",
]
[project.scripts]
learning-lab-courses = "learning_lab.course_mcp:main"
[build-system]
requires = ["hatchling==1.30.1"]
build-backend = "hatchling.build"
[tool.hatch.build.targets.wheel]
packages = ["src/learning_lab"]
"""
    (target / "pyproject.toml").write_text(project)
    import yaml

    config = yaml.safe_load((ROOT / "agents/learning-advisor/agent.yaml").read_text())
    config["name"] = f"singapore-learning-advisor-{harness}"
    if scenario_id == 'dreamjob':
        config['name'] = 'citizen-retail-advisor-deepagents-v1'
    config["default_harness"] = harness
    config["harnesses"] = {harness: {"kind": harness}}
    config["models"] = {
        "default": {
            "provider": "openai-compatible",
            "model": "lab-advisor-fixed",
            "temperature": 0.0,
            "max_tokens": 1024,
        }
    }
    config["environment"] = {
        "workspace": "./workspace",
        "artifacts": "./artifacts",
        "env": {"LAB_CATALOGUE_FILE": "/workspace/catalogue/courses.json"},
    }
    config["telemetry"] = {"enabled": True, "provider": "relay", "output_dir": "./artifacts/relay"}
    config["mcp"] = {
        "servers": {
            "catalogue": {
                "transport": "stdio",
                "url": "/workspace/.venv/bin/learning-lab-courses",
                "env": {"LAB_CATALOGUE_FILE": "/workspace/catalogue/courses.json",
                        'LAB_MCP_EVIDENCE_FILE': '/workspace/artifacts/mcp-tools-list.jsonl'},
            }
        }
    }
    if scenario_id == 'dreamjob':
        from learning_lab.retail_policy import instructions
        config['harnesses'][harness]['settings'] = {'reasoning_effort': 'none'}
        config['models']['default']['model'] = 'citizen-retail-advisor'
        config['instructions']['system']['content'] += instructions() + (
            '\nThis is a fresh managed retail-learning condition using explicitly selected public constraints. '
            'Use the full published fee and actual duration. A brand ambition does not establish endorsement '
            'or a job outcome. Income is not a training budget or evidence of affordability/funding eligibility. '
            'Respect the explicit S$3000 total training limit and weekend-only availability. Unknown fees '
            'or schedules remain unconfirmed; never promise that an alternative fits either. '
            'Compare the SMU programme with shorter analysis/Excel options using returned facts and official links.'
        )
        config['mcp']['servers']['catalogue']['env'].update(
            LAB_PREFERENCES_PRESET_FILE='/workspace/scenarios/dreamjob/preferences.json',
            LAB_PREFERENCES_PRESET_SHA256=preset_metadata(scenario_id)['preferences_sha256'],
            LAB_REQUIRE_PREFERENCES='1')
    if harness == "hermes":
        config["harnesses"][harness]["settings"] = {
            "reasoning_config": {"enabled": False, "effort": "none"},
            "save_trajectories": False,
        }
        config["tools"] = {"enabled": ["mcp-catalogue"]}
    else:
        config["harnesses"][harness]["settings"] = {"reasoning_effort": "none"}
        config["tools"] = {"enabled": ["search_courses", "get_course_details", "compare_courses"]}
    (target / "agent.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
    shutil.copyfile(HERE / "install_hermes.py", target / "install_hermes.py")
    shutil.copyfile(HERE / "patch_mcp_context.py", target / "patch_mcp_context.py")
    (target / "source-manifest.json").write_text(
        json.dumps(
            {
                "harness": harness,
                "sources": copied,
                "hermes_commit": HERMES_COMMIT,
                "public_preset": preset_metadata(scenario_id),
                "scenario_id": scenario_id,
                "catalogue_sha256": hashlib.sha256((catalogue / 'courses.json').read_bytes()).hexdigest(),
                "stage": "source-prepared",
                "built": False,
                "deployed": False,
            },
            indent=2,
        )
    )
    return target


def customize_dockerfile(path: Path, harness: str, scenario_id='photography'):
    text = path.read_text()
    if harness == "hermes":
        old_commit = "bf0203a794a07aac3ff764972ab9087baa4e4f4e"
        old_installer = "-m nemo_agents_plugin.container.install_hermes"
        if text.count(old_commit) != 1 or text.count(old_installer) != 1:
            raise RuntimeError(
                "Helix packaging template changed; inspect it before updating the compatibility patch"
            )
        text = text.replace(old_commit, HERMES_COMMIT).replace(old_installer, "/workspace/install_hermes.py")
    marker = "\nUSER agent\n"
    if text.count(marker) != 1:
        raise RuntimeError("Helix user boundary changed; inspect the packaging template")
    patch = "\nRUN /workspace/.venv/bin/python /workspace/patch_mcp_context.py\n"
    if harness == "hermes":
        patch += "RUN /opt/hermes-venv/bin/python /workspace/patch_mcp_context.py --harness hermes\n"
        patch += (
            "RUN test -L /workspace/.venv/bin/python && "
            "mv /workspace/.venv/bin/python /workspace/.venv/bin/python-real && "
            "cp /workspace/hermes-python.sh /workspace/.venv/bin/python && "
            "chmod 0555 /workspace/.venv/bin/python\n"
        )
        patch += "ENV HERMES_MANAGED_DIR=/workspace/hermes-managed HERMES_STREAM_RETRIES=0\n"
    # Native OpenShell needs its WORKDIR writable for staging. Root-owned
    # immutable children plus a sticky workdir prevent replacing packaged code
    # or its trusted preset while keeping explicit scratch locations writable.
    patch += """RUN chown -R root:root /workspace && chmod -R a-w /workspace && \\
    mkdir -p /workspace/workspace /workspace/artifacts /workspace/scratch && \\
    chown -R agent:sandbox /workspace/workspace /workspace/artifacts /workspace/scratch && \\
    chmod -R u+rwX,g+rwX /workspace/workspace /workspace/artifacts /workspace/scratch && \\
    chmod 2770 /workspace/workspace /workspace/artifacts /workspace/scratch && \\
    chown root:sandbox /workspace && chmod 1775 /workspace && \\
    usermod -a -G sandbox agent
"""
    if scenario_id == 'dreamjob':
        patch += "RUN printf 'public non-secret boundary fixture\\n' > /lab-denied.txt && chmod 0444 /lab-denied.txt\n"
    text = text.replace(marker, patch + marker)
    path.write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", choices=["deepagents", "hermes"], required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--build", action="store_true")
    parser.add_argument('--scenario', choices=['photography', 'dreamjob'], default='photography')
    args = parser.parse_args()
    bundle = prepare_bundle(args.harness, args.scenario)
    nemo = HERE / ".venv/bin/nemo"
    if not nemo.is_file():
        raise RuntimeError(
            "Install the locked isolated Platform environment first; source bundle was preserved"
        )
    subprocess.run(
        [
            str(nemo),
            "agents",
            "package",
            "--agent",
            str(bundle / "agent.yaml"),
            "--pyproject",
            str(bundle / "pyproject.toml"),
            "--python-version",
            "3.12",
            "--sandbox-runtime",
            "openshell",
            "--tag",
            args.image,
            "--no-build",
        ],
        check=True,
        env={**os.environ, "NEMO_TELEMETRY_ENABLED": "false"},
    )
    customize_dockerfile(bundle / "Dockerfile", args.harness, args.scenario)
    if args.build:
        subprocess.run(["docker", "build", "--tag", args.image, str(bundle)], check=True)
        manifest = json.loads((bundle / "source-manifest.json").read_text())
        manifest.update(stage="image-built", built=True, image=args.image)
        (bundle / "source-manifest.json").write_text(json.dumps(manifest, indent=2))
    print(
        json.dumps(
            {
                "bundle": str(bundle),
                "dockerfile": str(bundle / "Dockerfile"),
                "built": args.build,
                "published": False,
                "registered": False,
                "deployed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
