from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SensorReading(BaseModel):
    sensor_id: str
    timestamp: datetime
    temperature: Optional[float] = None
    ph: Optional[float] = None
    turbidity: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    conductivity: Optional[float] = None

class Anomaly(BaseModel):
    id: int
    type: str
    timestamp: datetime
    sensor_id: str
    parameter: str
    value: float
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    duration_seconds: Optional[int] = None

class AnomalySummary(BaseModel):
    summary: str
    total_anomalies: int
    anomalies: List[Anomaly]

class HealthStatus(BaseModel):
    sensor_simulator_active: bool
    anomaly_detector_active: bool
    llm_summarizer_active: bool
    api_service_active: bool
    ollama_active: bool
    last_sensor_reading_received: Optional[datetime] = None
    last_anomaly_detected: Optional[datetime] = None
    last_summary_generated: Optional[datetime] = None
    current_anomalies_count: int
    ollama_model_loaded: bool
