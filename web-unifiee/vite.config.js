import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true
      },
      // Proxy GeoServer requests to avoid CORS in development
      // Requests to /geoserver/* will be forwarded to http://localhost:8080/geoserver/*
      '/geoserver': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false,
        // leave path intact so /geoserver/ows -> http://localhost:8080/geoserver/ows
      }
    }
  }
});
