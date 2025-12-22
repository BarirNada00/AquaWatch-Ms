import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../services/api.js";

export const useDataStore = defineStore("data", () => {
  const anomalies = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const fetchAnomalies = async () => {
    loading.value = true;
    error.value = null;
    try {
      console.log("🔄 Fetching anomalies from GeoServer WFS...");
      const data = await api.getAnomaliesWFS();
      console.log("✓ WFS response:", data);
      console.log("✓ Data type:", typeof data);
      console.log("✓ Data keys:", Object.keys(data || {}));

      if (data && data.type === 'FeatureCollection' && Array.isArray(data.features)) {
        console.log(`📊 Received ${data.features.length} features from WFS`);

        if (data.features.length > 0) {
          // LOG LA PREMIÈRE FEATURE POUR VOIR SA STRUCTURE
          console.log("🔍 First feature structure:", data.features[0]);
          console.log("🔍 First feature properties:", data.features[0].properties);
          console.log("🔍 First feature geometry:", data.features[0].geometry);

          // Vérifier quels types existent dans les données
          const allTypes = [...new Set(data.features.map(f => f.properties?.type))];
          console.log("📋 All types found in data:", allTypes);

          // Filtrer SEULEMENT les anomalies (type = SPIKE, DRIFT, DROPOUT)
          const anomalyTypes = ['SPIKE', 'DRIFT', 'DROPOUT'];
          const filtered = data.features.filter(feature =>
            anomalyTypes.includes(feature.properties?.type?.toUpperCase())
          );

          console.log(`📊 Filtered ${filtered.length} anomalies from ${data.features.length} features`);

          anomalies.value = filtered.map((feature) => {
            // Handle different geometry formats
            let latitude = 0;
            let longitude = 0;

            if (feature.geometry && feature.geometry.coordinates) {
              if (Array.isArray(feature.geometry.coordinates) && feature.geometry.coordinates.length >= 2) {
                // GeoJSON Point: [longitude, latitude]
                longitude = feature.geometry.coordinates[0];
                latitude = feature.geometry.coordinates[1];
              }
            }

            return {
              id: feature.properties?.id ?? feature.id ?? Math.random().toString(36).slice(2),
              type: feature.properties?.type?.toUpperCase() ?? "UNKNOWN",
              timestamp: feature.properties?.timestamp ?? new Date().toISOString(),
              sensor_id: feature.properties?.sensor_id ?? "sensor-unknown",
              parameter: feature.properties?.parameter ?? "unknown",
              value: feature.properties?.value ?? null,
              message: feature.properties?.message ?? "",
              latitude: latitude,
              longitude: longitude,
            };
          }).filter(anomaly => anomaly.latitude !== 0 && anomaly.longitude !== 0) // Filter out invalid coordinates
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

          console.log(`✅ Final anomalies count: ${anomalies.value.length}`);
          error.value = null;
        } else {
          anomalies.value = [];
          error.value = "No features in WFS response";
          console.warn("No features in WFS response", data);
        }
      } else {
        anomalies.value = [];
        error.value = "Invalid WFS response format";
        console.error("Invalid WFS response format:", data);
      }
    } catch (e) {
      console.error("Error fetching anomalies:", e);
      anomalies.value = [];
      error.value = e?.message ?? String(e);
    } finally {
      loading.value = false;
    }
  };

  const refreshData = async () => {
    await fetchAnomalies();
  };

  return {
    anomalies,
    loading,
    error,
    fetchAnomalies,
    refreshData,
  };
});