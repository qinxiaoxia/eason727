import request from '@/utils/request'

const BASE_URL = '/screen/data'

export const screenDataApi = {
  /**
   * 大屏
   * @param {Object} data
   * @returns {Promise}
   */
  getInfo(data) {
    return request({
      url: `${BASE_URL}`,
      method: 'post',
      data,
    })
  },
}

export default screenDataApi
