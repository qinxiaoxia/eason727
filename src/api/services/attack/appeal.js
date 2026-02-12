import request from '@/utils/request'

const BASE_URL = '/result/appeal'

export default {
  // 申诉分页列表
  getPageList(data) {
    return request({
      url: `${BASE_URL}/page`,
      method: 'POST',
      data, // 使用 data 而不是 params
    })
  },

  // 申诉详情
  getInfo(data) {
    return request({
      url: `${BASE_URL}/info`,
      method: 'POST',
      data,
    })
  },

  // 新增申诉
  add(formData) {
    return request({
      url: `${BASE_URL}/add`,
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // 修改申诉
  modify(data) {
    return request({
      url: `${BASE_URL}/modify`,
      method: 'POST',
      data: data,
    })
  },

  // 提交申诉
  submit(data) {
    return request({
      url: `${BASE_URL}/submit`,
      method: 'POST',
      data: data,
    })
  },

  // 审核通过
  approve(data) {
    return request({
      url: `${BASE_URL}/approve`,
      method: 'POST',
      data,
    })
  },

  // 审核驳回
  reject(data) {
    return request({
      url: `${BASE_URL}/reject`,
      method: 'POST',
      data: data,
    })
  },

  // 批量删除
  batchRemove(ids) {
    return request({
      url: `${BASE_URL}/removes`,
      method: 'POST',
      ids,
    })
  },

  // 下载附件
  download(params) {
    return request({
      url: `${BASE_URL}/download`,
      method: 'POST',
      params,
      responseType: 'blob',
    })
  },
}
