<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useDataStore } from './stores/data.store';

const dataStore = useDataStore();

onMounted(async () => {
  console.log('🚀 App mounted - Loading initial data...');
  await dataStore.fetchAnomalies();
});
</script>

<style>
#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>