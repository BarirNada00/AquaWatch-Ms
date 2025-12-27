# Utiliser une image Python récente basée sur Debian Bookworm
FROM python:3.10-slim-bookworm

WORKDIR /app

# Installer curl pour le healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY anomaly_detector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code commun et le microservice
COPY common/ /app/common/
COPY anomaly_detector/*.py .

# Créer dossier pour stocker les anomalies
RUN mkdir -p /app/data

# Exposer le port FastAPI
EXPOSE 8001

# Commande pour lancer FastAPI
CMD ["uvicorn", "detector:app", "--host", "0.0.0.0", "--port", "8001"]
