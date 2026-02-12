import request from '@/utils/request'

const BASE_URL = '/rpt/report'

export const reportApi = {
  // 报告新增
  add(formData) {
    return request({
      url: `${BASE_URL}/add`,
      method: 'post',
      data: formData,
    })
  },

  // 报告修改
  // 报告修改（FormData格式，更新文件）
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

  // 报告修改（JSON格式，不更新文件）
  modify(data) {
    return request({
      url: `${BASE_URL}/modify`,
      method: 'post',
      data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },

  // 报告分页列表
  getPageList(params) {
    return request({
      url: `${BASE_URL}/page`,
      method: 'post',
      data: params,
    })
  },

  // 报告详情
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
      ids,
    })
  },

  // 下载报告
  download(params) {
    return request({
      url: `${BASE_URL}/download`,
      method: 'post',
      params,
      responseType: 'blob',
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },

  // 提交报告
  submit(formData) {
    return request({
      url: `${BASE_URL}/submit`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}
