"""Install or audit only the pinned original Singapore NGC Extended resource.

Default: verify an existing local install; no network or inference. --download uses
the existing NGC_CLI_API_KEY and NVIDIA's authenticated org/team resource route.
It never overwrites an asset, accepts license terms, or changes local credentials.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

import httpx

from learning_lab.ngc_personas import (
    CATALOGUE_URL,
    FILENAME,
    FILES_URL,
    LICENSE_URL,
    LOCALE,
    RESOURCE,
    VERSION,
    audit_source,
    file_sha256,
    install_folder,
    verify_pinned_install,
)
from learning_lab.settings import ROOT, load_environment


def _headers(key: str, url: str) -> dict:
    headers = {"Accept-Encoding": "identity"}
    if httpx.URL(url).host == "api.ngc.nvidia.com":
        headers["Authorization"] = "Bearer " + key
    return headers


def _check_status(status: int) -> None:
    if status in (401, 403):
        raise ValueError(
            f"NGC access denied (HTTP {status}). Check this resource's signed-in catalogue access "
            "and the key's NGC Catalog/GetArtifact permissions. No license terms were accepted."
        )
    if status != 200:
        raise ValueError(f"The official NGC resource request returned HTTP {status}")


def _redirect(current: str, location: str) -> str:
    url = httpx.URL(current).join(location)
    host = url.host or ""
    allowed = any(host == domain or host.endswith("." + domain)
                  for domain in ("nvidia.com", "amazonaws.com"))
    if url.scheme != "https" or not allowed or url.userinfo:
        raise ValueError("NGC returned an unsupported download redirect")
    return str(url)


def install(root: Path = ROOT) -> dict:
    load_environment()
    key = os.getenv("NGC_CLI_API_KEY")
    if not key:
        raise ValueError("Set NGC_CLI_API_KEY locally; credentials are never written by this installer")
    folder = install_folder(root)
    asset, manifest_path, partial = folder / FILENAME, folder / "provenance.json", folder / (FILENAME + ".part")
    temporary_manifest = folder / "provenance.json.part"
    if any(path.exists() or path.is_symlink() for path in (asset, manifest_path, partial, temporary_manifest)):
        raise ValueError("An asset, provenance file or partial download already exists; refusing to overwrite it")
    folder.mkdir(parents=True, mode=0o700, exist_ok=True)
    with httpx.Client(timeout=httpx.Timeout(120, connect=20), follow_redirects=False) as client:
        metadata_response = client.get(FILES_URL, headers=_headers(key, FILES_URL))
        _check_status(metadata_response.status_code)
        metadata = metadata_response.json()
        files = metadata.get("recipeFiles", [])
        if len(files) != 1 or files[0].get("path") != FILENAME:
            raise ValueError("The pinned Singapore resource has an unexpected file inventory")
        size = files[0].get("sizeInBytes")
        if type(size) is not int or size <= 0:
            raise ValueError("NGC did not provide a valid original file size")
        url = FILES_URL + "/" + FILENAME
        written = 0
        for _ in range(6):
            with client.stream("GET", url, headers=_headers(key, url)) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    url = _redirect(url, response.headers.get("location", ""))
                    continue
                _check_status(response.status_code)
                if "json" in response.headers.get("content-type", ""):
                    raise ValueError("NGC returned metadata instead of the parquet asset")
                descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(descriptor, "wb") as target:
                    for chunk in response.iter_bytes(1024 * 1024):
                        written += len(chunk)
                        if written > size:
                            raise ValueError("Downloaded content exceeds the original NGC file size")
                        target.write(chunk)
                    target.flush()
                    os.fsync(target.fileno())
                break
        else:
            raise ValueError("NGC download exceeded the redirect limit")
    if written != size:
        raise ValueError("Downloaded content does not match the original NGC file size")
    audit = audit_source(partial)
    if not audit["ready"]:
        raise ValueError("Original Singapore source failed its ID/OCEAN completeness audit")
    manifest = {
        "format": "persona-lab-ngc-install-v1", "resource": RESOURCE, "version": VERSION,
        "locale": LOCALE, "filename": FILENAME, "size_bytes": size,
        "sha256": file_sha256(partial), "digest_basis": "locally measured, not an NVIDIA signature",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "ngc_file_created_at": files[0].get("createdDate"), "source_url": FILES_URL + "/" + FILENAME,
        "catalogue_url": CATALOGUE_URL, "license_url": LICENSE_URL, "audit": audit,
    }
    # A hard link installs the complete original atomically and cannot overwrite a target.
    os.link(partial, asset, follow_symlinks=False)
    partial.unlink()
    descriptor = os.open(temporary_manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as target:
        json.dump(manifest, target, indent=2)
        target.write("\n")
        target.flush()
        os.fsync(target.fileno())
    os.link(temporary_manifest, manifest_path, follow_symlinks=False)
    temporary_manifest.unlink()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download version 0.0.1; never overwrite originals")
    args = parser.parse_args()
    try:
        if args.download:
            result = install()
        else:
            result = verify_pinned_install(ROOT)
        print(json.dumps({key: result[key] for key in ("resource", "version", "size_bytes", "sha256", "audit")},
                         indent=2))
        return 0
    except (OSError, ValueError, httpx.HTTPError, KeyError) as error:
        # HTTP exceptions may include signed URLs; emit only fixed application errors or their type.
        message = str(error) if type(error) is ValueError else type(error).__name__
        print("Singapore NGC install/audit failed: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
