"""Offline NGC source identity, discovery and non-overwriting download contracts."""

import copy
import importlib.util
import json
from pathlib import Path

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from learning_lab import datasets, ngc_personas as ngc


def profile():
    return {
        "uuid": "fabricated-ngc-source-id", "age": 35, "sex": "Female", "country": "Singapore",
        "occupation": "Clerical Worker", "education_level": "Secondary", "district": "Fixture district",
        "persona": "A fabricated learner interested in photography.",
        **{key: json.dumps({"t_score": 62, "label": "fixture label", "description": "Fixture trait"})
           for key in ngc.OCEAN},
    }


def write_install(root, row=None):
    folder = ngc.install_folder(root)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ngc.FILENAME
    pq.write_table(pa.Table.from_pylist([row or profile()]), path)
    manifest = {
        "format": "persona-lab-ngc-install-v1", "resource": ngc.RESOURCE, "version": ngc.VERSION,
        "locale": ngc.LOCALE, "filename": ngc.FILENAME, "size_bytes": path.stat().st_size,
        "sha256": ngc.file_sha256(path), "audit": ngc.audit_source(path),
    }
    manifest_path = folder / "provenance.json"
    manifest_path.write_text(json.dumps(manifest))
    return path, manifest_path, manifest


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(datasets, "ROOT", tmp_path)
    monkeypatch.setattr(datasets, "load_environment", lambda: None)
    monkeypatch.delenv("LAB_NGC_PERSONAS_PATH", raising=False)
    monkeypatch.delenv("LAB_NGC_PERSONAS_REVISION", raising=False)
    monkeypatch.setenv("DATA_DESIGNER_MANAGED_ASSETS_PATH", str(tmp_path / "managed"))
    return tmp_path


async def test_pinned_source_discovery_lock_and_usersim_materialisation_share_originals(isolated):
    from usersim.engine.external import ProbeEpisodeRuntime

    from learning_lab.simulation import host_models, prepare_rows

    path, _, manifest = write_install(isolated)
    metadata = datasets.dataset_catalogue()["datasets"][1]
    assert metadata["ready"] and metadata["revision"] == ngc.VERSION
    assert metadata["source_sha256"] == manifest["sha256"]
    assert metadata["behaviour_audit"]["ocean"]["openness"]["valid"] == 1
    assert datasets._paths("ngc") == [path]
    locked = datasets.lock_personas("ngc", [profile()["uuid"]])
    assert locked["rows"] == [profile()] and locked["source_revision"] == ngc.VERSION
    row = prepare_rows("ngc", count=1, source_ids=locked["source_ids"], max_turns=1)[0]
    assert row["persona"] == profile() and row["source_revision"] == ngc.VERSION
    assert row["usersim_config"]["probe_options"]["learning_advisor"]["profile_only"] is False
    assert "Source behavioural fields" in row["behavior_basis"]
    assert json.loads(row["behavioral_profile"])["ocean"] == {key: 0.7 for key in ngc.OCEAN}
    runtime = ProbeEpisodeRuntime.from_resolved_row(row, models=host_models("demo"))
    try:
        assert runtime.preamble.persona == profile()
        assert runtime.preamble.behavioral_profile["ocean"] == {key: 0.7 for key in ngc.OCEAN}
        assert runtime.probe.get_user_system_prompt()
    finally:
        await runtime.close()


def test_operator_override_has_priority_and_missing_override_fails_closed(isolated, monkeypatch):
    write_install(isolated)
    explicit = isolated / "operator.parquet"
    pq.write_table(pa.Table.from_pylist([profile()]), explicit)
    monkeypatch.setenv("LAB_NGC_PERSONAS_PATH", str(explicit))
    monkeypatch.setenv("LAB_NGC_PERSONAS_REVISION", "operator-revision")
    assert ngc.resolve_ngc(isolated).path == explicit
    assert datasets.dataset_catalogue()["datasets"][1]["revision"] == "operator-revision"
    explicit.unlink()
    assert not datasets.dataset_catalogue()["datasets"][1]["ready"]
    with pytest.raises(ValueError, match="Explicit NGC persona path"):
        datasets.lock_personas("ngc", [profile()["uuid"]])
    monkeypatch.setenv("LAB_NGC_PERSONAS_PATH", "")
    assert ngc.resolve_ngc(isolated).path is None


def test_existing_managed_asset_precedes_pinned_install(isolated, monkeypatch):
    write_install(isolated)
    managed = isolated / "managed/datasets/en_SG.parquet"
    managed.parent.mkdir(parents=True)
    pq.write_table(pa.Table.from_pylist([profile()]), managed)
    assert ngc.resolve_ngc(isolated).path == managed
    assert ngc.resolve_ngc(isolated).origin == "designer-managed"
    managed.unlink()
    monkeypatch.setenv("LAB_NGC_PERSONAS_REVISION", "not-the-pinned-release")
    assert ngc.resolve_ngc(isolated).revision == ngc.VERSION


@pytest.mark.parametrize("origin", ["operator-override", "designer-managed"])
@pytest.mark.parametrize("invalid", ["all-null", "huge-score"])
def test_existing_selected_origin_is_audited_without_falling_back(isolated, monkeypatch, origin, invalid):
    write_install(isolated)
    selected = isolated / ("operator.parquet" if origin == "operator-override"
                           else "managed/datasets/en_SG.parquet")
    selected.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist([profile()]), selected)
    if origin == "operator-override":
        monkeypatch.setenv("LAB_NGC_PERSONAS_PATH", str(selected))
    assert datasets.dataset_catalogue()["datasets"][1]["ready"]
    damaged = profile()
    if invalid == "all-null":
        damaged.update({key: None for key in ngc.OCEAN})
    else:
        damaged["openness"] = json.dumps({"t_score": 10**400, "label": "fixture", "description": "Fixture"})
    pq.write_table(pa.Table.from_pylist([damaged]), selected)
    metadata = datasets.dataset_catalogue()["datasets"][1]
    assert metadata["available"] and not metadata["ready"]
    assert metadata["installation"] == origin
    assert ngc.resolve_ngc(isolated).path == selected
    counts = metadata["behaviour_audit"]["ocean"]["openness"]
    assert counts["missing" if invalid == "all-null" else "invalid"] == 1
    with pytest.raises(ValueError, match="missing or invalid"):
        datasets.sample_personas(source="ngc", count=1)
    with pytest.raises(ValueError, match="missing or invalid"):
        datasets.lock_personas("ngc", [profile()["uuid"]])


