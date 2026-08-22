import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

  // 提取 origin 作为代理目标（如 http://localhost:8000）
  const match = apiBaseUrl.match(/^(https?:\/\/[^/]+)/)
  const proxyTarget = match ? match[1] : 'http://localhost:8000'

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      port: Number(env.FRONTEND_PORT) || 5173,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
