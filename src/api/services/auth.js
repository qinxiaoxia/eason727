// src/api/user.js
import request from '@/utils/request'

export default {
  // 用户登录
  login(data) {
    console.log('🔐 登录请求详情:', {
      url: '/auth/login',
      method: 'POST',
      data: { ...data, password: '***' }, // 隐藏密码
    })

    return request({
      url: '/auth/login',
      method: 'POST',
      data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },

  // 获取验证码
  getCaptcha() {
    return request({
      url: '/auth/getCode',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },

  // 用户登出
  logout(data) {
    return request({
      url: '/auth/logout',
      method: 'POST',
      data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },

  // 获取用户信息
  getUserInfo(data) {
    return request({
      url: '/sysUser/userInfo',
      method: 'POST',
      data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
}
