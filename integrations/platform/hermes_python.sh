#!/bin/sh
# OpenShell exec deliberately resets image ENV. Set only this image's public
# harness runtime selections before Helix imports Fabric and chooses a runner.
export ADAPTER_PYTHON=/opt/hermes-venv/bin/python
export HERMES_MANAGED_DIR=/workspace/hermes-managed
export HERMES_STREAM_RETRIES=0
exec /workspace/.venv/bin/python-real "$@"
