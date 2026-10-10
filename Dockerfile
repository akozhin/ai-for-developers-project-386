# Образ приложения «Запись на звонок»: backend и собранный frontend в одном процессе (ADR-004).
# Запуск: docker run -e PORT=8000 -p 8000:8000 <образ>; БД и флаги — в docker/entrypoint.sh.

# --- Frontend: статический экспорт Next.js ---
FROM node:24-slim AS frontend
ENV PNPM_HOME=/pnpm
ENV PATH="${PNPM_HOME}:${PATH}"
RUN corepack enable
WORKDIR /srv/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build:static

# --- Рантайм: FastAPI раздаёт API и собранный frontend ---
FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PATH="/srv/backend/.venv/bin:${PATH}"
WORKDIR /srv/backend
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
# Раскладка как в репозитории: настройки ищут контракт, данные и frontend относительно корня.
COPY api/openapi.yaml /srv/api/openapi.yaml
COPY seed/ /srv/seed/
COPY --from=frontend /srv/frontend/out /srv/frontend/out
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN useradd --uid 10001 --no-create-home app && chown -R app /srv
USER app

ENV PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/health')"]
ENTRYPOINT ["entrypoint.sh"]
