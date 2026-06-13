import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    // 生产环境移除 console/debugger
    minify: 'esbuild',
    target: 'es2020',
    // 分包策略: 将大型依赖拆分为独立 chunk
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-charts': ['recharts'],
          // echarts 已经是动态 import，不需要额外分包
        },
      },
    },
    // chunk 大小警告阈值
    chunkSizeWarningLimit: 600,
  },
})
