import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// `npm run dev` serves the page with hot reload and forwards the API to
// `python -m brain serve` (run it in another terminal).
const api = 'http://127.0.0.1:8765'

export default defineConfig({
  plugins: [svelte()],
  server: { proxy: { '/api': api, '/files': api } },
})
