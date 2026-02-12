// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    open: true,
    host: '0.0.0.0', // 确保监听所有地址
    cors: true,
    // 添加静态文件服务配置
    fs: {
      allow: ['..'], // 允许访问上级目录
    },
    proxy: {
      // 通用的智能代理配置
      '/api': {
        target: 'http://172.21.9.59:8082',
        changeOrigin: true,
        rewrite: (path) => {
          console.log('path before:', path)
          let p = path.replace(/^\/api/, '')

          console.log('path after:', p)
          return p
        }, // 可选的路径重写
        // 添加请求头信息
        headers: {
          Connection: 'keep-alive',
        },
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
  },
  publicDir: 'public',
  base: './',
})
