# AquaWatch CI Pipeline Fix

## Issue
The Jenkins CI pipeline was failing at the "Sensor Simulator" stage with the error:
```
failed to solve: lstat /sensor_simulator: no such file or directory
```

## Root Cause
- The `sensor_simulator` service was not defined in `docker-compose.ci.yml`.
- The Dockerfile had incorrect COPY paths assuming a different build context.
- The service lacked proper environment variables and dependencies (mosquitto).

## Changes Made

### 1. Updated `sensor_simulator/Dockerfile`
- Removed `sensor_simulator/` prefix from COPY commands to match build context `./sensor_simulator`.

### 2. Updated `Jenkinsfile`
- Added proper environment variables for sensor_simulator:
  - `SENSOR_ID: sensor-01`
  - `MQTT_BROKER_HOST: mosquitto`
  - `MQTT_BROKER_PORT: 1883`
  - `MQTT_TOPIC: sensors/readings`
- Updated dependencies to `[anomaly_detector, mosquitto]`

## Verification
- The pipeline should now successfully build and run the sensor_simulator service.
- All subsequent stages should proceed without the previous failure.

## Next Steps
- Test the pipeline to ensure all services start correctly.
- Monitor health checks to confirm proper service interactions.
