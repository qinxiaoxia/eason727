import request from '@/utils/request'

const BASE_URL = '/mgr/scoringRule'

export const scoringRuleApi = {
  /**
   * 评分规则分页列表
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
   * 添加评分规则
   * @param {Object} data 评分规则数据
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
   * 评分规则详情
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
   * 修改评分规则
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
   * 批量删除评分规则
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
   * 导入评分规则
   * @param {File} file 文件
   * @returns {Promise}
   */
  import(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: `${BASE_URL}/import`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}

export default scoringRuleApi
