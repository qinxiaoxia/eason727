// utils/request.js
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建axios实例
const service = axios.create({
  baseURL: '/api', // 使用空字符串，让Vite代理处理
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 如果是开发环境，打印请求信息
    if (import.meta.env.DEV) {
      console.log('🔐 请求配置:', {
        url: config.url,
        method: config.method,
        data: config.data,
      })
    }
    if (config.data instanceof FormData) {
      // 对于 FormData，让浏览器自动设置 Content-Type 和 boundary
      // 删除手动设置的 Content-Type，让浏览器自动处理
      delete config.headers['Content-Type']
    } else if (config.data && typeof config.data === 'object') {
      config.headers['Content-Type'] = 'application/json'
    } else {
      config.headers['Content-Type'] = 'application/x-www-form-urlencoded'
    }
    // 获取 token
    const token = localStorage.getItem('Authorization')

    // 不需要 token 的接口白名单
    const noAuthUrls = [
      '/auth/login',
      '/auth/getCode',
      '/auth/captcha',
      '/auth/refreshToken', // 如果有刷新token的接口
    ]

    // 检查当前请求是否需要认证
    const needsAuth = !noAuthUrls.some((url) => config.url.includes(url))

    if (needsAuth && token) {
      // 根据后端要求设置 Authorization 头
      // 方案1: 直接使用 token
      //config.headers.Authorization = token

      // 方案2: 使用 Bearer token (如果后端需要)
      config.headers.Authorization = `${token}`

      // 方案3: 使用自定义前缀 (如果后端需要)
      // config.headers.Authorization = `Token ${token}`

      console.log('✅ 已添加 Authorization 头:', config.headers.Authorization)
    } else if (needsAuth && !token) {
      console.warn('⚠️ 需要认证的接口但未找到 token')
      // 如果没有token且需要认证，跳转到登录页
      ElMessage.error('登录已过期，请重新登录')
      localStorage.clear()
      router.push('/login')
      return Promise.reject(new Error('未登录'))
    } else {
      console.log('🔐 接口无需认证或已跳过认证')
    }

    return config
  },
  (error) => {
    console.error('❌ 请求错误:', error)
    return Promise.reject(error)
  },
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    // 如果是开发环境，打印响应信息
    if (import.meta.env.DEV) {
      console.log('✅ 响应数据:', {
        url: response.config.url,
        status: response.status,
        data: response.data,
      })
    }

    // 如果响应是二进制数据（如图片），直接返回原始响应
    if (
      response.config.responseType === 'blob' ||
      response.headers['content-type']?.includes('image')
    ) {
      return response
    }

    return response.data
  },
  (error) => {
    console.error('❌ 响应错误:', error)

    if (error.code === 'ERR_NETWORK') {
      ElMessage.error('网络连接失败,请检查网络连接或后端服务是否启动')
      return Promise.reject(error)
    }

    if (error.response) {
      const { status, data } = error.response
      console.error(`❌ HTTP ${status} 错误:`, data)

      switch (status) {
        case 401:
          // 关键修复：401 错误时检查是否是路由问题
          if (router.currentRoute.value.path !== '/login') {
            ElMessage.error('登录已过期或token无效，请重新登录')
            // 清除本地存储
            const items = ['Authorization', 'user_info', 'user_permits', 'dynamic_route_added']
            items.forEach((item) => localStorage.removeItem(item))
            // 跳转到登录页
            router.push('/login')
          }
          break
        case 403:
          ElMessage.error('权限不足，无法访问该资产')
          break
        case 404:
          // 如果是 API 404，不显示错误消息
          if (!error.config.url.includes('/api/')) {
            ElMessage.error('接口不存在')
          }
          break
        case 500:
          ElMessage.error(data?.message || '服务器内部错误')
          break
        case 502:
          ElMessage.error('网关错误,后端服务可能未启动')
          break
        case 503:
          ElMessage.error('服务不可用，请稍后重试')
          break
        default:
          ElMessage.error(data?.message || `网络错误(${status})`)
      }
    }

    return Promise.reject(error)
  },
)

// 添加 token 相关的工具函数
export const tokenUtils = {
  // 获取当前 token
  getToken() {
    return localStorage.getItem('Authorization')
  },

  // 设置 token
  setToken(token) {
    localStorage.setItem('Authorization', token)
    console.log('✅ Token 已保存')
  },

  // 清除 token
  clearToken() {
    localStorage.removeItem('Authorization')
    console.log('✅ Token 已清除')
  },

  // 检查 token 是否存在
  hasToken() {
    return !!localStorage.getItem('Authorization')
  },

  // 验证 token 格式（简单验证）
  validateToken(token) {
    if (!token) return false
    // 简单的 token 验证，可以根据实际格式调整
    return token.length > 10 // 假设 token 长度大于10
  },
}

export default service
