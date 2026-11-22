import json

import httpx
import pytest

from learning_lab.captures import REQUIREMENTS, RULES, build_capture_manifest, verify_capture_manifest
from learning_lab.inference import Budget, Gateway
from learning_lab.proxy_capture import resolve_settings


def state():
    return {'scenario_id': 'photography', 'run_id': 'run-one', 'condition_id': 'baseline-one',
            'episode_id': 'episode-one', 'status': 'failed', 'source_revision': 'fixture'}


@pytest.fixture
def designer_capture(tmp_path, monkeypatch):
    from learning_lab import captures

    monkeypatch.setattr(captures, 'REQUIREMENTS', {'CAP-DD-05': REQUIREMENTS['CAP-DD-05']})
    selected = {**state(), 'scenario_id': 'dreamjob', 'status': 'completed'}
    (tmp_path / 'run.json').write_text(json.dumps(selected))
    private = tmp_path / 'designer-private'
    private.mkdir()
    receipt = private / 'designer-profiling.json'
    receipt.write_text(json.dumps({'status': 'completed', 'error': None, 'error_type': None,
                                   'analysis_report': 'designer-analysis.json'}))
    report = private / 'designer-analysis.json'
    report.write_text(json.dumps({'num_records': 1, 'target_num_records': 1,
        'column_statistics': [{'column_name': 'retail_situation', 'output_tokens_stddev': None}]}))
    return tmp_path, selected, receipt, report


def test_completed_designer_profiling_requires_the_actual_native_report(designer_capture):
    folder, selected, _, report = designer_capture
    manifest = build_capture_manifest(folder, selected)
    assert manifest['contract_version'] == 2 and manifest['coverage']['complete']
    assert {item['location'] for item in manifest['rows'][0]['artifacts']} == {
        'designer-private/designer-profiling.json', 'designer-private/designer-analysis.json'}
    verify_capture_manifest(folder, manifest)
    report.unlink()
    missing = build_capture_manifest(folder, selected)
    assert not missing['coverage']['complete'] and missing['rows'][0]['availability'] == 'missing'
    assert missing['rows'][0]['missing'] == [['designer-private/designer-analysis.json']]
    assert len(missing['rows'][0]['artifacts']) == 1  # Retain the real receipt.
    with pytest.raises(ValueError, match='no longer matches'):
        verify_capture_manifest(folder, manifest)


@pytest.mark.parametrize('change', ['failed-receipt', 'other-report', 'reported-error',
                                  'malformed-json', 'incomplete-rows', 'empty-statistics', 'nonfinite-json'])
def test_designer_report_presence_cannot_claim_successful_complete_profiling(designer_capture, change):
    folder, selected, receipt, report = designer_capture
    if change in {'failed-receipt', 'other-report', 'reported-error'}:
        value = json.loads(receipt.read_text())
        if change == 'failed-receipt':
            value.update(status='failed', analysis_report=None, error_type='DataDesignerProfilingError')
        elif change == 'other-report':
            value['analysis_report'] = '../another-run/designer-analysis.json'
        else:
            value['error'] = 'Native profiling failed'
        receipt.write_text(json.dumps(value))
    elif change == 'malformed-json':
        report.write_text('{broken')
    elif change == 'nonfinite-json':
        report.write_text('{"num_records":1,"target_num_records":1,"column_statistics":'
                          '[{"column_name":"retail_situation","output_tokens_stddev":NaN}]}')
    else:
        value = json.loads(report.read_text())
        value.update({'target_num_records': 2} if change == 'incomplete-rows' else {'column_statistics': []})
        report.write_text(json.dumps(value))
    manifest = build_capture_manifest(folder, selected)
    assert manifest['rows'][0]['availability'] == 'exists'
    assert manifest['rows'][0]['integrity_errors'] and not manifest['coverage']['complete']
    assert manifest['coverage']['missing'] == ['CAP-DD-05:baseline-one']
    with pytest.raises(ValueError, match='coverage is incomplete'):
        verify_capture_manifest(folder, manifest)


