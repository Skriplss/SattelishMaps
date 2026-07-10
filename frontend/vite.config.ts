import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        // maplibre and chart.js dominate bundle size — split them so the
        // app shell loads and caches independently of the heavy libs
        manualChunks: {
          maplibre: ['maplibre-gl'],
          charts: ['chart.js', 'react-chartjs-2'],
        },
      },
    },
  },
})
