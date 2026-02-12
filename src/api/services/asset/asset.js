import request from '@/utils/request'

export default {
  // 获取资产分页列表
  getPageList(params) {
    return request({
      url: '/mgr/asset/page',
      method: 'POST',
      data: params,
    })
  },

  // 新增资产
  add(data) {
    return request({
      url: '/mgr/asset/add',
      method: 'POST',
      data: data,
    })
  },

  // 编辑资产
  modify(data) {
    return request({
      url: '/mgr/asset/modify',
      method: 'POST',
      data: data,
    })
  },

  // 批量删除资产
  batchRemove(ids) {
    return request({
      url: '/mgr/asset/removes',
      method: 'POST',
      data: ids,
    })
  },

  // 获取资产详情
  getInfo(data) {
    return request({
      url: '/mgr/asset/info',
      method: 'POST',
      data: {
        param: data,
      },
    })
  },

  // 导入资产
  import(data) {
    return request({
      url: '/mgr/asset/import',
      method: 'POST',
      data: data,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}