def test_legacy_designer_failed_receipt_verifies_without_rewriting_history(designer_capture):
    folder, selected, receipt, report = designer_capture
    report.unlink()
    receipt.write_text(json.dumps({'status': 'failed', 'analysis_report': None,
                                   'error_type': 'DataDesignerProfilingError', 'error': 'NAType'}))
    selected['status'] = 'failed'
    (folder / 'run.json').write_text(json.dumps(selected))
    historical = build_capture_manifest(folder, selected, contract_version=1)
    historical.pop('contract_version')  # Exact unversioned historical contract.
    original = json.dumps(historical, sort_keys=True)
    assert historical['coverage']['complete']
    verify_capture_manifest(folder, historical)
    assert json.dumps(historical, sort_keys=True) == original
    current = build_capture_manifest(folder, selected)
    assert not current['coverage']['complete'] and len(current['rows'][0]['artifacts']) == 1


@pytest.mark.parametrize('version', [0, 3, '2', True, None])
def test_unsupported_capture_contract_cannot_skip_current_report_requirements(designer_capture, version):
    folder, selected, _, _ = designer_capture
    manifest = build_capture_manifest(folder, selected)
    manifest['contract_version'] = version
    with pytest.raises(ValueError, match='Unsupported capture contract'):
        verify_capture_manifest(folder, manifest)


def test_contract_covers_every_stable_requirement_and_never_borrows_another_run(tmp_path):
    assert len(REQUIREMENTS) == 51 and REQUIREMENTS.keys() == RULES.keys()
    unrelated = tmp_path / 'other-run'
    unrelated.mkdir()
    (unrelated / 'fabric-run-results.jsonl').write_text('{}\n')
    root = tmp_path / 'selected'
    root.mkdir()
    manifest = build_capture_manifest(root, state())
    result = next(row for row in manifest['rows'] if row['id'] == 'CAP-FAB-06')
    assert result['availability'] == 'missing' and result['artifacts'] == []
    assert result['execution_status'] == 'failed'
    assert next(row for row in manifest['rows'] if row['id'] == 'CAP-DD-03')['availability'] == 'not-used'
    assert manifest['coverage']['complete'] is False


def test_real_capture_can_exist_with_failed_execution_and_changed_bytes_are_rejected(tmp_path):
    native = tmp_path / 'episode-one/native'
    native.mkdir(parents=True)
    result = native / 'fabric-run-results.jsonl'
    result.write_text('{"error_type":"TimeoutError"}\n')
    (tmp_path / 'run.json').write_text(json.dumps(state()))
    manifest = build_capture_manifest(tmp_path, state())
    row = next(row for row in manifest['rows'] if row['id'] == 'CAP-FAB-06')
    assert row['availability'] == 'exists' and row['execution_status'] == 'failed'
    assert row['access'] == 'private'
    result.write_text('{"status":"succeeded"}\n')
    with pytest.raises(ValueError, match='no longer matches'):
        verify_capture_manifest(tmp_path, manifest)


def test_symbolic_native_artifacts_do_not_satisfy_capture(tmp_path):
    native = tmp_path / 'episode-one/native'
    native.mkdir(parents=True)
    outside = tmp_path / 'not-native.json'
    outside.write_text('{}')
    (native / 'fabric-config.json').symlink_to(outside)
    manifest = build_capture_manifest(tmp_path, state())
    assert next(row for row in manifest['rows'] if row['id'] == 'CAP-FAB-01')['availability'] == 'missing'


def test_one_result_cannot_satisfy_two_recorded_turns(tmp_path):
    native = tmp_path / 'episode-one/native'
    native.mkdir(parents=True)
    turns = [{'request_id': str(n), 'thread_id': 'one-thread', 'turn': n} for n in [1, 2]]
    for name, values in [('fabric-run-requests.jsonl', turns), ('preferences-by-turn.jsonl', turns),
                         ('fabric-run-results.jsonl', turns[:1])]:
        (native / name).write_text(''.join(json.dumps(row) + '\n' for row in values))
    manifest = build_capture_manifest(tmp_path, state())
    result = next(row for row in manifest['rows'] if row['id'] == 'CAP-FAB-06')
    assert result['availability'] == 'exists' and result['integrity_errors']
    assert 'CAP-FAB-06:baseline-one' in manifest['coverage']['missing']


