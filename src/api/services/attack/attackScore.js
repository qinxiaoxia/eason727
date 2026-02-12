import request from '@/utils/request'

const BASE_URL = '/result'

// 攻击成绩相关接口
export const attackScoreApi = {
  /**
   * 攻击成绩分页列表
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  async getPageList(params) {
    return request({
      url: `${BASE_URL}/attackResult/page`,
      method: 'post',
      data: params,
    })
  },

  /**
   * 攻击成绩详情
   * @param {Object} data 查询参数 { id: 成绩ID }
   * @returns {Promise}
   */
  getInfo(data) {
    return request({
      url: `${BASE_URL}/attackResult/info`,
      method: 'post',
      data,
    })
  },

  /**
   * 新增攻击成绩
   */
  async add(data) {
    return request({
      url: '/result/attackResult/add',
      method: 'post',
      data: data,
    })
  },

  /**
   * 修改攻击成绩
   */
  async modify(data) {
    return request({
      url: `${BASE_URL}/attackResult/modify`,
      method: 'post',
      data,
    })
  },

  /**
   * 批量删除攻击成绩
   * @param {Array} ids ID数组
   * @returns {Promise}
   */
  batchRemove(ids) {
    return request({
      url: `${BASE_URL}/attackResult/removes`,
      method: 'post',
      data: ids,
    })
  },
}

// 攻击成果相关接口
export const attackAchievementApi = {
  /**
   * 攻击成果分页列表（按成绩ID查询）
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  getPageList(params) {
    return request({
      url: `${BASE_URL}/attackAchievement/page`,
      method: 'post',
      data: params,
    })
  },

  /**
   * 攻击成果详情
   * @param {Object} data 查询参数 { id: 成果ID }
   * @returns {Promise}
   */
  getInfo(data) {
    return request({
      url: `${BASE_URL}/attackAchievement/info`,
      method: 'post',
      data,
    })
  },

  /**
   * 新增攻击成果
   * @param {Object} data 成果数据
   * @returns {Promise}
   */
  async add(data) {
    try {
      const response = await request({
        url: `${BASE_URL}/attackAchievement/add`,
        method: 'post',
        data,
      })

      // 确保返回标准格式
      return {
        data: response.data || { id: Date.now() }, // 如果后端没有返回ID，生成一个临时ID
        success: true,
      }
    } catch (error) {
      console.error('新增成果失败:', error)
      throw error
    }
  },

  /**
   * 修改攻击成果
   * @param {Object} data 修改数据
   * @returns {Promise}
   */
  async modify(data) {
    try {
      const response = await request({
        url: `${BASE_URL}/attackAchievement/modify`,
        method: 'post',
        data,
      })

      // 确保返回标准格式
      return {
        data: response.data || {},
        success: true,
      }
    } catch (error) {
      console.error('修改成果失败:', error)
      throw error
    }
  },

  /**
   * 批量删除攻击成果
   * @param {Array} ids ID数组
   * @returns {Promise}
   */
  batchRemove(ids) {
    return request({
      url: `${BASE_URL}/attackAchievement/removes`,
      method: 'post',
      data: ids,
    })
  },
}

export default {
  attackScoreApi,
  attackAchievementApi,
}
