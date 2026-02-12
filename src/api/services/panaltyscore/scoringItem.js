import request from '@/utils/request'

const BASE_URL = '/result/scoringItem'

export const scoringItemApi = {
  /**
   * 评分项分页列表
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
   * 添加评分项
   * @param {Object} data 评分项数据
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
   * 评分项详情
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
   * 修改评分项
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
   * 批量删除评分项
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
}

export default scoringItemApi
