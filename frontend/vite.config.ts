import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
    proxy: {
      '/api':               { target: 'http://127.0.0.1:5000', changeOrigin: true, secure: false },
      '/static':            { target: 'http://127.0.0.1:5000', changeOrigin: true, secure: false },
      '/handle-interaction':{ target: 'http://127.0.0.1:5000', changeOrigin: true, secure: false },
      '/subscribe':         { target: 'http://127.0.0.1:5000', changeOrigin: true, secure: false },
      '/alerts/subscribe':  { target: 'http://127.0.0.1:5000', changeOrigin: true, secure: false },
      '/item-click':        { target: 'http://127.0.0.1:5000', changeOrigin: true, secure: false },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: false,
    // Let Vite 6 / Rollup handle code-splitting automatically.
    // Manual manualChunks caused a module-initialization-order bug:
    // packages in vendor-misc called React.createContext() before
    // vendor-react was initialized → TypeError: Cannot read properties
    // of undefined (reading 'createContext').
    // Vite's automatic splitting always guarantees correct load order.
    chunkSizeWarningLimit: 800,
  },
})
