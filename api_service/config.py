# config.py
import os

class Config:
    # Database configurations
    POSTGIS_DSN = os.getenv("POSTGIS_DSN", "postgresql://aquawatch:example@postgis:5432/aquawatch_gis")
    
    # Service URLs
    ANOMALY_DETECTOR_HOST = os.getenv("ANOMALY_DETECTOR_HOST", "anomaly-detector")
    ANOMALY_DETECTOR_PORT = int(os.getenv("ANOMALY_DETECTOR_PORT", "8001"))
    
    SENSOR_SIMULATOR_HOST = os.getenv("SENSOR_SIMULATOR_HOST", "sensor_simulator")
    SENSOR_SIMULATOR_PORT = int(os.getenv("SENSOR_SIMULATOR_PORT", "8002"))
    
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama")
    OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
    
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemma2:2b")
    
    # Data directory
    DATA_DIR = os.getenv("DATA_DIR", "/app/data")
    
    # Eureka server
    EUREKA_SERVER_URL = os.getenv("EUREKA_SERVER_URL", "http://eureka-server:8761/eureka/")
