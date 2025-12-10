import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite config aligned with Telegram Mini App quickstart
export default defineConfig({
  plugins: [react()],
  base: './', // ensure assets resolve in Telegram WebView
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: true, // allow external access (ngrok)
    port: 3000,
    allowedHosts: ['marquita-hemoid-continuedly.ngrok-free.dev'],
    proxy: {
      // Proxy API calls to local backend so ngrok only needs the frontend tunnel.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
