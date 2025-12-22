"""
STModel Service - Spatio-temporal prediction for AquaWatch
"""

import os
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
import uvicorn
import torch
import torch.nn as nn
import numpy as np
from dotenv import load_dotenv
from pydantic import BaseModel

# Load configuration
load_dotenv()

# ====================
# MACHINE LEARNING MODEL
# ====================

class WaterQualityPredictor(nn.Module):
    """Neural network for water quality prediction."""
    def __init__(self, input_features=5, hidden_size=64, output_features=3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_features,
            hidden_size=hidden_size,
            num_layers=2,
            batch_first=True,
            dropout=0.2
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, output_features)
        )
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        return self.fc(last_output)

# ====================
# MQTT CLIENT FOR REAL-TIME DATA
# ====================

class SensorDataCollector:
    """Collects real-time data from MQTT broker."""
    def __init__(self, buffer_size=1000):
        self.data_buffer = []
        self.buffer_size = buffer_size
        self.client = mqtt.Client()
        self.setup_mqtt()
    
    def setup_mqtt(self):
        """Configure MQTT connection and callbacks."""
        broker = os.getenv("MQTT_BROKER", "mosquitto")
        port = int(os.getenv("MQTT_PORT", 1883))
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.loop_start()
        print(f"Connected to MQTT broker at {broker}:{port}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker."""
        print(f"MQTT connection established with code {rc}")
        client.subscribe("sensors/+/data")
    
    def on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        try:
            data = json.loads(msg.payload.decode())
            self.data_buffer.append(data)
            if len(self.data_buffer) > self.buffer_size:
                self.data_buffer.pop(0)
        except json.JSONDecodeError as e:
            print(f"Error decoding MQTT message: {e}")
    
    def get_recent_data(self, station_id, max_points=24):
        """Get recent data for a specific station."""
        station_data = [d for d in self.data_buffer if d.get('station_id') == station_id]
        return station_data[-max_points:] if station_data else []

# ====================
# FASTAPI APPLICATION
# ====================

app = FastAPI(
    title="STModel Service",
    description="Spatio-temporal water quality prediction",
    version="1.0.0"
)

# Initialize global components
predictor = WaterQualityPredictor()
data_collector = SensorDataCollector()

class PredictionRequest(BaseModel):
    station_id: str
    horizon_hours: int = 24

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    print("STModel Service starting...")
    # Load pre-trained model if available
    model_path = os.getenv("MODEL_PATH", "./model.pth")
    if os.path.exists(model_path):
        predictor.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        predictor.eval()
        print("Loaded pre-trained model")
    print("Service ready")

@app.get("/")
async def root():
    """Service root endpoint."""
    return {
        "service": "STModel",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "train": "/train"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": True,
        "data_points": len(data_collector.data_buffer)
    }

@app.post("/predict")
async def make_prediction(request: PredictionRequest):
    """
    Make a prediction for a specific station.
    Example: {"station_id": "station_01", "horizon_hours": 24}
    """
    # Get recent data for this station
    recent_data = data_collector.get_recent_data(request.station_id, max_points=24)
    
    if len(recent_data) < 12:  # Require at least 12 data points
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data for station {request.station_id}. Have {len(recent_data)} points, need at least 12."
        )
    
    # Prepare features from data (simplified - adapt to your actual data structure)
    # This assumes each data point has: temperature, ph, turbidity, conductivity, dissolved_oxygen
    feature_keys = ['temperature', 'ph', 'turbidity', 'conductivity', 'dissolved_oxygen']
    
    try:
        # Extract and normalize features
        features = []
        for point in recent_data:
            row = [point.get(key, 0.0) for key in feature_keys]
            features.append(row)
        
        # Convert to tensor
        features_array = np.array(features, dtype=np.float32)
        
        # Normalize (using example values - should be calibrated)
        mean_vals = np.array([20.0, 7.0, 15.0, 500.0, 8.0])  # Example means
        std_vals = np.array([5.0, 0.5, 10.0, 200.0, 2.0])    # Example standard deviations
        features_normalized = (features_array - mean_vals) / std_vals
        
        # Add batch dimension and predict
        input_tensor = torch.FloatTensor(features_normalized).unsqueeze(0)
        
        with torch.no_grad():
            prediction = predictor(input_tensor).numpy()[0]
        
        # Inverse normalization for output
        output_means = np.array([7.0, 15.0, 20.0])  # Example for ph, turbidity, temperature
        output_stds = np.array([0.5, 10.0, 5.0])
        final_prediction = (prediction * output_stds) + output_means
        
        # Generate time slots for the prediction horizon
        now = datetime.now()
        time_slots = [
            (now.timestamp() + i * 3600)  # Add i hours in seconds
            for i in range(1, request.horizon_hours + 1)
        ]
        
        return {
            "station_id": request.station_id,
            "prediction_timestamp": now.isoformat(),
            "horizon_hours": request.horizon_hours,
            "values": {
                "predicted_ph": float(final_prediction[0]),
                "predicted_turbidity": float(final_prediction[1]),
                "predicted_temperature": float(final_prediction[2])
            },
            "time_slots": time_slots,
            "data_points_used": len(recent_data),
            "model_version": "1.0"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/train")
async def train_model():
    """Endpoint to trigger model training (stub for now)."""
    return {
        "job_id": f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": "scheduled",
        "message": "Training pipeline not fully implemented. Use train_model.py script.",
        "estimated_duration": "2-3 hours"
    }

# ====================
# SERVICE ENTRY POINT
# ====================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("STModel Service - AquaWatch Project")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8003)),
        log_level="info"
    )