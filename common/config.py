import os
from dotenv import load_dotenv

load_dotenv()  # Charger les variables d'environnement depuis .env

class Config:
    """
    Configuration globale pour AquaWatch-MS
    """

    # --- Sensor Simulation ---
    SENSOR_ID: str = os.getenv("SENSOR_ID", "sensor-01")
    READING_INTERVAL_SECONDS: int = int(os.getenv("READING_INTERVAL_SECONDS", 2))

    # --- Normal Ranges ---
    TEMP_NORMAL_MIN: float = 10.0
    TEMP_NORMAL_MAX: float = 35.0
    PRESSURE_NORMAL_MIN: float = 1.0
    PRESSURE_NORMAL_MAX: float = 3.0
    FLOW_NORMAL_MIN: float = 20.0
    FLOW_NORMAL_MAX: float = 100.0

    # --- Spike Detection Thresholds ---
    TEMP_SPIKE_THRESHOLD_HIGH: float = TEMP_NORMAL_MAX
    TEMP_SPIKE_THRESHOLD_LOW: float = TEMP_NORMAL_MIN
    PRESSURE_SPIKE_THRESHOLD_HIGH: float = PRESSURE_NORMAL_MAX
    PRESSURE_SPIKE_THRESHOLD_LOW: float = PRESSURE_NORMAL_MIN
    FLOW_SPIKE_THRESHOLD_HIGH: float = FLOW_NORMAL_MAX
    FLOW_SPIKE_THRESHOLD_LOW: float = FLOW_NORMAL_MIN
    PH_SPIKE_THRESHOLD_HIGH: float = 8.0
    PH_SPIKE_THRESHOLD_LOW: float = 6.0
    TURBIDITY_SPIKE_THRESHOLD_HIGH: float = 5.0
    CONDUCTIVITY_SPIKE_THRESHOLD_HIGH: float = 200.0

    # --- Drift Detection ---
    DRIFT_CONSECUTIVE_READINGS: int = 8

    # --- Dropout Detection ---
    DROPOUT_THRESHOLD_SECONDS: int = 10

    # --- Anomaly Storage ---
    ANOMALY_RETENTION_SECONDS: int = 120
    CLEANUP_INTERVAL_SECONDS: int = 60
    DATA_DIR: str = "/app/data"
    ANOMALIES_FILE: str = os.path.join(DATA_DIR, "anomalies.json")
    SUMMARY_FILE: str = os.path.join(DATA_DIR, "summary.json")

    # --- MQTT ---
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "mosquitto")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", 1883))
    MQTT_TOPIC: str = os.getenv("MQTT_TOPIC", "sensors/readings")

    # --- TimescaleDB ---
    TIMESCALEDB_DSN: str = os.getenv(
        "TIMESCALEDB_DSN",
        "postgresql://aquawatch:example@timescaledb:5432/aquawatch"
    )

    POSTGIS_DSN: str = os.getenv(
        "POSTGIS_DSN",
        "postgresql://aquawatch:example@postgis:5432/aquawatch_gis"
    )

    # --- LLM (Ollama) ---
    OLLAMA_HOST: str = "ollama"
    OLLAMA_PORT: int = 11434
    LLM_MODEL_NAME: str = "gemma2:2b"  # ✅ Remplacez "mistral"
    LLM_MAX_NEW_TOKENS: int = 100    # ✅ Réduisez pour accélérer la génération
    LLM_TEMPERATURE: float = 0.0  # Réduit à 0 pour accélérer la génération

    # --- Service Ports ---
    ANOMALY_DETECTOR_HOST: str = "anomaly_detector"  # Service name in docker-compose
    ANOMALY_DETECTOR_PORT: int = 8001

    SENSOR_SIMULATOR_HOST: str = "sensor_simulator"  # Service name in docker-compose
    SENSOR_SIMULATOR_PORT: int = 8002

    
    DATA_DIR = "/app/data"
    SUMMARY_FILE: str = os.path.join(DATA_DIR, "summary.json")