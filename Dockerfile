FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip uv

COPY agent_fastapi ./agent_fastapi
COPY imp_agent_core ./imp_agent_core
COPY llm_inference_core ./llm_inference_core

WORKDIR /app/agent_fastapi
RUN uv sync --frozen --no-dev

RUN useradd --create-home --shell /usr/sbin/nologin appuser
USER appuser

EXPOSE 8080

CMD ["uvicorn", "agent_fastapi.main:app", "--host", "0.0.0.0", "--port", "8080"]
