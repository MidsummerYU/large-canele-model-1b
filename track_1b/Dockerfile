FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# The environment lives outside /app, because `make run` mounts the checkout over /app.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY src ./src
RUN uv sync --frozen

ENTRYPOINT ["/opt/venv/bin/newcomer-qa"]
CMD ["evaluate"]
