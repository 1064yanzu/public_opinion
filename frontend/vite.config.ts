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
  esbuild: {
    // 生产环境移除 console / debugger，减少噪声和体积
    drop: ['console', 'debugger'],
  },
  build: {
    minify: 'esbuild',
    target: 'es2020',
    cssCodeSplit: true,
    // 分包策略：大型依赖单独拆 chunk，避免 main bundle 膨胀。
    // echarts 即使本身用了动态 import，显式 manualChunks 后路由懒加载 + 浏览器缓存复用更可控。
    rollupOptions: {
      output: {
        // 用函数形式精确分组：对 node_modules 内的依赖按 package 名分桶。
        // 这样即使是动态 import（如 echarts）也能稳定落到对应 vendor chunk，
        // 浏览器缓存复用更高，main bundle 才不会被 echarts 等大包反复污染。
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;
          // Cross-platform path separator
          const normalized = id.replace(/\\/g, '/');
          if (normalized.includes('node_modules/echarts')) return 'vendor-echarts';
          if (normalized.includes('node_modules/zrender')) return 'vendor-echarts';
          if (normalized.includes('node_modules/recharts')) return 'vendor-charts';
          if (/node_modules\/d3-/.test(normalized)) return 'vendor-charts';
          if (normalized.includes('node_modules/victory-vendor')) return 'vendor-charts';
          if (
            normalized.includes('node_modules/react-markdown') ||
            normalized.includes('node_modules/remark') ||
            normalized.includes('node_modules/rehype') ||
            normalized.includes('node_modules/micromark') ||
            normalized.includes('node_modules/mdast-') ||
            normalized.includes('node_modules/unified') ||
            normalized.includes('node_modules/hast-')
          ) {
            return 'vendor-markdown';
          }
          if (
            /node_modules\/react\//.test(normalized) ||
            /node_modules\/react-dom\//.test(normalized) ||
            normalized.includes('node_modules/react-router')
          ) {
            return 'vendor-react';
          }
          if (normalized.includes('node_modules/lucide-react')) return 'vendor-icons';
          if (normalized.includes('node_modules/axios')) return 'vendor-net';
          return 'vendor';
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
})
