# Compatible SDKs come from the project's immutable uv lock, without Helix.
ARG PYTHON_IMAGE=ghcr.io/astral-sh/uv:python3.12-bookworm-slim
FROM ${PYTHON_IMAGE} AS environment
WORKDIR /opt/lab
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY integrations/guardrails /opt/lab/integrations/guardrails
RUN uv sync --project integrations/guardrails --locked --python /usr/local/bin/python3.12 --no-dev
# Hermes keeps its upstream-compatible Python and dependencies separate from
# the application's UserSim/Fabric environment.
RUN uv python install 3.14.0 --install-dir /opt/python
COPY integrations/hermes/upstream /opt/hermes/source
COPY integrations/platform/install_hermes.py /tmp/install_hermes.py
RUN uv venv --python /opt/python/cpython-3.14*-linux-*/bin/python3.14 /opt/lab/integrations/hermes/.venv && \
    python /tmp/install_hermes.py --checkout /opt/hermes/source --python /opt/lab/integrations/hermes/.venv/bin/python
COPY src/learning_lab ./src/learning_lab
# Editable installation keeps MCP imports independent of inherited PYTHONPATH.
RUN uv sync --locked --no-dev

FROM ${PYTHON_IMAGE}
RUN groupadd --gid 1000 sandbox && useradd --uid 1000 --gid sandbox --create-home sandbox
WORKDIR /opt/lab
COPY --from=environment /opt/lab/.venv /opt/lab/.venv
COPY --from=environment /opt/lab/integrations /opt/lab/integrations
COPY --from=environment /opt/python /opt/python
COPY --from=environment /opt/hermes /opt/hermes
COPY src/learning_lab /opt/lab/src/learning_lab
COPY catalogue /opt/lab/catalogue
COPY runtime-skills /opt/lab/runtime-skills
COPY integrations/openshell/image-manifest.json /opt/lab/image-manifest.json
COPY integrations/hermes/managed /opt/lab/integrations/hermes/managed
RUN printf 'public non-secret Landlock test fixture\n' > /lab-denied.txt && chmod 0444 /lab-denied.txt && \
    chmod a-w /opt/lab /opt/hermes /opt/python && mkdir -p /workspace && chown sandbox:sandbox /workspace
ENV PYTHONPATH=/opt/lab/src PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/lab/.venv/bin:$PATH UV_OFFLINE=1
WORKDIR /workspace
USER sandbox
CMD ["sleep", "infinity"]
