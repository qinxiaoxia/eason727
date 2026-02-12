import request from '@/utils/request'

export default {
  // 获取代理池分页列表
  getPageList(params) {
    return request({
      url: '/mgr/proxyPool/page',
      method: 'POST',
      data: params,
    })
  },

  // 新增代理池
  add(data) {
    return request({
      url: '/mgr/proxyPool/add',
      method: 'POST',
      data: data,
    })
  },

  // 编辑代理池
  modify(data) {
    return request({
      url: '/mgr/proxyPool/modify',
      method: 'POST',
      data: data,
    })
  },

  // 批量删除代理池
  batchRemove(ids) {
    return request({
      url: '/mgr/proxyPool/removes',
      method: 'POST',
      data: ids,
    })
  },

  // 获取代理池详情
  getInfo(data) {
    return request({
      url: '/mgr/proxyPool/info',
      method: 'POST',
      data: data,
    })
  },

  // 导入代理池
  import(data) {
    return request({
      url: '/mgr/proxyPool/import',
      method: 'POST',
      data: data,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}
