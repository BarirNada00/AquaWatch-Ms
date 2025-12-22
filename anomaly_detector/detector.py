import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from asyncio_mqtt import Client as MQTTClient, MqttError
import asyncpg
import uuid  # <-- AJOUT IMPORTANT

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.config import Config
from common.models import SensorReading, Anomaly, HealthStatus

# ---------------------------
# Logging
# ---------------------------
logger = logging.getLogger("anomaly_detector")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------
# Globals
# ---------------------------
recent_anomalies: List[Anomaly] = []
db_pool: Optional[asyncpg.Pool] = None
last_readings: dict = {}
health_status_data = HealthStatus(
    sensor_simulator_active=True,
    anomaly_detector_active=True,
    llm_summarizer_active=False,
    api_service_active=True,
    ollama_active=False,
    current_anomalies_count=0
)

# ---------------------------
# DB helpers
# ---------------------------
async def create_db_pool():
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=Config.TIMESCALEDB_DSN, min_size=1, max_size=10)

async def save_anomaly_to_db(anomaly: Anomaly):
    """
    Correction principale : générer un UUID si anomaly.id == None
    car la colonne id est TEXT NOT NULL dans PostgreSQL/TimescaleDB.
    """
    if not db_pool:
        return

    # --- CORRECTION : garantir un ID non null ---
    if not anomaly.id:
        anomaly.id = str(uuid.uuid4())

    query = """
        INSERT INTO anomalies (
            id, type, timestamp, sensor_id, parameter, value, duration_seconds, message, latitude, longitude
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """

    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                query,
                anomaly.id,                # <-- Correction : JAMAIS None
                anomaly.type,
                anomaly.timestamp,
                anomaly.sensor_id,
                anomaly.parameter,
                anomaly.value,
                anomaly.duration_seconds,
                anomaly.message,
                anomaly.latitude,
                anomaly.longitude,
            )
        logger.info(f"Anomaly saved: {anomaly.id}")

    except Exception as e:
        logger.error(f"Error inserting anomaly to DB: {e}")

async def write_anomalies_to_file():
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    try:
        anomalies_list = [a.model_dump(mode="json") for a in recent_anomalies]
        with open(Config.ANOMALIES_FILE, "w") as f:
            json.dump(anomalies_list, f, indent=2)

        # Save each anomaly to DB
        for a in recent_anomalies:
            await save_anomaly_to_db(a)

    except Exception as e:
        logger.error("Error writing anomalies to file/DB: %s", e)

# ---------------------------
# Anomaly detection logic
# ---------------------------
def detect_anomalies(reading: SensorReading) -> List[Anomaly]:
    anomalies = []
    now = datetime.now(timezone.utc)
    sensor_id = reading.sensor_id

    # Spike detection
    thresholds = {
        "temperature": Config.TEMP_SPIKE_THRESHOLD_HIGH,
        "pressure": Config.PRESSURE_SPIKE_THRESHOLD_HIGH,
        "flow": Config.FLOW_SPIKE_THRESHOLD_HIGH,
        "ph": Config.PH_SPIKE_THRESHOLD_HIGH,
        "turbidity": Config.TURBIDITY_SPIKE_THRESHOLD_HIGH,
        "conductivity": Config.CONDUCTIVITY_SPIKE_THRESHOLD_HIGH,
    }

    for param, limit in thresholds.items():
        value = getattr(reading, param)
        if value > limit:
            anomalies.append(Anomaly(
                type="SPIKE",
                timestamp=now,
                sensor_id=sensor_id,
                parameter=param,
                value=value,
                message=f"{param.capitalize()} spike detected",
                latitude=reading.latitude,
                longitude=reading.longitude
            ))

    # Drift detection
    sensor_history = last_readings.get(sensor_id, {})
    for param in thresholds.keys():
        last_values: List[float] = sensor_history.get(param, [])
        current_value = getattr(reading, param)
        last_values.append(current_value)
        if len(last_values) > Config.DRIFT_CONSECUTIVE_READINGS:
            last_values.pop(0)
        if len(last_values) == Config.DRIFT_CONSECUTIVE_READINGS:
            delta = max(last_values) - min(last_values)
            if delta > 2.0:
                anomalies.append(Anomaly(
                    type="DRIFT",
                    timestamp=now,
                    sensor_id=sensor_id,
                    parameter=param,
                    value=current_value,
                    message=f"{param.capitalize()} drift detected",
                    latitude=reading.latitude,
                    longitude=reading.longitude
                ))
        sensor_history[param] = last_values

    # Dropout detection
    last_ts = sensor_history.get("last_timestamp")
    if last_ts:
        delta_sec = (reading.timestamp - last_ts).total_seconds()
        if delta_sec > Config.DROPOUT_THRESHOLD_SECONDS:
            anomalies.append(Anomaly(
                type="DROPOUT",
                timestamp=now,
                sensor_id=sensor_id,
                parameter="all",
                value=0,
                message=f"Sensor inactive for {delta_sec:.1f} seconds",
                latitude=reading.latitude,
                longitude=reading.longitude
            ))
    sensor_history["last_timestamp"] = reading.timestamp
    last_readings[sensor_id] = sensor_history

    return anomalies

