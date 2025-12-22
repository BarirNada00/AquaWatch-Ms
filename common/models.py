from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid


class SensorReading(BaseModel):
    timestamp: datetime
    sensor_id: str
    latitude: float
    longitude: float
    temperature: float
    pressure: float
    flow: float
    ph: float
    turbidity: float
    conductivity: float


class Anomaly(BaseModel):
    # Génère automatiquement un UUID si non fourni → évite les erreurs DB
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    type: str
    timestamp: datetime
    sensor_id: str
    parameter: str
    value: float
    duration_seconds: Optional[int] = None
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AnomalySummary(BaseModel):
    overall_status: str = Field(
        ...,
        description="Overall operational status based on anomalies (e.g., 'Major', 'Minor', 'Critical')."
    )
    summary_message: str = Field(
        ...,
        description="A concise human-readable summary message about anomalies."
    )
    anomalies_count: int = Field(
        ...,
        description="Total number of anomalies detected."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the summary was generated."
    )


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
    ollama_model_loaded: bool = False
