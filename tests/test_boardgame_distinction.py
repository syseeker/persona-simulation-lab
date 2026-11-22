"""Synthetic regressions for one explicit playing-versus-designing paraphrase."""
import json

import pytest

from learning_lab.journey_checks import evaluate_boardgames


@pytest.mark.parametrize('reply,expected', [
    ('Board-game classes teach playing and strategy; video-game design teaches coding, a separate skill set.', True),
    ('Board‑game classes teach playing and strategy; video‑game design teaches coding — a separate skill set.', True),
    ('Playing board games is different from video-game design.', True),
    ('Board-game classes teach playing; video-game design is not a separate skill set.', False),
    ('Board-game classes teach playing; video-game design is not necessarily a separate skill set.', False),
    ('Board-game classes teach playing; cooking uses a separate skill set.', False),
    ('Video-game design teaches a separate skill set.', False),
    ('Board-game classes teach playing. Video-game design is discussed. Cooking uses a separate skill set.', False),
    ('Playing board games and video-game design are the same activity.', False),
])
def test_selected_explicit_distinction_is_not_an_unrelated_or_negated_phrase(tmp_path, reply, expected):
    catalogue = tmp_path / 'catalogue.json'
    catalogue.write_text(json.dumps({'courses': [{'id': 'CC-001', 'title': 'Synthetic cooking class',
        'provider': 'Offline fixture', 'kind': 'community', 'summary': 'Learn basic cooking.', 'tags': ['cooking'],
        'source_url': 'https://example.test/cooking', 'captured_on': '2026-11-22'}]}))
    result = evaluate_boardgames([
        {'role': 'user', 'content': 'I want to play board games.'},
        {'role': 'assistant', 'content': 'The catalogue has no matching class.', 'thread_id': 'offline'},
        {'role': 'user', 'content': 'Is video-game design the same?'},
        {'role': 'assistant', 'content': reply, 'thread_id': 'offline'},
    ], catalogue, [{'name': 'search_courses', 'evidence_origin': 'native_relay', 'status': 'completed',
                    'result': {'matches': []}}], {'original_sha256': 'offline', 'source_revision': 'offline'})
    row = next(row for row in result['rows'] if row['id'] == 'distinguish-design')
    assert row['actual'] is expected
    assert (row['status'] == 'pass') is expected
    assert result['total'] == 11 and result['inference_calls'] == 0
    assert 'not complete semantic' in row['reason']
