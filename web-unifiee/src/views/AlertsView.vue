<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-6">⚠️ Centre d'Alertes</h1>
    <div class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b">
              <th class="text-left p-3">Capteur</th>
              <th class="text-left p-3">Type</th>
              <th class="text-left p-3">Message</th>
              <th class="text-left p-3">Timestamp</th>
              <th class="text-left p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="alerte in dataStore.alertes" :key="alerte.id" class="border-b hover:bg-gray-50">
              <td class="p-3">{{ alerte.sensor_id }}</td>
              <td class="p-3">
                <span class="status-badge status-red">{{ alerte.type }}</span>
              </td>
              <td class="p-3">{{ alerte.message }}</td>
              <td class="p-3 text-sm text-gray-500">{{ new Date(alerte.timestamp).toLocaleString() }}</td>
              <td class="p-3">
                <button class="btn-secondary text-sm">Acquitter</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useDataStore } from '../stores/data.store';

const dataStore = useDataStore();
</script>

