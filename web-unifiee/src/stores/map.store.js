import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useMapStore = defineStore('map', () => {
  const center = ref([33.5731, -7.5898]); // Casablanca par défaut
  const zoom = ref(10);
  const selectedSensor = ref(null);
  const activeLayers = ref({
    capteurs: true,
    zones: true,
    anomalies: true,
    satellite: false,
    predictions: false
  });

  const capteursData = ref(null);
  const zonesData = ref(null);
  const anomaliesData = ref(null);
  const satelliteData = ref(null);
  const predictionsData = ref(null);

  const setCenter = (lat, lng) => {
    center.value = [lat, lng];
  };

  const setZoom = (newZoom) => {
    zoom.value = newZoom;
  };

  const selectSensor = (sensor) => {
    selectedSensor.value = sensor;
  };

  const toggleLayer = (layerName) => {
    activeLayers.value[layerName] = !activeLayers.value[layerName];
  };

  const setCapteursData = (data) => {
    capteursData.value = data;
  };

  const setZonesData = (data) => {
    zonesData.value = data;
  };

  const setAnomaliesData = (data) => {
    anomaliesData.value = data;
  };

  const setSatelliteData = (data) => {
    satelliteData.value = data;
  };

  const setPredictionsData = (data) => {
    predictionsData.value = data;
  };

  return {
    center,
    zoom,
    selectedSensor,
    activeLayers,
    capteursData,
    zonesData,
    anomaliesData,
    satelliteData,
    predictionsData,
    setCenter,
    setZoom,
    selectSensor,
    toggleLayer,
    setCapteursData,
    setZonesData,
    setAnomaliesData,
    setSatelliteData,
    setPredictionsData
  };
});

