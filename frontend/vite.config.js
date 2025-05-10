import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // server: {
  //   proxy: {
  //     '/documents': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //       secure: false,
  //     },
  //     '/query': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //       secure: false,
  //     },
  //   },
  // },
})
