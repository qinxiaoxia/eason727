import request from '@/utils/request'

const BASE_URL = '/mgr/project'

export const projectApi = {
  // 项目新增
  add(data) {
    return request({
      url: `${BASE_URL}/add`,
      method: 'post',
      data, // 直接发送数据，不包装
    })
  },

  // 项目修改
  modify(data) {
    return request({
      url: `${BASE_URL}/modify`,
      method: 'post',
      data, // 直接发送数据，不包装
    })
  },

  // 项目分页列表
  getPageList(params) {
    return request({
      url: `${BASE_URL}/page`,
      method: 'post',
      data: params, // 直接发送参数
    })
  },

  // 项目详情
  getInfo(data) {
    return request({
      url: `${BASE_URL}/info`,
      method: 'post',
      data, // 直接发送数据
    })
  },

  // 批量删除
  batchRemove(ids) {
    return request({
      url: `${BASE_URL}/removes`,
      method: 'post',
      data: ids, // 直接发送ID数组
    })
  },

  // 导入项目
  async importProject(file, version = 'v1') {
    const formData = new FormData()
    formData.append('file', file)

    const response = await request({
      url: `${BASE_URL}/import/${version}`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}
