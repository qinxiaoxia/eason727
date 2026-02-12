import request from '@/utils/request'

export default {
  // 获取队伍分页列表
  getPageList(params) {
    return request({
      url: '/mgr/team/page',
      method: 'POST',
      data: params,
    })
  },

  // 新增队伍
  add(data) {
    return request({
      url: '/mgr/team/add',
      method: 'POST',
      data: data,
    })
  },

  // 编辑队伍
  modify(data) {
    return request({
      url: '/mgr/team/modify',
      method: 'POST',
      data: data,
    })
  },

  // 批量删除队伍
  batchRemove(ids) {
    return request({
      url: '/mgr/team/removes',
      method: 'POST',
      data: ids,
    })
  },

  // 获取队伍详情
  getInfo(data) {
    return request({
      url: '/mgr/team/info',
      method: 'POST',
      data: {
        param: data,
      },
    })
  },

  // 导入队伍
  import(data) {
    return request({
      url: '/mgr/team/import',
      method: 'POST',
      data: data,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}
