<template>
  <div class="flex flex-col h-screen">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <h1 class="text-2xl font-bold text-blue-600">🌊 AquaWatch Quality Intelligence</h1>
          </div>
          <div class="flex items-center space-x-4">
            <button
              @click="refreshData"
              :disabled="dataStore.loading"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {{ dataStore.loading ? '⏳ Actualisation...' : '🔄 Actualiser' }}
            </button>
            <div class="flex items-center space-x-2">
              <div :class="['w-3 h-3 rounded-full animate-pulse', dataStore.error ? 'bg-red-500' : 'bg-green-500']"></div>
              <span class="text-sm text-gray-600">{{ dataStore.error || '✓ Connecté' }}</span>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Main Content -->
      <main class="flex-1 flex flex-col overflow-hidden">
        <!-- Map Container -->
        <div class="flex-1 p-4">
          <MapContainer />
        </div>
      </main>

      <!-- Right Sidebar -->
      <aside class="w-80 bg-white border-l border-gray-200 p-4 overflow-y-auto">
        <div class="space-y-4">
          <!-- Tabs -->
          <div class="flex border-b border-gray-200">
            <button
              @click="activeTab = 'anomalies'"
              :class="['flex-1 py-2 px-4 text-center font-medium text-sm border-b-2 transition-colors',
                activeTab === 'anomalies' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700']"
            >
              🔴 Anomalies
            </button>
            <button
              @click="activeTab = 'satellite'"
              :class="['flex-1 py-2 px-4 text-center font-medium text-sm border-b-2 transition-colors',
                activeTab === 'satellite' ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700']"
            >
              🛰️ Satellite
            </button>
          </div>

          <!-- Status -->
          <div class="bg-gray-50 p-4 rounded-lg">
            <h3 class="text-lg font-semibold mb-2">📊 Status</h3>
            <div v-if="activeTab === 'anomalies'">
              <div v-if="dataStore.loading" class="text-blue-600">
                ⏳ Chargement anomalies...
              </div>
              <div v-else-if="dataStore.error" class="text-red-600">
                ❌ {{ dataStore.error }}
              </div>
              <div v-else class="text-green-600">
                ✓ {{ dataStore.anomalies.length }} anomalies
              </div>
            </div>
            <div v-else>
              <div v-if="satelliteStore.loading" class="text-green-600">
                ⏳ Chargement satellite...
              </div>
              <div v-else-if="satelliteStore.error" class="text-red-600">
                ❌ {{ satelliteStore.error }}
              </div>
              <div v-else class="text-green-600">
                ✓ {{ satelliteStore.satelliteData.length }} métriques
              </div>
            </div>
          </div>

          <!-- Anomalies Tab -->
          <div v-if="activeTab === 'anomalies'">
            <h3 class="text-lg font-semibold mb-4">🔴 Anomalies Récentes</h3>
            <div class="space-y-2 max-h-96 overflow-y-auto">
              <div v-if="dataStore.anomalies.length === 0" class="text-center text-gray-400 py-8">
                Aucune anomalie
              </div>
              <div
                v-for="anomaly in dataStore.anomalies.slice(0, 15)"
                :key="anomaly.id"
                class="p-3 bg-gray-50 rounded-lg border-l-4"
                :class="getBorderColor(anomaly.type)"
              >
                <div class="flex items-center justify-between mb-1">
                  <span class="font-medium text-sm">{{ anomaly.sensor_id }}</span>
                  <span class="text-xs px-2 py-1 rounded font-bold" :class="getBadgeClass(anomaly.type)">
                    {{ anomaly.type }}
                  </span>
                </div>
                <p class="text-xs text-gray-600">{{ anomaly.message || anomaly.parameter }}</p>
                <p class="text-xs text-gray-400 mt-1">
                  {{ new Date(anomaly.timestamp).toLocaleString() }}
                </p>
              </div>
            </div>

            <!-- Generate Summary Section - Below Anomalies -->
            <div class="mt-6 pt-4 border-t border-gray-200">
              <h3 class="text-lg font-semibold mb-4">📊 Analyse des Anomalies</h3>
              <button
                @click="generateSummary"
                :disabled="summaryLoading"
                class="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {{ summaryLoading ? '⏳ Génération...' : '🤖 Générer Résumé' }}
              </button>
              <div v-if="summary" class="mt-4 p-4 rounded-lg border-2"
                   :class="getSummaryStyle(summary.overall_status)">
                <div class="flex items-center mb-3">
                  <span class="text-lg mr-2">{{ getStatusIcon(summary.overall_status) }}</span>
                  <h4 class="text-lg font-bold">Résumé des Anomalies</h4>
                </div>
                <div class="bg-white bg-opacity-50 p-3 rounded-md mb-3">
                  <p class="text-sm text-gray-800 leading-relaxed">{{ summary.summary_message }}</p>
                </div>
                <div class="space-y-2 text-xs">
                  <div class="grid grid-cols-2 gap-4">
                    <div class="flex items-center">
                      <span class="w-2 h-2 rounded-full mr-2" :class="getStatusDotColor(summary.overall_status)"></span>
                      <div>
                        <div class="text-gray-500 font-medium">Status</div>
                        <div class="font-semibold">{{ summary.overall_status }}</div>
                      </div>
                    </div>
                    <div class="flex items-center">
                      <span class="text-red-500 mr-2 text-sm">⚠️</span>
                      <div>
                        <div class="text-gray-500 font-medium">Anomalies</div>
                        <div class="font-semibold">{{ summary.anomalies_count }}</div>
                      </div>
                    </div>
                  </div>
                  <div class="border-t border-gray-300 pt-2">
                    <div class="text-gray-500 font-medium">Dernière mise à jour</div>
                    <div class="font-semibold">{{ formatTimestamp(summary.timestamp) }}</div>
                  </div>
                </div>
              </div>
              <div v-if="summaryError" class="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
                <p class="text-sm text-red-700">{{ summaryError }}</p>
              </div>
            </div>
          </div>

          <!-- Satellite Tab -->
          <div v-else>
            <h3 class="text-lg font-semibold mb-4">🛰️ Métriques Satellitaires</h3>

            <!-- AOI Section -->
            <div class="mb-4">
              <h4 class="text-sm font-medium mb-2">Zones d'Intérêt</h4>
              <div v-if="satelliteStore.aois.length === 0" class="text-xs text-gray-600">Chargement...</div>
              <div v-else class="space-y-1">
                <div v-for="aoi in satelliteStore.aois" :key="aoi" class="flex items-center justify-between">
                  <span class="text-xs">{{ aoi }}</span>
                  <button
                    @click="processAOI(aoi)"
                    :disabled="processingAOI === aoi"
                    class="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    {{ processingAOI === aoi ? '...' : '▶️' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Metrics Section -->
            <div class="space-y-2 max-h-64 overflow-y-auto">
              <div v-if="satelliteStore.satelliteData.length === 0" class="text-center text-gray-400 py-4">
                Aucune donnée satellite
              </div>
              <div
                v-for="data in satelliteStore.satelliteData.slice(0, 10)"
                :key="data.aoi"
                class="p-2 bg-green-50 rounded-lg border border-green-200"
              >
                <div class="flex items-center justify-between mb-1">
                  <span class="font-medium text-xs">{{ data.aoi }}</span>
                  <span class="text-xs text-gray-500">{{ formatTimestamp(data.timestamp) }}</span>
                </div>
                <div class="space-y-1 text-xs">
                  <div class="flex justify-between">
                    <span>NDWI:</span>
                    <span class="font-mono">{{ data.metrics.ndwi_mean.toFixed(3) }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span>Turbidité:</span>
                    <span class="font-mono">{{ data.metrics.turbidity_mean.toFixed(1) }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span>Chlorophylle:</span>
                    <span class="font-mono">{{ data.metrics.chlorophyll_mean.toFixed(1) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <button
              @click="refreshSatelliteData"
              :disabled="satelliteStore.loading"
              class="w-full mt-2 px-3 py-2 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
            >
              {{ satelliteStore.loading ? '⏳ Actualisation...' : '🔄 Actualiser' }}
            </button>
          </div>



        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useDataStore } from '@/stores/data.store';
import { useSatelliteStore } from '@/stores/satellite.store';
import MapContainer from '@/components/Map/MapContainer.vue';
import api from '@/services/api.js';

const dataStore = useDataStore();
const satelliteStore = useSatelliteStore();
const activeTab = ref('anomalies');
const processingAOI = ref(null);
const summary = ref(null);
const summaryLoading = ref(false);
const summaryError = ref('');

const getBadgeClass = (type) => {
  const typeLower = type?.toLowerCase() || '';
  if (typeLower.includes('spike')) return 'bg-red-100 text-red-800';
  if (typeLower.includes('drift')) return 'bg-yellow-100 text-yellow-800';
  if (typeLower.includes('dropout')) return 'bg-gray-100 text-gray-800';
  return 'bg-blue-100 text-blue-800';
};

const getBorderColor = (type) => {
  const typeLower = type?.toLowerCase() || '';
  if (typeLower.includes('spike')) return 'border-red-500';
  if (typeLower.includes('drift')) return 'border-yellow-500';
  if (typeLower.includes('dropout')) return 'border-gray-500';
  return 'border-blue-500';
};

const getSummaryStyle = (status) => {
  const statusLower = status?.toLowerCase() || '';
  if (statusLower.includes('critical') || statusLower.includes('severe')) {
    return 'bg-red-50 border-red-300';
  }
  if (statusLower.includes('moderate') || statusLower.includes('warning')) {
    return 'bg-yellow-50 border-yellow-300';
  }
  if (statusLower.includes('good') || statusLower.includes('normal')) {
    return 'bg-green-50 border-green-300';
  }
  return 'bg-blue-50 border-blue-300';
};

const getStatusIcon = (status) => {
  const statusLower = status?.toLowerCase() || '';
  if (statusLower.includes('critical') || statusLower.includes('severe')) {
    return '🚨';
  }
  if (statusLower.includes('moderate') || statusLower.includes('warning')) {
    return '⚠️';
  }
  if (statusLower.includes('good') || statusLower.includes('normal')) {
    return '✅';
  }
  return 'ℹ️';
};

const getStatusDotColor = (status) => {
  const statusLower = status?.toLowerCase() || '';
  if (statusLower.includes('critical') || statusLower.includes('severe')) {
    return 'bg-red-500';
  }
  if (statusLower.includes('moderate') || statusLower.includes('warning')) {
    return 'bg-yellow-500';
  }
  if (statusLower.includes('good') || statusLower.includes('normal')) {
    return 'bg-green-500';
  }
  return 'bg-blue-500';
};

const refreshData = async () => {
  console.log('🔄 Refreshing data...');
  await dataStore.refreshData();
};

const refreshSatelliteData = async () => {
  console.log('🛰️ Refreshing satellite data...');
  await satelliteStore.fetchSatelliteData();
};

const processAOI = async (aoi) => {
  processingAOI.value = aoi;
  try {
    await satelliteStore.processAOI(aoi);
    // Refresh data after processing
    await refreshSatelliteData();
  } catch (error) {
    console.error('Erreur lors du traitement de l\'AOI:', error);
  } finally {
    processingAOI.value = null;
  }
};

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  try {
    return new Date(timestamp).toLocaleString('fr-FR');
  } catch {
    return timestamp;
  }
};

const generateSummary = async () => {
  summaryLoading.value = true;
  summaryError.value = '';
  summary.value = null;
  try {
    const data = await api.getAnomalySummary();
    summary.value = data;
  } catch (error) {
    console.error('Erreur lors de la génération du résumé:', error);
    summaryError.value = 'Erreur lors de la génération du résumé. Veuillez réessayer.';
  } finally {
    summaryLoading.value = false;
  }
};

onMounted(async () => {
  console.log('📍 Home view mounted, fetching anomalies and satellite data...');
  await Promise.all([
    dataStore.fetchAnomalies(),
    satelliteStore.fetchAOIs(),
    satelliteStore.fetchSatelliteData()
  ]);
});
</script>