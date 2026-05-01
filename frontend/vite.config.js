import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Icons from 'unplugin-icons/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), Icons({
      compiler: 'vue3',
      autoInstall: true,
  })],
    server: {
        proxy: {
            '/api': { // префикс ваших эндпоинтов (зависит от того, как написано на бэке)
                target: 'http://localhost:8080',
                changeOrigin: true,
            }
        }
    }
})
