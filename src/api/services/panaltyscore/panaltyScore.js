// src/api/services/penalty.js
import request from '@/utils/request'

const BASE_URL = '/result/penaltyScore'

export const penaltyScoreApi = {
  /**
   * 扣分分页列表
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  getPageList(params) {
    return request({
      url: `${BASE_URL}/page`,
      method: 'post',
      data: params,
    })
  },

  /**
   * 添加扣分
   * @param {Object} data 扣分数据
   * @returns {Promise}
   */
  add(data) {
    return request({
      url: `${BASE_URL}/add`,
      method: 'post',
      data: data,
    })
  },

  /**
   * 扣分详情
   * @param {Object} data 查询参数
   * @returns {Promise}
   */
  getInfo(data) {
    return request({
      url: `${BASE_URL}/info`,
      method: 'post',
      data: data,
    })
  },

  /**
   * 修改扣分
   * @param {Object} data 修改数据
   * @returns {Promise}
   */
  modify(data) {
    return request({
      url: `${BASE_URL}/modify`,
      method: 'post',
      data: data,
    })
  },

  /**
   * 批量删除扣分
   * @param {Array} ids ID数组
   * @returns {Promise}
   */
  batchRemove(ids) {
    return request({
      url: `${BASE_URL}/removes`,
      method: 'post',
      data: ids,
    })
  },

  /**
   * 确认扣分
   * @param {Object} data 确认数据
   * @returns {Promise}
   */
  confirm(data) {
    return request({
      url: `${BASE_URL}/confirm`,
      method: 'post',
      data: data,
    })
  },
}

export default penaltyScoreApi
