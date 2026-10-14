import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
//Esse proxy é útil só pra teste em local, a gente vai trocar isso aq dps qndo for lançar o coisinho
export default defineConfig({
  plugins: [
    tailwindcss(),
    react()],
  server:{
    proxy:{
      '/api': 'http://127.0.0.1:5000',
    },
  },
})