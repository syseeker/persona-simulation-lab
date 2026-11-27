"""Application labels agree without changing SDK or protocol versions."""
import json
from pathlib import Path
import tomllib

from learning_lab import __version__


def test_application_release_metadata_agrees():
    root = Path(__file__).resolve().parents[1]
    python = tomllib.loads((root / 'pyproject.toml').read_text())
    web = json.loads((root / 'web/package.json').read_text())
    lock = json.loads((root / 'web/package-lock.json').read_text())
    assert python['project']['version'] == web['version'] == lock['version'] == lock['packages']['']['version'] == __version__ == '0.3.0'
