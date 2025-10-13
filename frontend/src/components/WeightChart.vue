<template>
  <div>
    <canvas ref="canvas"></canvas>
  </div>
</template>

<script>
import { onMounted, ref, watch } from 'vue'
import { Chart, LineController, LineElement, PointElement, LinearScale, TimeScale, Title, Tooltip, Legend, CategoryScale } from 'chart.js'
import 'chartjs-adapter-date-fns'

Chart.register(LineController, LineElement, PointElement, LinearScale, TimeScale, Title, Tooltip, Legend, CategoryScale)

export default {
  name: 'WeightChart',
  props: {
    measurements: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    const canvas = ref(null)
    let chart = null

    const buildChart = () => {
      if (!canvas.value) return
      const ctx = canvas.value.getContext('2d')
      const labels = props.measurements.map(m => new Date(m.creado_en))
      const data = props.measurements.map(m => m.peso)

      if (chart) chart.destroy()

      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Peso (kg)',
            data,
            borderColor: '#34D399',
            backgroundColor: 'rgba(52,211,153,0.2)',
            tension: 0.2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              type: 'time',
              time: {
                unit: 'day'
              }
            }
          }
        }
      })
    }

    onMounted(buildChart)
    watch(() => props.measurements, buildChart)

    return { canvas }
  }
}
</script>

<style>
canvas { width: 100%; height: 300px; }
</style>
