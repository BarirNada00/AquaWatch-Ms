# Plan to Fix GeoServer API Integration and Run Front/Backend

## Step 1: Update API Endpoints for Docker Networking
- [ ] Update web-unifiee/src/services/api.js to ensure proper endpoints for Docker services

## Step 2: Fix MapContainer.vue API Calls
- [ ] Update loadCapteurs to use api.getCapteursGeoJSON() instead of deriving from anomalies
- [ ] Update loadZones to use api.getZones() properly
- [ ] Fix duplicate zoneLayers declarations
- [ ] Ensure anomalies load correctly from GeoServer WFS

## Step 3: Run Backend Services
- [ ] Execute docker-compose up to start all services including GeoServer

## Step 4: Run Frontend
- [ ] Execute npm run dev in web-unifiee directory

## Step 5: Test Integration
- [ ] Verify anomalies display on map from GeoServer API
- [ ] Check that capteurs and zones load correctly
