FROM python:3.12-slim AS runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv

COPY app ./app
RUN python -m compileall -q app && useradd --system --uid 10001 appuser

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]