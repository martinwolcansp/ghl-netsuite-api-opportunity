# Dockerfile — ghl-netsuite-api-opportunities (Etapa 2)
# Imagen liviana para Coolify, siguiendo la base sugerida en el Plan de
# Migración v1.1 (python:3.11-slim). Sin capas de build innecesarias:
# sólo FastAPI/uvicorn + dependencias de requirements.txt.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Health check propio (además del que puede configurarse en Coolify contra /health)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
