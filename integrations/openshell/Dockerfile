# Compatible SDKs come from the project's immutable uv lock, without Helix.
ARG PYTHON_IMAGE=ghcr.io/astral-sh/uv:python3.12-bookworm-slim
FROM ${PYTHON_IMAGE} AS environment
WORKDIR /opt/lab
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src/learning_lab ./src/learning_lab
# Editable installation keeps the package's repository-root calculation intact
# and makes MCP subprocess imports independent of inherited PYTHONPATH.
RUN uv sync --locked --no-dev

FROM ${PYTHON_IMAGE}
RUN groupadd --gid 1000 sandbox && useradd --uid 1000 --gid sandbox --create-home sandbox
WORKDIR /opt/lab
COPY --from=environment /opt/lab/.venv /opt/lab/.venv
COPY src/learning_lab /opt/lab/src/learning_lab
COPY catalogue /opt/lab/catalogue
COPY runtime-skills /opt/lab/runtime-skills
COPY integrations/openshell/image-manifest.json /opt/lab/image-manifest.json
RUN printf 'public non-secret Landlock test fixture\n' > /lab-denied.txt && chmod 0444 /lab-denied.txt && \
    chmod -R a-w /opt/lab && mkdir -p /workspace && chown sandbox:sandbox /workspace
ENV PYTHONPATH=/opt/lab/src PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/lab/.venv/bin:$PATH UV_OFFLINE=1
WORKDIR /workspace
USER sandbox
CMD ["sleep", "infinity"]
