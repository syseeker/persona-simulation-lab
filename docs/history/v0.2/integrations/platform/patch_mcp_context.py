"""Exact Fabric 0.6.1 image workaround for trusted MCP context indirection.

Expand one allowlisted env slot at adapter runtime. OpenShell supplies its issued
opaque placeholder; this never manufactures a credential handle or copies all
of the agent's environment into the catalogue server.
"""

import argparse
from pathlib import Path


PATCHES = {
    "nemo_fabric_adapters/deepagents/adapter.py": (
        'connection["env"] = env',
        'connection["env"] = {key: os.path.expandvars(value) if key == "LAB_PREFERENCES_TOKEN" else value for key, value in env.items()}',
    ),
    "nemo_fabric_adapters/hermes/configuration.py": (
        '"env": server.env or None,',
        '"env": {key: os.path.expandvars(value) if key == "LAB_PREFERENCES_TOKEN" else value for key, value in server.env.items()} or None,',
    ),
}


def patch(site_packages: Path, harness: str = "all") -> None:
    for name, (before, after) in PATCHES.items():
        if harness != "all" and f"/{harness}/" not in name:
            continue
        path = site_packages / name
        source = path.read_text()
        if source.count(before) != 1:
            raise RuntimeError(f"Fabric MCP compatibility context changed: {name}")
        path.write_text(source.replace(before, after))


if __name__ == "__main__":
    import site

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-packages", type=Path, default=Path(site.getsitepackages()[0]))
    parser.add_argument("--harness", choices=["all", "deepagents", "hermes"], default="all")
    args = parser.parse_args()
    patch(args.site_packages, args.harness)
