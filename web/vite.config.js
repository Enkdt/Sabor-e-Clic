import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react()],
  server: {
    // Bind explícito em IPv4. Sob `vercel dev` (arquitetura de services), o
    // gateway faz proxy para este dev server via 127.0.0.1. O padrão do Vite
    // ("localhost") resolve para ::1 (IPv6) no Windows e o gateway não alcança
    // esse endereço, resultando em falhas de proxy. Fixar 127.0.0.1 mantém
    // gateway e Vite no mesmo stack IP.
    host: '127.0.0.1',
    // Proxy /api para o Flask em dev STANDALONE (ex.: `npm run dev` isolado e os
    // testes E2E do Playwright, que sobem Vite + Flask diretamente, sem o
    // gateway da Vercel). Sob `vercel dev`, quem roteia /api é o gateway via os
    // rewrites do vercel.json; este proxy não interfere nesse fluxo.
    proxy: {
      '/api': 'http://127.0.0.1:5000',
    },
  },
})
