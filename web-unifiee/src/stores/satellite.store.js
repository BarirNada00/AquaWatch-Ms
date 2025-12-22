import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../services/api.js';

export const useSatelliteStore = defineStore('satellite', () => {
  const satelliteData = ref([]);
  const aois = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const fetchAOIs = async () => {
    try {
      aois.value = await api.getSatelliteAOIs();
    } catch (err) {
      console.error('Erreur lors du chargement des AOI:', err);
      aois.value = [];
    }
  };

  const fetchSatelliteData = async () => {
    loading.value = true;
    error.value = null;
    try {
      satelliteData.value = await api.getSatelliteMetrics();
    } catch (err) {
      error.value = 'Erreur lors du chargement des données satellitaires';
      console.error('Satellite data error:', err);
      satelliteData.value = [];
    } finally {
      loading.value = false;
    }
  };

  const processAOI = async (aoi) => {
    try {
      await api.processSatelliteAOI(aoi);
    } catch (err) {
      console.error('Erreur lors du traitement de l\'AOI:', err);
      throw err;
    }
  };

  return {
    satelliteData,
    aois,
    loading,
    error,
    fetchAOIs,
    fetchSatelliteData,
    processAOI
  };
});
