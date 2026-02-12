import request from '@/utils/request'

const BASE_URL = '/mgr/projectMaterial'

export const projectMaterialApi = {
  // 项目材料修改
  modify(data) {
    return request({
      url: `${BASE_URL}/modify`,
      method: 'post',
      data,
    })
  },
  modifyWithFormData(formData) {
    return request({
      url: `${BASE_URL}/modify`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  // 项目材料分页列表
  getPageList(params) {
    return request({
      url: `${BASE_URL}/page`,
      method: 'post',
      data: params,
    })
  },

  // 项目材料详情
  getInfo(data) {
    return request({
      url: `${BASE_URL}/info`,
      method: 'post',
      data,
    })
  },

  // 批量删除
  batchRemove(ids) {
    return request({
      url: `${BASE_URL}/removes`,
      method: 'post',
      data: ids,
    })
  },

  // 下载项目材料
  download(params) {
    return request({
      url: `${BASE_URL}/download`,
      method: 'post',
      data: params, // 使用data而不是params
      responseType: 'blob',
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },

  // 上传项目材料
  upload(formData) {
    return request({
      url: `${BASE_URL}/upload`,
      method: 'post',
      data: formData,
    })
  },
}
