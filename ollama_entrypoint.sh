#!/bin/bash
set -e

# Installer curl
apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Démarrer Ollama
echo "🚀 Démarrage du serveur Ollama..."
ollama serve &
OLLAMA_PID=$!

# Attendre que le serveur soit prêt
echo "⏳ Attente que le serveur Ollama soit prêt..."
until curl -f http://localhost:11434; do
  sleep 2
done

# Télécharger gemma2:2b
echo "📥 Téléchargement du modèle 'gemma2:2b'..."
ollama pull gemma2:2b

echo "✅ Modèle 'gemma2:2b' prêt !"

# Garder le conteneur actif
wait $OLLAMA_PID