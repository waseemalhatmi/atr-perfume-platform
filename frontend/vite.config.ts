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

    // ── Manual chunk splitting ────────────────────────────────────────────────
    // Goal: keep the initial bundle small; lazy-load heavy/infrequent modules.
    //
    //  vendor-react   → React runtime (cached for a long time across deploys)
    //  vendor-ui      → Animation / icon libraries (large, rarely changes)
    //  vendor-data    → Data fetching / state (react-query, zustand, axios)
    //  admin          → Admin panel (NEVER loaded for regular users)
    //  pages-*        → Each page group in its own chunk (code-split by route)
    //
    // Regular users only download:
    //   vendor-react + vendor-data + the current page chunk  (~150-200 KB gzipped)
    // Admin bundle (~300 KB) loads only when /admin route is hit.
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          // ── Admin: completely isolated chunk ─────────────────────────────
          if (id.includes('/admin/')) {
            return 'admin'
          }

          // ── Heavy UI libraries ───────────────────────────────────────────
          if (
            id.includes('framer-motion') ||
            id.includes('lucide-react')  ||
            id.includes('react-hot-toast')
          ) {
            return 'vendor-ui'
          }

          // ── Data / state libraries ───────────────────────────────────────
          if (
            id.includes('@tanstack/react-query') ||
            id.includes('zustand')               ||
            id.includes('axios')
          ) {
            return 'vendor-data'
          }

          // ── React core (most aggressively cached) ─────────────────────────
          if (
            id.includes('node_modules/react/') ||
            id.includes('node_modules/react-dom/') ||
            id.includes('react-router-dom')
          ) {
            return 'vendor-react'
          }

          // All other node_modules in a general vendor chunk
          if (id.includes('node_modules')) {
            return 'vendor-misc'
          }
        },
      },
    },
  },
})
