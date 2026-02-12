// src/stores/user.js
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    // 用户信息
    userInfo: null,
    // 用户权限列表
    permissions: [],
    // token
    token: localStorage.getItem('token') || '',
  }),

  getters: {
    // 检查是否有某个权限
    hasPermission: (state) => (permission) => {
      return state.permissions.includes(permission)
    },

    // 检查是否登录
    isLoggedIn: (state) => {
      return !!state.token
    },
  },

  actions: {
    // 设置用户信息
    setUserInfo(userInfo) {
      this.userInfo = userInfo
      this.permissions = userInfo?.permissions || []
    },

    // 设置token
    setToken(token) {
      this.token = token
      localStorage.setItem('token', token)
    },

    // 清除用户信息（退出登录）
    clearUserInfo() {
      this.userInfo = null
      this.permissions = []
      this.token = ''
      localStorage.removeItem('token')
    },
  },
})
