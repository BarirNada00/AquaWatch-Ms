#!/bin/bash
# Script de démarrage pour lancer à la fois l'ETL et l'API

# Lancer l'ETL en arrière-plan
echo "Démarrage de l'ETL de synchronisation..."
python3 etl_anomalies.py &
ETL_PID=$!

# Attendre un peu pour que l'ETL se connecte
sleep 2

# Lancer l'API
echo "Démarrage de l'API REST/GeoJSON..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Fonction de nettoyage à l'arrêt
cleanup() {
    echo "Arrêt des services..."
    kill $ETL_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    exit 0
}

trap cleanup SIGTERM SIGINT

# Attendre que les processus se terminent
wait
