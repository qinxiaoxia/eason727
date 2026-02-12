import request from '@/utils/request'

export default {
  // 获取分派动态列分页列表
  getPageList(params) {
    return request({
      url: '/refer/assignColumns/page',
      method: 'POST',
      data: params,
    })
  },

  // 新增分派动态列
  add(data) {
    return request({
      url: '/refer/assignColumns/add',
      method: 'POST',
      data: data,
    })
  },

  // 编辑分派动态列
  modify(data) {
    return request({
      url: '/refer/assignColumns/modify',
      method: 'POST',
      data: data,
    })
  },

  // 批量删除分派动态列
  batchRemove(ids) {
    return request({
      url: '/refer/assignColumns/removes',
      method: 'POST',
      data: ids,
    })
  },

  // 获取分派动态列详情
  getInfo(data) {
    return request({
      url: '/refer/assignColumns/info',
      method: 'POST',
      data: data,
    })
  },
}
