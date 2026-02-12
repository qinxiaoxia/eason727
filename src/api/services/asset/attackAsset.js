import request from '@/utils/request'

export default {
  // 获取攻击资产分配分页列表
  getPageList(params) {
    return request({
      url: '/refer/attackAsset/page',
      method: 'POST',
      data: params,
    })
  },

  // 新增攻击资产分配
  add(data) {
    return request({
      url: '/refer/attackAsset/add',
      method: 'POST',
      data: data,
    })
  },

  // 编辑攻击资产分配
  modify(data) {
    return request({
      url: '/refer/attackAsset/modify',
      method: 'POST',
      data: data,
    })
  },

  // 批量删除攻击资产分配
  batchRemove(ids) {
    return request({
      url: '/refer/attackAsset/removes',
      method: 'POST',
      data: ids,
    })
  },

  // 获取攻击资产分配详情
  getInfo(data) {
    return request({
      url: '/refer/attackAsset/info',
      method: 'POST',
      data: data,
    })
  },
}
