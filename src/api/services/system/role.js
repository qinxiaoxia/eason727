// @/api/services/system/role.js
import request from '@/utils/request'

export default {
  // 获取角色分页列表
  getPageList(params) {
    return request({
      url: '/sysRole/page',
      method: 'POST',
      data: params,
    })
  },

  // 新增角色
  addRole(data) {
    return request({
      url: '/sysRole/add',
      method: 'POST',
      data,
    })
  },

  // 编辑角色
  editRole(data) {
    return request({
      url: '/sysRole/edit',
      method: 'POST',
      data,
    })
  },

  // 删除角色
  removeRole(id) {
    return request({
      url: `/sysRole/remove/${id}`,
      method: 'POST',
    })
  },

  // 批量删除角色
  batchRemoveRoles(ids) {
    return request({
      url: '/sysRole/removes',
      method: 'POST',
      data: ids,
    })
  },

  // 分配用户
  assignUser(data) {
    return request({
      url: '/sysRole/assignUser',
      method: 'POST',
      data,
    })
  },

  // 获取角色用户ID列表
  getRoleUserIds(data) {
    return request({
      url: '/sysRole/getRoleUserIds',
      method: 'POST',
      data,
    })
  },
}
