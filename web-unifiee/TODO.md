# Frontend Adaptation TODO

## Completed
- [ ] Analyze current codebase
- [ ] Create adaptation plan

## In Progress
- [ ] Update api.js: Add methods for /summary and /anomalies_from_db, change base URL to localhost:8004
- [ ] Update data.store.js: Add functions to fetch summary and anomalies data
- [ ] Update map.store.js: Change center to Morocco coordinates (31.7917°N, -7.0926°W)
- [ ] Create AnomalyChart.vue component using Chart.js for bar chart of anomalies by type
- [ ] Restructure HomeView.vue: Update navbar title to "AquaSense AI Assistant" with green status badge, add right panel with status/summary/count/refresh button, place chart below map
- [ ] Update MapContainer.vue: Use new anomalies data, color markers by type (🔴 SPIKE, 🟡 DRIFT, ⚪ DROPOUT), center on Morocco
- [ ] Add auto-refresh every 30 seconds

## Followup
- [ ] Run the application to test functionality
- [ ] Ensure backend CORS allows frontend requests
