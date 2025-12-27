<template>
  <div class="anomaly-chart-container">
    <h3 class="text-lg font-semibold mb-4">Distribution des Anomalies</h3>
    <div class="chart-wrapper">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDataStore } from '@/stores/data.store'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const dataStore = useDataStore()

const countAnomaliesByType = () => {
  const counts = {
    SPIKE: 0,
    DRIFT: 0,
    DROPOUT: 0
  }

  dataStore.anomalies.forEach(anomaly => {
    const type = anomaly.type?.toUpperCase()
    if (counts.hasOwnProperty(type)) {
      counts[type]++
    }
  })

  return counts
}

const chartData = computed(() => {
  const counts = countAnomaliesByType()
  return {
    labels: ['SPIKE', 'DRIFT', 'DROPOUT'],
    datasets: [{
      label: 'Nombre d\'anomalies',
      data: [counts.SPIKE, counts.DRIFT, counts.DROPOUT],
      backgroundColor: [
        'rgba(239, 68, 68, 0.8)', // Red for SPIKE
        'rgba(245, 158, 11, 0.8)', // Yellow for DRIFT
        'rgba(156, 163, 175, 0.8)' // Gray for DROPOUT
      ],
      borderColor: [
        'rgb(239, 68, 68)',
        'rgb(245, 158, 11)',
        'rgb(156, 163, 175)'
      ],
      borderWidth: 1
    }]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    },
    title: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        stepSize: 1
      }
    }
  }
}
</script>

<style scoped>
.anomaly-chart-container {
  width: 100%;
  height: 100%;
}

.chart-wrapper {
  position: relative;
  height: 300px;
  width: 100%;
}
</style>
