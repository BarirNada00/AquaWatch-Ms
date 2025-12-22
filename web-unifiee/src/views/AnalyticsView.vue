<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-6">📊 Tableau de Bord Analytique</h1>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div class="card">
        <h2 class="text-lg font-semibold mb-4">Évolution Temporelle</h2>
        <div class="h-64 bg-gray-100 rounded flex items-center justify-center text-gray-400">
          Graphique Chart.js à implémenter
        </div>
      </div>
      <div class="card">
        <h2 class="text-lg font-semibold mb-4">Comparaison Zones</h2>
        <div class="h-64 bg-gray-100 rounded flex items-center justify-center text-gray-400">
          Graphique Chart.js à implémenter
        </div>
      </div>
      <div class="card">
        <h2 class="text-lg font-semibold mb-4">Distribution Qualité</h2>
        <div class="h-64 bg-gray-100 rounded flex items-center justify-center text-gray-400">
          Graphique Chart.js à implémenter
        </div>
      </div>
    </div>

    <!-- AI Quality Intelligence Section -->
    <div class="mt-8">
      <h2 class="text-2xl font-bold mb-4">🤖 AquaWatch: Quality Intelligence</h2>
      <div class="card">
        <div v-if="dataStore.loading" class="flex items-center justify-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <span class="text-gray-600">Analysant les données...</span>
        </div>
        <div v-else-if="dataStore.aiSummary" class="space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <span class="text-lg font-semibold">Statut Global:</span>
              <span :class="getStatusBadgeClass(dataStore.aiSummary.overall_status)" class="px-3 py-1 rounded-full text-sm font-medium">
                {{ getStatusText(dataStore.aiSummary.overall_status) }}
              </span>
            </div>
            <div class="text-sm text-gray-500">
              Dernière analyse: {{ formatTimestamp(dataStore.aiSummary.timestamp) }}
            </div>
          </div>

          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="font-semibold mb-2">Résumé Intelligent:</h3>
            <p class="text-gray-700">{{ dataStore.aiSummary.summary_message }}</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-blue-50 rounded-lg p-4">
              <div class="text-2xl font-bold text-blue-600">{{ dataStore.aiSummary.anomalies_count || 0 }}</div>
              <div class="text-sm text-blue-800">Anomalies Détectées</div>
            </div>
            <div class="bg-green-50 rounded-lg p-4">
              <div class="text-2xl font-bold text-green-600">{{ dataStore.anomalies?.length || 0 }}</div>
              <div class="text-sm text-green-800">Capteurs Actifs</div>
            </div>
            <div class="bg-purple-50 rounded-lg p-4">
              <div class="text-2xl font-bold text-purple-600">{{ dataStore.alertes?.length || 0 }}</div>
              <div class="text-sm text-purple-800">Alertes Actives</div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-500">
          <p>Impossible de charger l'analyse intelligente.</p>
          <p class="text-sm mt-1">Vérifiez que le service backend est disponible.</p>
        </div>
      </div>
    </div>

    <!-- Historical Data Section -->
    <div class="mt-8">
      <h2 class="text-2xl font-bold mb-4">Historique des Anomalies</h2>
      <div class="card">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b">
                <th class="text-left p-3">Date</th>
                <th class="text-left p-3">Paramètre</th>
                <th class="text-left p-3">Anomalies</th>
                <th class="text-left p-3">Moyenne</th>
                <th class="text-left p-3">Min/Max</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="record in historicalData" :key="record.date" class="border-b hover:bg-gray-50">
                <td class="p-3">{{ formatDate(record.date) }}</td>
                <td class="p-3">{{ record.parameter }}</td>
                <td class="p-3">{{ record.anomaly_count }}</td>
                <td class="p-3">{{ record.statistics.avg_value ? record.statistics.avg_value.toFixed(2) : 'N/A' }}</td>
                <td class="p-3">
                  {{ record.statistics.min_value ? record.statistics.min_value.toFixed(2) : 'N/A' }} /
                  {{ record.statistics.max_value ? record.statistics.max_value.toFixed(2) : 'N/A' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api.js';
import { useDataStore } from '../stores/data.store.js';

const dataStore = useDataStore();
const historicalData = ref([]);

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  try {
    return new Date(dateStr).toLocaleDateString('fr-FR');
  } catch {
    return dateStr;
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

const getStatusBadgeClass = (status) => {
  switch (status?.toLowerCase()) {
    case 'critical':
    case 'red':
      return 'bg-red-100 text-red-800';
    case 'warning':
    case 'orange':
      return 'bg-orange-100 text-orange-800';
    case 'good':
    case 'green':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getStatusText = (status) => {
  switch (status?.toLowerCase()) {
    case 'critical':
    case 'red':
      return 'Critique';
    case 'warning':
    case 'orange':
      return 'Attention';
    case 'good':
    case 'green':
      return 'Bon';
    default:
      return status || 'Inconnu';
  }
};

const loadHistoricalData = async () => {
  try {
    const data = await api.getHistorical({ days: 30 });
    historicalData.value = data.data || [];
  } catch (error) {
    console.error('Error loading historical data:', error);
  }
};

const loadAISummary = async () => {
  await dataStore.fetchAISummary();
};

onMounted(async () => {
  await Promise.all([
    loadHistoricalData(),
    loadAISummary()
  ]);
});
</script>

<style scoped>
.card {
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>

