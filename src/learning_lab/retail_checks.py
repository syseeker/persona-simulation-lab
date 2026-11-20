"""Explicit criteria over saved retail replies/facts; Helix scores these rows."""
from __future__ import annotations

import json
from pathlib import Path
import re

from .catalogue import all_courses
from .outcomes import answer_outcome
from .retail_policy import unsupported_funding_claims
from .journey_checks import valid_native_search


def evaluate_retail(conversation: list, catalogue: Path, tools: list, source_lock: dict, folder: Path) -> dict:
    rows = []

    def check(key, title, expected, actual, reason, evidence):
        rows.append({'id': key, 'criterion': title, 'expected': expected, 'actual': actual,
            'status': 'pass' if expected == actual else 'fail', 'reason': reason, 'evidence': evidence,
            'implementation': 'application-defined criterion; scored by native Helix ExactMatchMetric'})

    def lines(name):
        path = folder / name
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []

    users = [m for m in conversation if m['role'] == 'user']
    replies = [m for m in conversation if m['role'] == 'assistant']
    constraints, audit = lines('public-constraints.jsonl'), lines('disclosure-audit.jsonl')
    check('three-turns', 'Three public learner/advisor pairs completed', [3, 3], [len(users), len(replies)],
          'Native early stops and incomplete replies are preserved rather than filled in.', ['public-conversation.json'])
    check('valid-answers', 'All three replies contain valid public answers', True,
          len(replies) == 3 and all(answer_outcome(r.get('content'))['status'] == 'valid' for r in replies),
          'Transport success alone cannot satisfy this criterion.', ['public-conversation.json'])
    check('original-lock', 'Source identity/revision/hash are retained', True,
          bool(source_lock.get('original_sha256') and source_lock.get('source_revision')),
          'This checks provenance, not demographic coverage or personal entitlement.', ['source-lock.json'])
    salary_turns = [index + 1 for index, row in enumerate(users) if '2500' in row['content'].replace(',', '')
                    and '3499' in row['content'].replace(',', '')]
    check('salary-disclosure', 'The salary band first appears in public turn 2', 2,
          salary_turns[0] if salary_turns else None,
          'The fixed hypothetical band is simulator context until the learner actually discloses it.', ['public-conversation.json'])
    check('salary-request-boundary', 'Actual advisor requests respect public disclosure', True,
          bool(audit) and all(row['boundary_passed'] for row in audit)
          and any(row['public_turn'] == 1 and not row['salary_band_in_request'] for row in audit),
          'Actual request bodies are checked before dispatch for the selected hidden salary values; this is not a universal privacy classifier.', ['disclosure-audit.jsonl'])
    check('salary-not-budget', 'No training budget is inferred from salary in turn 2', None,
          constraints[1]['preferences']['budget_sgd'] if len(constraints) > 1 else 'missing evidence',
          'Only an explicit public spending limit can set the tool budget.', ['public-constraints.jsonl'])
    check('explicit-final-constraints', 'Turn 3 binds the explicit spending and weekend limit',
          {'budget_sgd': 3000.0, 'days': [5, 6]},
          {key: constraints[2]['preferences'][key] for key in ['budget_sgd', 'days']} if len(constraints) > 2 else None,
          'Income, provider full fees and explicit training budget are different values.', ['public-constraints.jsonl'])
    facts = {c.id: c for c in all_courses(catalogue)}
    smu = facts['SF-007']
    # Provider answers may contain NBSP/narrow spaces. Matching typography is
    # not a test of factual accuracy; preserve the original answer separately.
    first = re.sub(r'\s+', ' ', replies[0]['content']) if replies else ''
    check('published-full-fee', 'The opening reports the sourced full programme fee', True,
          bool(re.search(r'(?:S\$|SGD|\$)\s*20,?928(?:\.00)?', first, re.I)),
          f'Frozen provider fact: S${smu.price_max_sgd:,.0f}. Conditional funding is separate.', ['public-conversation.json', 'catalogue-snapshot.json'])
    check('published-duration', 'The opening preserves the actual three-month duration', True,
          bool(re.search(r'\b(?:3|three)[ -]months?\b|\b12[ -]weeks?\b', first, re.I)),
          f'Frozen fact: {smu.duration_months} months / {smu.duration_hours:g} hours. A hypothetical six months cannot replace it.', ['public-conversation.json', 'catalogue-snapshot.json'])
    check('persistent-thread', 'The three turns use one persistent native thread', True,
          len(replies) == 3 and len({r.get('thread_id') for r in replies}) == 1 and bool(replies[0].get('thread_id')),
          'This checks the local three-turn condition; managed execution starts a new session.', ['public-conversation.json'])
    for index, reply in enumerate(replies):
        text = reply['content']
        urls = {url.rstrip('.,;') for url in re.findall(r'https://[^\s)\]>]+', text)}
        ids = set(re.findall(r'\b(?:CC|SF)-\d{3}\b', text))
        check(f'sources-{index+1}', f'Turn {index+1} cited links/IDs belong to the snapshot', True,
              urls <= {str(c.source_url) for c in facts.values()} and ids <= facts.keys(),
              'Checks exact links and identifiers; uncited natural-language claims still require review.', ['public-conversation.json', 'catalogue-snapshot.json'])
        plain = re.sub(r'[*_]', '', text)
        assurance = any(not re.search(r'(?:if|whether)\s*$', plain[max(0, match.start()-16):match.start()], re.I)
            for match in re.finditer(r'you (?:will definitely get|are guaranteed) (?:a job|hired)|you (?:qualify|are eligible|can afford this)|this course guarantees (?:a job|employment)|(?:UNIQLO|Decathlon) (?:endorses|guarantees)', plain, re.I))
        check(f'assurances-{index+1}', f'Turn {index+1} makes no selected outcome/eligibility assurance', False,
              assurance,
              'Narrow phrase coverage; no blanket certification of financial, employment or endorsement statements.', ['public-conversation.json'])
    funding = [finding for reply in replies for finding in unsupported_funding_claims(reply['content'])]
    check('unpublished-funding-figures', 'No unlisted numerical funding rates or annual credit amount', [],
          sorted(set(funding)), 'This frozen catalogue publishes no subsidy percentages or annual credit cap. Narrow numerical-claim coverage; other claims need review.',
          ['public-conversation.json', 'catalogue-snapshot.json'])
    usage_path = folder / 'usage.json'
    advisor = [row for row in json.loads(usage_path.read_text()).get('records', []) if row.get('role') == 'assistant'] if usage_path.is_file() else []
    completed = [row for row in advisor if row.get('status') == 'completed']
    check('output-completion', 'Advisor model outputs did not exhaust their token ceiling', True,
          bool(completed) and all(row.get('finish_reason') not in {None, 'length'} for row in completed),
          'Native finish reasons distinguish a completed answer/tool call from token truncation. Missing completion evidence is not a pass.', ['usage.json'])
    final = replies[2]['content'] if len(replies) > 2 else ''
    check('unknowns-retained', 'The final reply retains an explicit confirmation/unknown boundary', True,
          bool(re.search(r'confirm|unconfirmed|unknown|not (?:verified|established)|check (?:with|the)', final, re.I)),
          'An unknown fee or timetable is not proof that an alternative fits the budget/weekends.', ['public-conversation.json'])
    check('native-course-search', 'A completed actual MCP search is attributable', True,
          any(valid_native_search(tool) for tool in tools),
          'The frozen catalogue and an application intent log alone are insufficient.', ['native-tools.json'])
    return {'kind': 'Helix Evals SDK · application-defined criteria', 'rows': rows,
        'passed': sum(row['status'] == 'pass' for row in rows), 'total': len(rows),
        'coverage': 'Saved public pairs, source provenance, actual salary-request audit, explicit constraints, full fee/duration, exact cited sources, selected assurance phrases, uncertainty and native tools. Other semantics and personal eligibility require review.',
        'inference_calls': 0, 'helix_used': False}
