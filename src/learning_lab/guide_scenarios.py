"""Versioned preset capabilities; adding a story does not fork run/evidence APIs."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ScenarioPreset:
    id: str
    implemented: bool
    public_turns: int
    harness: str
    preparation: str
    route: str
    evaluation: str
    behavioural_checks: str
    deployment: str


PRESETS = {
    'photography': ScenarioPreset('photography', True, 1, 'deepagents', 'authored', 'fixed',
                                 'application assertions', 'application restrictions', 'standalone OpenShell'),
    'boardgames': ScenarioPreset('boardgames', True, 2, 'hermes', 'authored', 'fixed',
                                'application assertions', 'native Guardrails', 'standalone OpenShell'),
    'dreamjob': ScenarioPreset('dreamjob', False, 3, 'deepagents', 'Data Designer overlay', 'switchyard',
                              'Helix Evals and jobs', 'native Guardrails', 'Helix-managed OpenShell'),
}


def scenario_presets():
    return {'schema': 'citizen-presets/v1', 'presets': [asdict(p) for p in PRESETS.values()],
            'notice': 'Implemented means an execution adapter exists; live readiness and recorded acceptance are separate.'}
