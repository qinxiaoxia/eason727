// @/api/services/system/user.js
import request from '@/utils/request'

export default {
  // 获取用户分页列表
  getPageList(params) {
    return request({
      url: '/sysUser/page',
      method: 'POST',
      data: params,
    })
  },

  // 新增用户
  addUser(data) {
    return request({
      url: '/sysUser/add',
      method: 'POST',
      data,
    })
  },

  // 编辑用户信息
  editUserInfo(data) {
    return request({
      url: '/sysUser/editUserInfo',
      method: 'POST',
      data,
    })
  },

  // 获取用户详情
  getUserInfo(data) {
    return request({
      url: '/sysUser/userInfo',
      method: 'POST',
      data,
    })
  },

  // 批量删除用户
  batchRemoveUsers(ids) {
    return request({
      url: '/sysUser/removes',
      method: 'POST',
      data: ids,
    })
  },

  // 重置密码
  resetPassword(data) {
    return request({
      url: '/sysUser/resetPass',
      method: 'POST',
      data,
    })
  },

  // 修改密码
  modifyPassword(data) {
    return request({
      url: '/sysUser/modifyPass',
      method: 'POST',
      data,
    })
  },
}