# ---------------------------
# MQTT listener
# ---------------------------
async def mqtt_listener():
    while True:
        try:
            logger.info("Connecting to MQTT broker at %s:%d", Config.MQTT_BROKER_HOST, Config.MQTT_BROKER_PORT)
            async with MQTTClient(Config.MQTT_BROKER_HOST, Config.MQTT_BROKER_PORT) as client:
                await client.subscribe(Config.MQTT_TOPIC)
                logger.info("Subscribed to topic: %s", Config.MQTT_TOPIC)
                async with client.unfiltered_messages() as messages:
                    async for message in messages:
                        try:
                            payload = message.payload.decode()
                            data = json.loads(payload)
                            reading = SensorReading(**data)
                            anomalies = detect_anomalies(reading)
                            if anomalies:
                                recent_anomalies.extend(anomalies)
                                health_status_data.last_anomaly_detected = datetime.now(timezone.utc)
                                health_status_data.current_anomalies_count = len(recent_anomalies)
                                await write_anomalies_to_file()
                                for a in anomalies:
                                    logger.info("Detected anomaly: %s", a.model_dump_json())
                        except Exception as e:
                            logger.error("Error processing MQTT message: %s", e)
        except MqttError as e:
            logger.error("MQTT error, reconnecting in 5s: %s", e)
            await asyncio.sleep(5)
        except Exception as e:
            logger.error("Unexpected error in MQTT listener, reconnecting in 5s: %s", e)
            await asyncio.sleep(5)

# ---------------------------
# Background cleanup
# ---------------------------
async def cleanup_old_anomalies():
    while True:
        cutoff = datetime.now(timezone.utc).timestamp() - Config.ANOMALY_RETENTION_SECONDS
        recent_anomalies[:] = [a for a in recent_anomalies if a.timestamp.timestamp() > cutoff]
        health_status_data.current_anomalies_count = len(recent_anomalies)
        await asyncio.sleep(Config.CLEANUP_INTERVAL_SECONDS)

# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI(title="AquaWatch-MS Anomaly Detector", version="1.0.0")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Anomaly Detector starting...")
    try:
        await create_db_pool()
        logger.info("Connected to TimescaleDB")
    except Exception as e:
        logger.warning("Could not connect to TimescaleDB, fallback to JSON only: %s", e)

    mqtt_task = asyncio.create_task(mqtt_listener())
    cleanup_task = asyncio.create_task(cleanup_old_anomalies())
    yield
    mqtt_task.cancel()
    cleanup_task.cancel()
    if db_pool:
        await db_pool.close()
    logger.info("Anomaly Detector shutdown complete")

app.router.lifespan_context = lifespan

@app.get("/status")
async def get_status():
    return health_status_data.model_dump(mode="json")

@app.get("/anomalies")
async def get_anomalies():
    return [a.model_dump(mode="json") for a in recent_anomalies]

@app.post("/data")
async def post_data(reading: SensorReading):
    anomalies = detect_anomalies(reading)
    if anomalies:
        recent_anomalies.extend(anomalies)
        health_status_data.last_anomaly_detected = datetime.now(timezone.utc)
        health_status_data.current_anomalies_count = len(recent_anomalies)
        await write_anomalies_to_file()
        for a in anomalies:
            logger.info("Detected anomaly via POST: %s", a.json())
    return {"status": "ok", "anomalies_detected": len(anomalies)}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
