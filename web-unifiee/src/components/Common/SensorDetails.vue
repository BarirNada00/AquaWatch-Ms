<template>
  <div class="space-y-4">
    <div class="border-b pb-4">
      <h2 class="text-xl font-bold">{{ sensor.sensor_id }}</h2>
      <p class="text-sm text-gray-500">Dernière mise à jour: il y a 2s</p>
    </div>

    <div class="space-y-3">
      <div>
        <div class="text-sm text-gray-500 mb-1">pH</div>
        <div class="flex items-center justify-between">
          <span class="text-2xl font-bold">{{ sensor.ph }}</span>
          <span class="status-badge status-green">✅ Normal</span>
        </div>
      </div>

      <div>
        <div class="text-sm text-gray-500 mb-1">Température</div>
        <div class="flex items-center justify-between">
          <span class="text-2xl font-bold">{{ sensor.temperature }}°C</span>
          <span class="status-badge status-green">✅ Normal</span>
        </div>
      </div>

      <div>
        <div class="text-sm text-gray-500 mb-1">Turbidité</div>
        <div class="flex items-center justify-between">
          <span class="text-2xl font-bold">{{ sensor.turbidity }} NTU</span>
          <span class="status-badge status-green">✅ Normal</span>
        </div>
      </div>
    </div>

    <div class="pt-4 border-t">
      <h3 class="text-sm font-semibold mb-2">Historique</h3>
      <div class="h-32 bg-gray-100 rounded flex items-center justify-center text-gray-400 text-sm">
        Graphique à venir
      </div>
    </div>

    <div class="pt-4 border-t">
      <h3 class="text-sm font-semibold mb-2">Alertes</h3>
      <div class="text-sm text-gray-500">Aucune alerte active</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sensor: {
    type: Object,
    required: true
  }
});
</script>

