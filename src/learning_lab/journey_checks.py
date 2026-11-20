"""Inspectable application assertions over saved facts; no judge or Helix call."""
from __future__ import annotations

import re
from pathlib import Path

from .catalogue import Preferences, all_courses, search_courses
from .outcomes import answer_outcome


def evaluate_boardgames(conversation: list, catalogue: Path, tools: list, source_lock: dict) -> dict:
    """Check the two-turn negative case against actual saved public/native output."""
    users = [m for m in conversation if m['role'] == 'user']
    replies = [m for m in conversation if m['role'] == 'assistant']
    rows = []

    def check(key, title, expected, actual, reason, evidence):
        rows.append({'id': key, 'criterion': title, 'expected': expected, 'actual': actual,
                     'status': 'pass' if expected == actual else 'fail', 'reason': reason,
                     'evidence': evidence, 'implementation': 'application assertion; no model judge'})

    check('two-turns', 'Two public learner/advisor pairs were completed', [2, 2], [len(users), len(replies)],
          'An early stop or missing reply remains incomplete, rather than being padded with a transcript.', ['public-conversation.json'])
    check('valid-answers', 'Both replies are valid public answers', True,
          len(replies) == 2 and all(answer_outcome(r.get('content'))['status'] == 'valid' for r in replies),
          'Checks empty/error/pseudo-tool output independently of transport success.', ['public-conversation.json'])
    check('source-lock', 'Original identity and revision are preserved', True,
          bool(source_lock.get('original_sha256') and source_lock.get('source_revision')),
          'Saved provenance does not establish population coverage.', ['source-lock.json'])
    public_followup = users[1]['content'] if len(users) > 1 else ''
    check('followup', 'The follow-up asks about game design', True,
          bool(re.search(r'(?:video[ -]?game|game)[ -]?(?:s?\s+)?design|design(?:ing)?\s+(?:video[ -]?)?games?', public_followup, re.I)),
          'The actual UserSim follow-up must exercise the intended distinction.', ['public-conversation.json'])
    check('catalogue-no-match', 'The frozen catalogue has no board-game playing class', [],
          search_courses(Preferences(goal='board games'),
                         catalogue_path=catalogue)['matches'],
          'This is a dated catalogue result, not a claim about every provider.', ['catalogue-snapshot.json'])
    for i, reply in enumerate(replies):
        text = reply['content']
        if i == 0:
            check('honest-no-match', 'The first reply acknowledges a catalogue limit', True,
                  bool(re.search(r'no (?:matching |suitable |specific |listed |dedicated |available )*(?:board[ -]?game|class|course|match)|(?:couldn.t|cannot|can.t|didn.t|don.t|not able to) (?:find|see)|(?:not|none|nothing).{0,60}(?:catalogue|catalog|listed|match)|(?:catalogue|catalog|snapshot).{0,70}(?:doesn.t|not|no |none)', text, re.I | re.S)),
                  'A narrow phrase check; review the linked reply for nuance.', ['public-conversation.json'])
        else:
            check('distinguish-design', 'Playing and designing games are distinguished', True,
                  bool(re.search(r'not the same|different|distinct|isn.t the same|rather than|not equivalent', text, re.I)),
                  'Checks an explicit distinction, not its complete pedagogical quality.', ['public-conversation.json'])
        check(f'no-invented-id-{i}', 'Any cited course IDs exist in the snapshot', True,
              set(re.findall(r'\b(?:CC|SF)-\d{3}\b', text)) <= {c.id for c in all_courses(catalogue)},
              'Does not certify unsupported claims without a course identifier.', ['public-conversation.json', 'catalogue-snapshot.json'])
    check('one-thread', 'Both replies use the same persistent native thread', True,
          len(replies) == 2 and len({r.get('thread_id') for r in replies}) == 1 and bool(replies[0].get('thread_id')),
          'Same-thread identity plus the follow-up checks persistence; it is not proof of cross-session memory.', ['public-conversation.json'])
    check('native-tools', 'A completed native catalogue search is attributable', True,
          any('search_courses' in t.get('name', '') and t.get('evidence_origin') == 'native_relay'
              and t.get('status') == 'completed' and t.get('output', t.get('result')) is not None for t in tools),
          'Application intent logs cannot replace native tool execution.', ['native-tools.json'])
    return {'kind': 'application assertions', 'rows': rows,
            'passed': sum(r['status'] == 'pass' for r in rows), 'total': len(rows),
            'coverage': 'Two public pairs, explicit no-match/design distinction, valid answers, known IDs, same native thread and actual tool evidence. Semantic recommendation quality still requires review.',
            'inference_calls': 0, 'helix_used': False}


