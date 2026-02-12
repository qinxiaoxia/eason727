import request from '@/utils/request'

const BASE_URL = '/mgr/userProxy'

export default {
  // 获取用户代理分页列表 - 使用data传递参数
  getPageList(data) {
    return request({
      url: `${BASE_URL}/page`,
      method: 'POST',
      data, // 使用data而不是params
    })
  },

  // 新增用户代理
  add(data) {
    return request({
      url: `${BASE_URL}/add`,
      method: 'POST',
      data: data,
    })
  },

  // 修改用户代理
  modify(data) {
    return request({
      url: `${BASE_URL}/modify`,
      method: 'POST',
      data,
    })
  },

  // 批量删除用户代理
  batchRemove(ids) {
    return request({
      url: `${BASE_URL}/removes`,
      method: 'POST',
      data: ids,
    })
  },

  // 获取用户代理详情
  getInfo(data) {
    return request({
      url: `${BASE_URL}/info`,
      method: 'POST',
      data,
    })
  },

  // 导入用户代理
  import(data) {
    return request({
      url: `${BASE_URL}/import`,
      method: 'POST',
      data: data,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // 启动代理
  start(data) {
    return request({
      url: `${BASE_URL}/start`,
      method: 'POST',
      data,
    })
  },

  // 停止代理
  stop(data) {
    return request({
      url: `${BASE_URL}/stop`,
      method: 'POST',
      data,
    })
  },
}
