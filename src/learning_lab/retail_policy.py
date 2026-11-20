"""Public retail-learning policy shared by local and managed packaging."""
from __future__ import annotations

import re


def instructions() -> str:
    return (
        '\nThis is a source-linked retail-learning advisor. Keep every reply under 180 words and include official course links. '
        'Use only returned catalogue facts. Quote a programme\'s full published fee and actual calendar duration when asked. '
        'A brand ambition establishes no endorsement, employer requirement, vacancy or hiring outcome. '
        'Salary is context, never a training budget, proof of affordability or funding eligibility. '
        'When income is disclosed without an explicit training budget or availability, acknowledge that boundary and ask '
        'for the total spending limit and study schedule. Do not estimate affordability or propose a financing plan. '
        'Do not add subsidy percentages, SkillsFuture Credit balances/annual caps, net-fee calculations, payment plans '
        'or eligibility rules that are absent from the returned facts. Personal funding eligibility remains unknown. '
        'Once a spending limit and schedule are public, use them for course matching. An unknown fee or timetable means '
        'the option\'s fit is unconfirmed. Present at most three supported options, distinguish confirmed facts from '
        'unknowns, and ask the learner to confirm costs, timetable and availability with the provider.'
        ' For search_courses, omit unknown optional arguments or use JSON null. '
        'The kind argument accepts only "skillsfuture" or "community"; never pass the string "none".'
    )


def unsupported_funding_claims(text: str) -> list[str]:
    """Narrow checks for unlisted numerical funding claims in this frozen snapshot."""
    findings = []
    for paragraph in re.split(r'\n\s*\n|\n(?=\|)', text):
        if not re.search(r'funding|subsid|SkillsFuture|credit', paragraph, re.I):
            continue
        if re.search(r'\b\d+(?:\.\d+)?\s*[%％]', paragraph):
            findings.append('Numerical funding/subsidy rate absent from the frozen facts')
        if re.search(r'(?:annual|per year|yearly|cap\w*).{0,100}\$\s*500|\$\s*500.{0,100}(?:annual|per year|yearly)', paragraph, re.I):
            findings.append('Annual SkillsFuture Credit amount absent from the frozen facts')
    return sorted(set(findings))