def evaluate_photography(conversation: list, catalogue: Path, tools: list, source_lock: dict) -> dict:
    rows = []

    def check(key, title, expected, actual, reason, evidence):
        rows.append({'id': key, 'criterion': title, 'expected': expected, 'actual': actual,
                     'status': 'pass' if expected == actual else 'fail', 'reason': reason,
                     'evidence': evidence, 'implementation': 'application assertion; no model judge'})

    replies = [m for m in conversation if m['role'] == 'assistant']
    check('public-answer', 'A valid public answer was saved', True,
          bool(replies) and all(answer_outcome(m.get('content'))['status'] == 'valid' for m in replies),
          'A transport result, empty answer or error string does not count as advice.', ['public-conversation.json'])
    check('source-lock', 'The test persona has an unchanged original hash', True,
          bool(source_lock.get('original_sha256')) and bool(source_lock.get('source_revision')),
          'This checks the saved lock receipt, not representativeness or citizenship.', ['source-lock.json'])
    courses = {c.id: c for c in all_courses(catalogue)}
    from .journey import public_photography_preferences
    users = [m for m in conversation if m['role'] == 'user']
    requested = {'budget_sgd': 50.0, 'days': [5]}
    stated = public_photography_preferences(users[0]['content']) if users else None
    check('public-situation', 'The public opening actually states the selected situation', requested,
          {'budget_sgd': stated.budget_sgd, 'days': stated.days} if stated else None,
          'Generated UserSim wording may vary; omitted constraints do not count as a successful Saturday/S$50 demonstration.',
          ['public-conversation.json', 'situation.json'])
    for index, reply in enumerate(replies):
        text = str(reply.get('content') or '').replace('\u2011', '-').replace('\u2013', '-')
        cited = set(re.findall(r'\b(?:CC|SF)-\d{3}\b', text))
        urls = set(re.findall(r'https://[^\s)\]>]+', text))
        known_urls = {str(c.source_url): c.id for c in courses.values()}
        # Public recommendations need a source link, not our application's
        # internal identifier. An exact frozen URL identifies the same listing.
        linked = {known_urls[url] for url in urls if url in known_urls}
        identified = cited | linked
        check(f'grounding-{index}', 'Recommendation links and IDs belong to the frozen catalogue', True,
              bool(urls) and urls <= known_urls.keys() and cited <= courses.keys(),
              'An exact catalogue URL identifies a listing; internal course IDs are optional. Other factual sentences still need review.',
              ['public-conversation.json', 'catalogue-snapshot.json'])
        areas = {c.planning_area.casefold() for key, c in courses.items() if key in identified and c.planning_area}
        claims = []
        for match in re.finditer(r'\b(?:within|inside|located in|in)\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+){0,4})\s+planning area\b', text, re.I):
            if not re.search(r'\b(?:not|outside)\s*$', text[max(0, match.start()-12):match.start()], re.I):
                claims.append(' '.join(match[1].casefold().split()))
        claims.extend(' '.join(area.casefold().split()) for area in re.findall(
            r'\bplanning area(?:\*\*)?\s*:\s*(?:\*\*)?\s*([a-z]+(?:[ \t]+[a-z]+){0,4})', text, re.I))
        check(f'location-{index}', 'Explicit venue planning-area claims match the cited facts', True,
              set(claims) <= areas,
              f'Checks explicit planning-area attribution phrases: {claims}; cited source areas: {sorted(areas)}. This does not establish proximity or cover every geographic expression.',
              ['public-conversation.json', 'catalogue-snapshot.json'])
        fees = {float(v) for v in re.findall(r'(?:\*\*)?(?:published |course )?fee(?:\*\*)?\s*:?\s*(?:\*\*)?\s*S\$\s*(\d+(?:\.\d+)?)', text, re.I)}
        published = {v for key, c in courses.items() if key in identified for v in (c.price_min_sgd, c.price_max_sgd) if v is not None}
        check(f'fee-{index}', 'Explicit fee fields match published catalogue amounts', True, fees <= published,
              f'Checks labelled fee amounts {sorted(fees)} against published amounts {sorted(published)}; does not infer an all-in total.',
              ['public-conversation.json', 'catalogue-snapshot.json'])
        if index < len(users):
            preferences = public_photography_preferences(users[index]['content'])
            allowed = {r['course']['id'] for r in search_courses(preferences, catalogue_path=catalogue)['matches']}
            check(f'constraints-{index}', 'Recommended listings respect the publicly stated budget and day', True,
                  bool(identified) and identified <= allowed,
                  'Constraints are extracted only from the saved public learner turn, never the private persona.',
                  ['public-conversation.json', 'catalogue-snapshot.json'])
        lower = text.lower()
        check(f'assurances-{index}', 'No unsupported fee or funding assurance pattern', False,
              bool(re.search(r'no (?:additional|extra|material) (?:fees|costs)|you (?:are eligible|qualify|will receive)|guaranteed (?:funding|subsidy)', lower)),
              'A narrow phrase check; a pass does not certify every financial statement.', ['public-conversation.json'])
    check('native-tools', 'Native tool evidence includes a completed catalogue request', True,
          any('search_courses' in str(t.get('name', t.get('tool_name', '')))
              and t.get('evidence_origin') == 'native_relay' and t.get('status') == 'completed'
              and t.get('output', t.get('result')) is not None for t in tools),
          'Native Relay evidence is required; an application log saying “searched” is insufficient.', ['native/fabric-traces/relay.jsonl'])
    return {'kind': 'application assertions', 'rows': rows,
            'passed': sum(r['status'] == 'pass' for r in rows), 'total': len(rows),
            'coverage': 'Exact course URLs/IDs, explicit planning-area and fee phrases, source lock, stated constraints, selected assurance patterns and native tool evidence. Other factual phrasing, proximity, seats and personal eligibility require review.',
            'inference_calls': 0, 'helix_used': False}
