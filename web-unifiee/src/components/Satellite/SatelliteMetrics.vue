<template>
  <div class="satellite-metrics">
    <h3 class="text-lg font-semibold mb-4">Métriques Satellitaires</h3>

    <!-- Section AOI -->
    <div class="aoi-section mb-6">
      <h4 class="text-md font-medium mb-2">Zones d'Intérêt (AOI)</h4>
      <div v-if="satelliteStore.aois.length === 0" class="text-sm text-gray-600">Chargement des AOI...</div>
      <div v-else class="aoi-grid">
        <div v-for="aoi in satelliteStore.aois" :key="aoi" class="aoi-card">
          <span class="aoi-name">{{ aoi }}</span>
          <button @click="processAOI(aoi)" :disabled="processingAOI === aoi" class="process-btn">
            {{ processingAOI === aoi ? 'Traitement...' : 'Traiter' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Section Métriques -->
    <div v-if="satelliteStore.loading" class="loading-state">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="text-sm text-gray-600 mt-2">Chargement des données satellitaires...</p>
    </div>

    <div v-else-if="satelliteStore.error" class="error-state">
      <p class="text-sm text-red-600">{{ satelliteStore.error }}</p>
      <button @click="refreshData" class="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
        Réessayer
      </button>
    </div>

    <div v-else-if="satelliteStore.satelliteData.length === 0" class="empty-state">
      <p class="text-sm text-gray-600">Aucune donnée satellitaire disponible</p>
    </div>

    <div v-else class="metrics-grid">
      <div v-for="data in satelliteStore.satelliteData" :key="data.aoi" class="metric-card">
        <div class="card-header">
          <h4 class="font-medium">{{ data.aoi }}</h4>
          <span class="timestamp">{{ formatTimestamp(data.timestamp) }}</span>
        </div>

        <div class="metrics-list">
          <div class="metric-item">
            <span class="metric-label">NDWI Moyen:</span>
            <span class="metric-value">{{ data.metrics.ndwi_mean.toFixed(4) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Turbidité Moyenne:</span>
            <span class="metric-value">{{ data.metrics.turbidity_mean.toFixed(2) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Chlorophylle Moyenne:</span>
            <span class="metric-value">{{ data.metrics.chlorophyll_mean.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>

    <button @click="refreshData" class="refresh-btn" :disabled="satelliteStore.loading">
      {{ satelliteStore.loading ? 'Actualisation...' : 'Actualiser' }}
    </button>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useSatelliteStore } from '@/stores/satellite.store'

const satelliteStore = useSatelliteStore()
const processingAOI = ref(null)

const refreshData = async () => {
  await satelliteStore.fetchSatelliteData()
}

const processAOI = async (aoi) => {
  processingAOI.value = aoi
  try {
    await satelliteStore.processAOI(aoi)
    // Refresh data after processing
    await refreshData()
  } catch (err) {
    console.error('Erreur lors du traitement:', err)
  } finally {
    processingAOI.value = null
  }
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A'
  try {
    return new Date(timestamp).toLocaleString('fr-FR')
  } catch {
    return timestamp
  }
}

onMounted(async () => {
  await satelliteStore.fetchAOIs()
  await refreshData()
})
</script>

<style scoped>
.satellite-metrics {
  width: 100%;
  padding: 1rem;
}

.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.metrics-grid {
  display: grid;
  gap: 1rem;
  margin-bottom: 1rem;
}

.metric-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.timestamp {
  font-size: 0.75rem;
  color: #64748b;
}

.metrics-list {
  space-y: 0.5rem;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
}

.metric-label {
  font-size: 0.875rem;
  color: #475569;
}

.metric-value {
  font-weight: 600;
  color: #1e293b;
}

.refresh-btn {
  width: 100%;
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.refresh-btn:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}
</style>
