import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react({
      // 启用 React 插件
      include: "**/*.{jsx,tsx}",
      exclude: /node_modules/
    })
  ],
  
  // 服务器配置
  server: {
    port: 3000,
    hmr: {
      overlay: false
    },
    watch: {
      usePolling: true
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/images': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  
  // 优化依赖处理
  optimizeDeps: {
    include: ['react', 'react-dom', 'antd', '@ant-design/icons']
  },
  
  // 禁用 CSS 模块和 HMR
  css: {
    devSourcemap: false,
    modules: false
  },
  
  // 构建配置
  build: {
    target: 'esnext',
    minify: 'esbuild',
    rollupOptions: {
      external: ['@vite/client']
    }
  },
  
  // 定义全局变量
  define: {
    global: 'globalThis',
    'import.meta.hot': 'undefined'
  }
})