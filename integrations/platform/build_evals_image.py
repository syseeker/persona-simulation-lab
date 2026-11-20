"""Supply a native task image to a local Helix installation without restarting it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'citizen-helix-evals:0.1.0'


def build(platform_task_image: str):
    # The existing local installation uses this unpopulated development tag.
    # Never overwrite another operator's image or change its server config.
    if platform_task_image not in {IMAGE, 'my-registry/nhx-tasks:local'}:
        raise ValueError('Select the documented local task image reference')
    existing = subprocess.run(['docker', 'image', 'inspect', platform_task_image], capture_output=True, text=True)
    if existing.returncode == 0:
        labels = json.loads(existing.stdout)[0]['Config'].get('Labels') or {}
        if labels.get('citizen.lab.role') != 'retail-evaluation-tasks':
            raise ValueError('The task tag already belongs to another image; no replacement was attempted')
    dockerfile = ROOT / 'integrations/platform/Dockerfile.evals'
    with tempfile.TemporaryDirectory(prefix='citizen-evaluation-image-') as directory:
        source = Path(directory) / 'Dockerfile'
        source.write_bytes(dockerfile.read_bytes())
        subprocess.run(['uv', 'export', '--project', str(ROOT / 'integrations/platform'),
                        '--frozen', '--no-dev', '--no-editable', '--output-file',
                        str(Path(directory) / 'requirements.txt')], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['docker', 'build', '--tag', IMAGE, directory], check=True)
    subprocess.run(['docker', 'tag', IMAGE, platform_task_image], check=True)
    image_id = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', IMAGE], text=True).strip()
    return {'image': IMAGE, 'image_id': image_id, 'platform_task_image': platform_task_image,
            'helix_version': '0.10.0', 'dockerfile_sha256': hashlib.sha256(dockerfile.read_bytes()).hexdigest(),
            'server_configuration_changed': False, 'contains_private_profiles': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform-task-image', default=IMAGE)
    print(json.dumps(build(parser.parse_args().platform_task_image)))