def test_retail_conditions_do_not_conflate_overall_and_baseline_status(tmp_path):
    selected = {**state(), 'scenario_id': 'dreamjob', 'baseline_status': 'completed',
                'comparison_conditions': ['fixed-comparison', 'routed-comparison'],
                'managed_condition_id': 'managed-one'}
    for identity, label in [('fixed-comparison', 'fixed-candidate'), ('routed-comparison', 'switchyard')]:
        work = tmp_path / 'comparisons' / identity
        work.mkdir(parents=True)
        (work / 'condition.json').write_text(json.dumps({'condition_id': identity, 'label': label, 'status': 'failed'}))
        (work / 'litellm-loaded.yaml').write_text('model_list: []\n')
        native = work / 'runtime/native'
        native.mkdir(parents=True)
        (native / 'guardrails-decisions.jsonl').write_text('{}\n')
    manifest = build_capture_manifest(tmp_path, selected)
    assert next(row for row in manifest['rows'] if row['id'] == 'CAP-FAB-01')['execution_status'] == 'completed'
    candidates = [row for row in manifest['rows'] if row['id'] == 'CAP-LLM-02' and row['required']]
    assert len(candidates) == 2 and all(row['availability'] == 'exists' for row in candidates)
    rails = [row for row in manifest['rows'] if row['id'] == 'CAP-GR-02' and row['purpose'] in {'fixed-candidate', 'switchyard'}]
    assert len(rails) == 2 and all(row['availability'] == 'exists' for row in rails)
    managed = next(row for row in manifest['rows'] if row['id'] == 'CAP-PLAT-01')
    assert managed['condition_id'] == 'managed-one' and managed['purpose'] == 'managed'


async def test_schema_capture_is_after_filtering_and_terminal_error_is_kept(tmp_path, monkeypatch):
    monkeypatch.setattr('learning_lab.inference.load_environment', lambda: None)
    monkeypatch.setenv('LAB_PROXY_BASE_URL', 'http://proxy.test/v1')
    secret = 'private-fixture-key-do-not-retain'
    monkeypatch.setenv('LAB_PROXY_API_KEY', secret)
    gateway = Gateway(Budget(1), allowed_tool_names=['search_courses'], evidence_dir=tmp_path)
    await gateway._client.aclose()
    gateway._client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request:
        httpx.Response(504, json={'error': {'message': 'upstream timed out'}})))
    try:
        with pytest.raises(RuntimeError, match='504'):
            await gateway.complete({'model': 'fixture', 'messages': [], 'tools': [
                {'type': 'function', 'function': {'name': name, 'parameters': {'type': 'object'}}}
                for name in ['read_file', 'search_courses']]})
        schemas = json.loads((tmp_path / 'provider-tool-schemas.jsonl').read_text())
        assert [t['function']['name'] for t in schemas['tools']] == ['search_courses']
        record = json.loads((tmp_path / 'gateway-calls.jsonl').read_text())
        assert record['status'] == 'failed' and record['http_status'] == 504
        assert record.get('usage') is None and record['call'] == 1
        assert secret not in ''.join(p.read_text() for p in tmp_path.iterdir())
    finally:
        await gateway._client.aclose()


def test_proxy_resolution_preserves_settings_but_never_resolves_secret_values():
    native = {'model': 'os.environ/LAB_FIXED_MODEL', 'api_key': 'os.environ/LAB_FIXED_API_KEY'}
    result = resolve_settings(native, {'LAB_FIXED_MODEL': 'openai/example', 'LAB_FIXED_API_KEY': 'private-test'})
    assert result['model'] == 'openai/example'
    assert result['api_key']['present'] is True
    assert 'private-test' not in json.dumps(result)


async def test_predispatch_failure_still_has_one_terminal_capture(tmp_path):
    gateway = Gateway(Budget(1), 'demo', evidence_dir=tmp_path)
    try:
        with pytest.raises(ValueError, match='positive integers'):
            await gateway.complete({'model': 'fixture', 'messages': [], 'max_tokens': -1})
        record = json.loads((tmp_path / 'gateway-calls.jsonl').read_text())
        assert record['status'] == 'failed' and record['call'] == 1
        assert record['error_type'] == 'ValueError' and 'usage' not in record
        assert not (tmp_path / 'provider-tool-schemas.jsonl').exists()
    finally:
        await gateway._client.aclose()
