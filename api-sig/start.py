#!/usr/bin/env python3
# AquaWatch/api-sig/start.py
# Script de démarrage pour lancer à la fois l'ETL et l'API
import asyncio
import signal
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales pour les tâches
etl_task = None
api_task = None

def signal_handler(sig, frame):
    """Gestionnaire pour arrêter proprement les processus"""
    logger.info("Arrêt des services...")
    if etl_task:
        etl_task.cancel()
    if api_task:
        api_task.cancel()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

async def run_etl():
    """Lancer l'ETL en tâche de fond"""
    try:
        import etl_anomalies
        await etl_anomalies.main_loop()
    except asyncio.CancelledError:
        logger.info("ETL arrêté")
        raise
    except Exception as e:
        logger.error(f"Erreur dans l'ETL: {e}", exc_info=True)

async def run_api():
    """Lancer l'API"""
    try:
        import uvicorn
        from main import app
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    except asyncio.CancelledError:
        logger.info("API arrêtée")
        raise
    except Exception as e:
        logger.error(f"Erreur dans l'API: {e}", exc_info=True)

async def main():
    """Lancer les deux services en parallèle"""
    global etl_task, api_task
    
    logger.info("Démarrage des services API-SIG...")
    logger.info("  - ETL de synchronisation TimescaleDB -> PostGIS")
    logger.info("  - API REST/GeoJSON sur le port 8000")
    
    # Lancer l'ETL et l'API en tâches parallèles
    etl_task = asyncio.create_task(run_etl())
    api_task = asyncio.create_task(run_api())
    
    # Attendre que l'une des tâches se termine (ou soit annulée)
    done, pending = await asyncio.wait(
        [etl_task, api_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    # Annuler les tâches restantes
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur.")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