def test_oversized_source_score_counts_invalid_instead_of_raising(isolated):
    damaged = profile()
    damaged["openness"] = json.dumps({"t_score": 10**400, "label": "fixture", "description": "Fixture"})
    path, _, _ = write_install(isolated, damaged)
    audit = ngc.audit_source(path)
    assert not audit["ready"] and audit["ocean"]["openness"]["invalid"] == 1


@pytest.mark.parametrize("field,value", [
    ("version", "latest"), ("locale", "en_US"), ("resource", "unrelated/resource"),
    ("filename", "../../elsewhere.parquet"), ("size_bytes", 1), ("sha256", "0" * 64),
])
def test_inconsistent_provenance_is_not_discovered(isolated, field, value):
    _, manifest_path, manifest = write_install(isolated)
    manifest[field] = value
    manifest_path.write_text(json.dumps(manifest))
    assert ngc.resolve_ngc(isolated).path is None
    assert not datasets.dataset_catalogue()["datasets"][1]["ready"]


@pytest.mark.parametrize("manifest_content", [None, "not-json", "[]"])
def test_missing_or_malformed_provenance_does_not_activate_original(isolated, manifest_content):
    _, manifest_path, _ = write_install(isolated)
    if manifest_content is None:
        manifest_path.unlink()
    else:
        manifest_path.write_text(manifest_content)
    assert ngc.resolve_ngc(isolated).path is None


def test_changed_asset_and_fabricated_audit_cannot_reuse_cached_readiness(isolated):
    path, manifest_path, original = write_install(isolated)
    assert ngc.resolve_ngc(isolated).path == path
    changed = profile()
    changed["openness"] = '{"description":"Score missing","label":"fixture"}'
    pq.write_table(pa.Table.from_pylist([changed]), path)
    manifest = copy.deepcopy(original)
    manifest.update(size_bytes=path.stat().st_size, sha256=ngc.file_sha256(path))
    manifest_path.write_text(json.dumps(manifest))
    assert ngc.audit_source(path)["ocean"]["openness"]["invalid"] == 1
    assert ngc.resolve_ngc(isolated).path is None


def test_final_asset_symlink_is_rejected(isolated):
    path, _, _ = write_install(isolated)
    original = path.with_name("original.parquet")
    path.rename(original)
    path.symlink_to(original.name)
    assert ngc.resolve_ngc(isolated).path is None


@pytest.fixture
def installer(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/install_ngc_personas.py"
    spec = importlib.util.spec_from_file_location("ngc_installer_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "load_environment", lambda: None)
    monkeypatch.setenv("NGC_CLI_API_KEY", "fixture-personal-key")
    return module


def test_installer_uses_authenticated_org_route_and_does_not_forward_key_to_storage(
    isolated, installer, monkeypatch,
):
    fixture_path = isolated / "fixture.parquet"
    pq.write_table(pa.Table.from_pylist([profile()]), fixture_path)
    content = fixture_path.read_bytes()
    requests = []

    def respond(request):
        requests.append(request)
        if str(request.url) == ngc.FILES_URL:
            return httpx.Response(200, json={"recipeFiles": [{"path": ngc.FILENAME,
                                                             "sizeInBytes": len(content)}]})
        if request.url.host == "api.ngc.nvidia.com":
            return httpx.Response(302, headers={"location": "https://fixture.amazonaws.com/asset?signature=fake"})
        return httpx.Response(200, content=content, headers={"content-type": "application/octet-stream"})

    client = httpx.Client(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(installer.httpx, "Client", lambda **kwargs: client)
    result = installer.install(isolated)
    assert result["audit"]["ready"]
    assert ngc.verify_pinned_install(isolated)["sha256"] == result["sha256"]
    assert all(request.method == "GET" for request in requests)
    assert str(requests[0].url) == ngc.FILES_URL
    assert requests[0].headers["authorization"] == "Bearer fixture-personal-key"
    assert "authorization" not in requests[-1].headers
    assert not list(ngc.install_folder(isolated).glob("*.part"))
    with pytest.raises(ValueError, match="refusing to overwrite"):
        installer.install(isolated)


def test_installer_access_denial_stops_without_accepting_terms(isolated, installer, monkeypatch):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(403, json={"private": "must never be printed"})

    client = httpx.Client(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(installer.httpx, "Client", lambda **kwargs: client)
    with pytest.raises(ValueError, match="HTTP 403"):
        installer.install(isolated)
    assert len(requests) == 1 and requests[0].method == "GET"
    assert not (ngc.install_folder(isolated) / ngc.FILENAME).exists()


@pytest.mark.parametrize("url", ["http://storage.nvidia.com/asset", "https://nvidia.com.evil.test/asset",
                                 "https://unrelated.test/asset", "https://user:pass@storage.nvidia.com/asset"])
def test_installer_rejects_unsupported_redirects(installer, url):
    with pytest.raises(ValueError, match="unsupported download redirect"):
        installer._redirect(ngc.FILES_URL, url)
