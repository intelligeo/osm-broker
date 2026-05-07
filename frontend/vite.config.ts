import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // @mapbox/mapbox-gl-draw importa internamente 'mapbox-gl';
      // questo alias lo reindirizza a maplibre-gl così i pulsanti draw funzionano.
      'mapbox-gl': 'maplibre-gl',
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
