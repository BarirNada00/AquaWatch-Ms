<template>
  <div class="h-full w-full relative rounded-lg overflow-hidden shadow-lg">
    <div id="map" class="h-full w-full"></div>

    <!-- Layer Controls -->
    <div class="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3 z-[1000]">
      <h3 class="text-sm font-semibold mb-2">Couches</h3>
      <div class="space-y-2">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            v-model="showAnomalies"
            @change="toggleAnomalies"
            class="rounded"
          />
          <span class="text-sm">🔴 Anomalies ({{ dataStore.anomalies.length }})</span>
        </label>
      </div>
    </div>

    <!-- Status Info -->
    <div class="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 z-[1000] max-w-xs">
      <div v-if="dataStore.loading" class="text-sm text-blue-600">
        ⏳ Chargement des anomalies...
      </div>
      <div v-else-if="dataStore.error" class="text-sm text-red-600">
        ❌ {{ dataStore.error }}
      </div>
      <div v-else class="text-sm text-green-600">
        ✓ {{ dataStore.anomalies.length }} anomalies affichées
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue';
import L from 'leaflet';
import { useDataStore } from '../../stores/data.store';

const dataStore = useDataStore();
let map = null;
let anomalyMarkers = [];
const showAnomalies = ref(true);

// Fix pour les icônes Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png'
});

const getAnomalyColor = (type) => {
  switch (type) {
    case 'SPIKE': return '#e63946';
    case 'DRIFT': return '#f77f00';
    case 'DROPOUT': return '#a8dadc';
    default: return '#457b9d';
  }
};

const loadAnomalies = () => {
  // Clear existing markers
  anomalyMarkers.forEach(marker => {
    if (map && map.hasLayer(marker)) {
      map.removeLayer(marker);
    }
  });
  anomalyMarkers = [];

  console.log('📍 Loading anomalies on map:', dataStore.anomalies.length);

  dataStore.anomalies.forEach(anomaly => {
    if (anomaly.latitude && anomaly.longitude) {
      const color = getAnomalyColor(anomaly.type);
      
      const marker = L.circleMarker([anomaly.latitude, anomaly.longitude], {
        radius: 8,
        fillColor: color,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      })
        .bindPopup(`
          <div class="p-2 text-sm">
            <div class="font-bold" style="color: ${color}">${anomaly.type}</div>
            <div>🔹 Sensor: ${anomaly.sensor_id}</div>
            <div>📊 Param: ${anomaly.parameter}</div>
            <div>📈 Value: ${typeof anomaly.value === 'number' ? anomaly.value.toFixed(2) : anomaly.value}</div>
            <div class="text-xs text-gray-600">${anomaly.message}</div>
            <div class="text-xs text-gray-500">${new Date(anomaly.timestamp).toLocaleString()}</div>
          </div>
        `)
        .on('click', () => {
          console.log('Clicked anomaly:', anomaly);
        });

      if (showAnomalies.value && map) {
        marker.addTo(map);
      }
      anomalyMarkers.push(marker);
    } else {
      console.warn('Anomaly missing coordinates:', anomaly.id, anomaly.latitude, anomaly.longitude);
    }
  });
};

const toggleAnomalies = () => {
  if (!map) return;
  if (showAnomalies.value) {
    anomalyMarkers.forEach(marker => marker.addTo(map));
  } else {
    anomalyMarkers.forEach(marker => {
      if (map.hasLayer(marker)) {
        map.removeLayer(marker);
      }
    });
  }
};

onMounted(async () => {
  console.log('🗺️ Initializing map...');
  map = L.map('map').setView([34.02, -6.73], 10);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  // Load anomalies from store; store itself calls GeoServer WFS
  await dataStore.fetchAnomalies();
  loadAnomalies();
});

onUnmounted(() => {
  if (map) {
    map.remove();
  }
});

// refresh markers when anomalies change
watch(() => dataStore.anomalies, () => {
  console.log('📍 Anomalies data changed, reloading map markers...');
  loadAnomalies();
}, { deep: true });

// update markers after loading completes
watch(() => dataStore.loading, (isLoading) => {
  if (!isLoading && dataStore.anomalies.length > 0) {
    console.log('✓ Anomalies loaded, updating map');
    loadAnomalies();
  }
});
</script>

<style scoped>
#map {
  z-index: 1;
  height: 100%;
}
</style>
