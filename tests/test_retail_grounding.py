"""Narrow saved-answer regressions; no provider calls or private answer fixtures."""
import json

import pytest

from learning_lab.catalogue import all_courses
from learning_lab.retail import freeze_retail_catalogue
from learning_lab.retail_checks import evaluate_retail


@pytest.fixture
def evaluate(tmp_path):
    catalogue = tmp_path / 'catalogue.json'
    freeze_retail_catalogue(catalogue)
    official_url = str(next(c for c in all_courses(catalogue) if c.id == 'SF-007').source_url)
    (tmp_path / 'public-constraints.jsonl').write_text('\n'.join(json.dumps({
        'turn': turn, 'salary_publicly_disclosed': turn > 1,
        'preferences': {'budget_sgd': 3000 if turn == 3 else None,
                        'days': [5, 6] if turn == 3 else None},
    }) for turn in range(1, 4)))

    def run(text, turn=2):
        answers = [f'The full fee is S$20,928 for 3 months. {official_url}',
                   'Salary does not establish affordability. What is your total training budget and study schedule?',
                   'The fee and weekend timetable are unknown; confirm both with the provider.']
        answers[turn - 1] = text
        conversation = [item for i, answer in enumerate(answers, 1) for item in [
            {'role': 'user', 'content': 'Salary S$2,500–3,499.' if i == 2 else 'Retail learning.'},
            {'role': 'assistant', 'content': answer, 'thread_id': 'fixture-thread'},
        ]]
        result = evaluate_retail(conversation, catalogue, [], {}, tmp_path)
        return {row['id']: row for row in result['rows']}

    return run


@pytest.mark.parametrize('text', [
    'Unless you qualify for funding, the fee remains unchanged.',
    'If you qualify, contact the provider to confirm the personal amount.',
    'Confirm whether you are eligible with the provider.',
])
def test_conditional_eligibility_is_not_a_direct_assurance(evaluate, text):
    assert evaluate(text)['assurances-2']['status'] == 'pass'


@pytest.mark.parametrize('text', [
    'You qualify for funding.',
    'If fees change, you qualify for funding.',
    'Unless you qualify for funding, you are eligible for a different scheme.',
    'If you ask, this course guarantees a job.',
])
def test_conditional_elsewhere_cannot_hide_an_asserted_assurance(evaluate, text):
    assert evaluate(text)['assurances-2']['status'] == 'fail'


def test_unsupported_official_looking_link_still_fails(evaluate):
    result = evaluate('Ask the provider at https://www.skillsfuture.sg/credit.')['sources-2']
    assert result['status'] == 'fail'
    assert result['observed']['unsupported_urls'] == ['https://www.skillsfuture.sg/credit']


@pytest.mark.parametrize('turn', [1, 2, 3])
@pytest.mark.parametrize('count, status', [(179, 'pass'), (180, 'pass'), (181, 'fail')])
def test_every_reply_must_be_at_most_180_words(evaluate, turn, count, status):
    result = evaluate(' '.join(['word'] * count), turn)[f'concise-reply-{turn}']
    assert result['status'] == status
    assert result['observed']['word_count'] == count


@pytest.mark.parametrize('text', [
    'Given your salary, the course is likely out of reach unless you qualify for funding.',
    'You cannot afford this course on your income.',
    'These alternatives may be more affordable.',
    'I cannot confirm the fee; these alternatives are more affordable.',
    'Unless you qualify for funding, you cannot afford this course.',
    'Ask about payment plans or instalment arrangements.',
    'If you qualify, ask about payment plans or instalment arrangements.',
    'Check your SkillsFuture Credit balance; the remaining credit can be applied toward the fee.',
])
def test_salary_only_turn_does_not_invent_affordability_or_financing(evaluate, text):
    result = evaluate(text)['salary-only-advice']
    assert result['status'] == 'fail'
    assert result['actual'] and result['coverage']


@pytest.mark.parametrize('text', [
    'Salary does not establish affordability. What is your total training budget and study schedule?',
    'Payment plans are not listed. Confirm the full fee and funding eligibility with the provider.',
    'I cannot say you can afford this. What is your training budget and study schedule?',
    'These alternatives are not necessarily more affordable.',
    'I cannot confirm that these alternatives are more affordable.',
    'It is unknown whether these courses are more affordable.',
    'This course is not necessarily out of reach.',
])
def test_salary_only_turn_can_explain_unknowns_and_ask_for_constraints(evaluate, text):
    assert evaluate(text)['salary-only-advice']['status'] == 'pass'


def test_missing_salary_only_context_is_not_a_content_check_pass(evaluate, tmp_path):
    (tmp_path / 'public-constraints.jsonl').unlink()
    result = evaluate('What is your budget and study schedule?')['salary-only-advice']
    assert result['status'] == 'fail'
    assert result['observed']['context_verified'] is False
