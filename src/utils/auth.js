// utils/auth.js - 修改用户信息获取
import { resetRouter } from '@/utils/routerUtils'
import router from '@/router'

/**
 * 退出登录
 */
export function logout() {
  console.log('执行退出登录...')

  // 清除本地存储
  localStorage.removeItem('Authorization')
  localStorage.removeItem('user_info')
  localStorage.removeItem('user_permits') // 修改：删除权限信息
  localStorage.removeItem('dynamic_route_added')

  // 重置路由
  resetRouter()

  // 跳转到登录页
  router.push('/login')
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser() {
  const userInfoStr = localStorage.getItem('user_info')
  if (userInfoStr && userInfoStr !== 'undefined' && userInfoStr !== 'null') {
    try {
      return JSON.parse(userInfoStr)
    } catch (error) {
      console.error('解析用户信息失败:', error)
      localStorage.removeItem('user_info') // 移除损坏的数据
      return null
    }
  }
  return null
}

/**
 * 检查是否已登录
 */
export function isLoggedIn() {
  return !!localStorage.getItem('Authorization')
}

/**
 * 获取用户权限
 */
export function getUserPermits() {
  const permitsStr = localStorage.getItem('user_permits')
  if (permitsStr) {
    try {
      const permits = JSON.parse(permitsStr)
      // 确保返回的是数组
      return Array.isArray(permits) ? permits : [permits]
    } catch (error) {
      console.error('解析用户权限失败:', error)
      localStorage.removeItem('user_permits') // 移除损坏的数据
      return ['user'] // 默认权限数组
    }
  }
  return ['user'] // 默认权限数组
}
// src/utils/auth.js
/**
 * 用户认证相关工具函数
 */

// Token 相关操作
export const authUtils = {
  // 检查是否已登录
  isLoggedIn() {
    // 使用 Authorization 作为 token 键名
    const token = localStorage.getItem('Authorization')
    const userPermits = this.getUserPermits()

    console.log('🔍 authUtils.isLoggedIn 检查:', {
      hasToken: !!token,
      tokenLength: token ? token.length : 0,
      hasUserPermits: userPermits.length > 0,
      tokenKey: 'Authorization',
    })

    return !!(token && userPermits && userPermits.length > 0)
  },

  // 获取 token
  getToken() {
    return localStorage.getItem('Authorization')
  },

  // 清除用户数据
  clearUserData() {
    const items = [
      'Authorization', // 主要使用这个
      'auth_token', // 同时清除可能的其他键名
      'user_info',
      'user_permits',
      'dynamic_route_added',
      'user_top_menus',
    ]

    items.forEach((item) => {
      if (localStorage.getItem(item)) {
        localStorage.removeItem(item)
        console.log(`✅ 已清除: ${item}`)
      }
    })

    console.log('✅ 用户数据已清除')
  },

  // 获取用户权限
  getUserPermits() {
    const permitsStr = localStorage.getItem('user_permits')
    if (permitsStr) {
      try {
        const permits = JSON.parse(permitsStr)
        return Array.isArray(permits) ? permits : [permits]
      } catch (error) {
        console.error('解析用户权限失败:', error)
        return []
      }
    }
    return []
  },

  // 获取用户信息
  getUserInfo() {
    const userInfoStr = localStorage.getItem('user_info')
    if (userInfoStr) {
      try {
        return JSON.parse(userInfoStr)
      } catch (error) {
        console.error('解析用户信息失败:', error)
        return null
      }
    }
    return null
  },
}
