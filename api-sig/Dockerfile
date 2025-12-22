# Dockerfile pour API-SIG (ETL + API REST/GeoJSON)
FROM python:3.10-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances et installer les packages Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code de l'application
COPY . .

# Rendre le script de démarrage exécutable
RUN chmod +x start.py

# Définir la commande principale : lancer à la fois l'ETL et l'API
CMD ["python3", "start.py"]
