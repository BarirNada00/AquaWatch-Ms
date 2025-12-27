<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-6">🛰️ Vue Satellite</h1>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <h2 class="text-lg font-semibold mb-4">Images Satellite</h2>
        <div class="h-96 bg-gray-100 rounded flex items-center justify-center text-gray-400">
          Visualiseur d'images satellite à implémenter
        </div>
      </div>
      <div class="card">
        <SatelliteMetrics />
      </div>
    </div>
  </div>
</template>

<script setup>
import SatelliteMetrics from '../components/Satellite/SatelliteMetrics.vue';
</script>

<style scoped>
.card {
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>

