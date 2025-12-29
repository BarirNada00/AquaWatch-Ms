# Jenkinsfile Modifications for Consistency and Functionality

## Issues Identified
1. **Port Inconsistencies**: CI docker-compose.ci.yml has wrong internal ports for some services.
   - anomaly_detector: CI has 8002, but Dockerfile/CMD uses 8001
   - satellite_processor: CI has 8003, but Dockerfile/CMD uses 5000
   - sensor_simulator: CI has 8004, but Dockerfile/CMD uses 8002
   - api_sig: CI has 8001, but Dockerfile/CMD uses 8000

2. **Environment Variables**: CI uses DATABASE_URL, but services expect TIMESCALEDB_DSN and POSTGIS_DSN.

3. **Health Checks**: Missing health check for satellite_processor, and ports may be wrong after fixes.

4. **Dependencies**: Some dependencies may be missing or incorrect.

## Tasks
- [ ] Fix ports in docker-compose.ci.yml for consistency
- [ ] Fix environment variables to match service expectations
- [ ] Update health checks to include satellite_processor and correct ports
- [ ] Ensure Eureka registration uses correct ports
- [ ] Test the pipeline after changes

## Files to Modify
- Jenkinsfile: Update the writeFile for docker-compose.ci.yml and health checks
