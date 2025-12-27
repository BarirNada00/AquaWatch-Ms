from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timezone
import json
import os
import sys
import httpx
import asyncpg
from py_eureka_client.eureka_client import EurekaClient

# Add the parent directory to sys.path to allow importing from common
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.config import Config
POSTGIS_DSN = Config.POSTGIS_DSN  # ✅ Utilisation de la config
from common.models import Anomaly, AnomalySummary, HealthStatus, SensorReading
from summarizer import LLMSummarizer

app = FastAPI(
    title="AquaSense-Monitor Public API",
    description="Provides access to recent anomalies, LLM summaries, and system health.",
    version="1.0.0",
)

llm_summarizer_instance = LLMSummarizer()

# Initialize Eureka client
eureka_client = EurekaClient(
    app_name='api-service',
    eureka_server="http://eureka-server:8761/eureka/",
    instance_host='api-service',
    instance_port=8004
)
eureka_client.register()

# --- Global State for Health Status ---
health_status_data = {
    "sensor_simulator_active": False,
    "anomaly_detector_active": False,
    "llm_summarizer_active": False,
    "api_service_active": True,
    "ollama_active": False,
    "last_sensor_reading_received": None,
    "last_anomaly_detected": None,
    "last_summary_generated": None,
    "current_anomalies_count": 0,
    "ollama_model_loaded": False,
}

# URL for the anomaly detector service (non utilisé dans /summary)
anomaly_detector_url = (
    f"http://{Config.ANOMALY_DETECTOR_HOST}:{Config.ANOMALY_DETECTOR_PORT}/anomalies"
)


async def check_service_health(
    service_host: str, port: int, endpoint: str = "/status", return_data=False
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{service_host}:{port}{endpoint}", timeout=5
            )
            response.raise_for_status()
            if return_data:
                return True, response.json()
            else:
                return True
    except (httpx.RequestError, httpx.HTTPStatusError):
        return (False, None) if return_data else False


async def check_ollama_model_loaded():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{Config.OLLAMA_HOST}:{Config.OLLAMA_PORT}/api/show",
                json={"name": Config.LLM_MODEL_NAME},
                timeout=5,
            )
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"Ollama model check failed: {e}")
        return False


@app.get("/anomalies_from_db", response_model=List[Anomaly])
async def get_anomalies_from_db():
    try:
        conn = await asyncpg.connect(POSTGIS_DSN)
        rows = await conn.fetch("""
            SELECT 
                id, 
                type, 
                timestamp, 
                sensor_id, 
                parameter, 
                value, 
                message,
                ST_X(geom) AS longitude,
                ST_Y(geom) AS latitude
            FROM anomalies_gis
            WHERE geom IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        await conn.close()

        anomalies = []
        for row in rows:
            anomaly_data = {
                "id": row["id"],
                "type": row["type"],
                "timestamp": row["timestamp"],
                "sensor_id": row["sensor_id"],
                "parameter": row["parameter"],
                "value": row["value"],
                "message": row["message"],
                "latitude": float(row["latitude"]) if row["latitude"] is not None else None,
                "longitude": float(row["longitude"]) if row["longitude"] is not None else None,
                # ⚠️ duration_seconds n'existe PAS → on met None (compatible avec le modèle Pydantic)
                "duration_seconds": None
            }
            anomalies.append(Anomaly(**anomaly_data))

        return anomalies

    except Exception as e:
        # 🔥 Ajoutez un log explicite pour voir l'erreur en production
        print(f"🚨 Erreur PostGIS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur PostGIS : {str(e)}")

# ✅ Endpoint /summary : utilise les anomalies de PostGIS
@app.get("/summary", response_model=AnomalySummary)
async def get_latest_summary():
    anomalies = await get_anomalies_from_db()
    success, summary_output = await llm_summarizer_instance.generate_summary(anomalies)
    health_status_data["last_summary_generated"] = datetime.now(timezone.utc)

    if success:
        return summary_output
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate anomaly summary: {summary_output}",
        )


@app.get("/status", response_model=HealthStatus)
async def get_health_status():
    if not os.path.exists(Config.DATA_DIR):
        print(f"Warning: Shared data directory {Config.DATA_DIR} does not exist.")

    health_status_data["anomaly_detector_active"] = await check_service_health(
        Config.ANOMALY_DETECTOR_HOST,
        Config.ANOMALY_DETECTOR_PORT,
        endpoint="/anomalies",
    )

    llm_summarizer_health_status, _ = await llm_summarizer_instance.check_llm_status()
    health_status_data["llm_summarizer_active"] = llm_summarizer_health_status

    health_status_data["ollama_active"] = await check_service_health(
        Config.OLLAMA_HOST,
        Config.OLLAMA_PORT,
        endpoint="/api/tags",
    )
    health_status_data["ollama_model_loaded"] = await check_ollama_model_loaded()

    health_status_data["sensor_simulator_active"], sensor_simulator_data = (
        await check_service_health(
            Config.SENSOR_SIMULATOR_HOST,
            Config.SENSOR_SIMULATOR_PORT,
            endpoint="/status",
            return_data=True,
        )
    )
    if sensor_simulator_data:
        health_status_data["last_sensor_reading_received"] = sensor_simulator_data.get(
            "last_data_sent", health_status_data["last_sensor_reading_received"]
        )

    return HealthStatus(**health_status_data)


@app.get("/discovery")
async def get_discovery():
    """Get registered services from Eureka"""
    try:
        applications = eureka_client.get_applications()
        return {"services": applications.get_apps()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eureka discovery failed: {str(e)}")
