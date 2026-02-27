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

export const attackAchievementApi = {
  async add(data, files) {
    try {
      const formData = new FormData()

      // 修复：只添加实际选择的文件，不添加空占位符
      if (files && files.length > 0) {
        files.forEach((file) => {
          if (file instanceof File && file.size > 0) {
            formData.append('file', file)
            console.log('📁 添加文件到FormData:', file.name, file.size)
          }
        })
      }

      // 如果用户没有选择文件，但后端要求必须传file参数
      // 可以在这里添加空文件逻辑（根据后端实际要求）
      if (formData.has('file') === false) {
        // 只有后端确实要求必须有file参数时才添加空文件
        const emptyBlob = new Blob([], { type: 'application/pdf' })
        const emptyFile = new File([emptyBlob], 'empty.pdf', { type: 'application/pdf' })
        formData.append('file', emptyFile)
        console.log('📭 添加空文件占位符')
      }

      // 添加其他参数
      const paramData = {
        achievementName: data.achievementName,
        assetName: data.assetName || '',
        assetIP: data.assetIP || '',
        assetId: Number(data.assetId) || 0,
        networkLevel: data.networkLevel || '',
        status: 'draft',
        description: data.description || '',
        predictedScore: Number(data.predictedScore) || 0,
        actualScore: Number(data.actualScore) || 0,
        scoreVerifiedBy: data.scoreVerifiedBy || '',
        resultId: Number(data.resultId) || 0,
        projectId: Number(data.projectId) || 0,
        attackTeamId: Number(data.attackTeamId) || 0,
      }

      formData.append('param', JSON.stringify(paramData))

      console.log('📤 最终FormData内容:')
      for (let [key, value] of formData.entries()) {
        console.log(
          `${key}:`,
          value instanceof File ? `[File: ${value.name}, ${value.size} bytes]` : value,
        )
      }

      const response = await request({
        url: `${BASE_URL}/attackAchievement/add`,
        method: 'post',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      return response
    } catch (error) {
      console.error('❌ 新增失败:', error)
      throw error
    }
  },

  // 修改攻击成果
  async modify(data, files) {
    try {
      const formData = new FormData()

      // 添加文件
      if (files && files.length > 0) {
        files.forEach((file) => {
          formData.append('file', file)
        })
      }

      // 参数放在 'param' 字段中
      formData.append('param', JSON.stringify(data))

      console.log('📤 修改成果请求到:', `${BASE_URL}/attackAchievement/modify`)
      console.log('📊 修改请求参数:', data)

      const response = await request({
        url: `${BASE_URL}/attackAchievement/modify`,
        method: 'post',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      console.log('✅ 修改成果响应:', response)
      return response
    } catch (error) {
      console.error('❌ 修改攻击成果失败:', error)
      throw error
    }
  },

  // 审核通过攻击成果
  async approve(data) {
    try {
      const formData = new FormData()
      formData.append('param', JSON.stringify(data))

      console.log('📤 审核通过请求参数:', data)

      const response = await request({
        url: `${BASE_URL}/attackAchievement/approve`,
        method: 'post',
        data: formData,
      })

      console.log('✅ 审核通过响应:', response)
      return response
    } catch (error) {
      console.error('❌ 审核通过失败:', error)
      throw error
    }
  },

  // 审核驳回攻击成果
  async reject(data) {
    try {
      const formData = new FormData()
      formData.append('param', JSON.stringify(data))

      console.log('📤 审核驳回请求参数:', data)

      const response = await request({
        url: `${BASE_URL}/attackAchievement/reject`,
        method: 'post',
        data: formData,
      })

      console.log('✅ 审核驳回响应:', response)
      return response
    } catch (error) {
      console.error('❌ 审核驳回失败:', error)
      throw error
    }
  },

  // 分页列表
  async getPageList(params) {
    try {
      const response = await request({
        url: `${BASE_URL}/attackAchievement/page`,
        method: 'post',
        data: params,
      })

      console.log('📊 成果分页列表响应:', response)

      // 根据后端实际返回的数据结构调整
      if (response && response.data) {
        return {
          code: 200,
          data: response.data.data || response.data.records || response.data,
          total: response.data.total || response.data.count || 0,
          message: 'success',
        }
      }

      return response.data
    } catch (error) {
      console.error('获取成果分页列表失败:', error)
      throw error
    }
  },

  // 详情
  async getInfo(data) {
    try {
      const response = await request({
        url: `${BASE_URL}/attackAchievement/info`,
        method: 'post',
        data: data,
      })
      return response.data
    } catch (error) {
      console.error('获取成果详情失败:', error)
      throw error
    }
  },

  // 批量删除
  async batchRemove(ids) {
    try {
      const response = await request({
        url: `${BASE_URL}/attackAchievement/removes`,
        method: 'post',
        data: ids,
      })

      console.log('成果批量删除原始响应:', response)

      if (response && response.data) {
        return response.data
      }

      return response
    } catch (error) {
      console.error('批量删除成果失败:', error)
      throw error
    }
  },

  // 下载成果附件
  async downloadFileById(achievementId) {
    try {
      console.log('📥 下载成果附件 (通过ID):', achievementId)

      const param = {
        id: achievementId,
      }

      const response = await request({
        url: `${BASE_URL}/attackAchievement/download`,
        method: 'post',
        data: param,
        responseType: 'blob',
      })

      console.log('📄 成果附件响应详情:', {
        status: response.status,
        headers: response.headers,
        dataType: typeof response.data,
        dataSize: response.data?.size,
        dataTypeDetail: response.data?.type,
      })

      // 检查响应类型
      const contentType = response.headers['content-type']
      console.log('📋 响应Content-Type:', contentType)

      if (contentType && contentType.includes('application/json')) {
        const text = await new Response(response.data).text()
        const errorData = JSON.parse(text)
        console.error('❌ 后端返回错误:', errorData)
        throw new Error(errorData.message || '文件下载失败')
      }

      // 检查文件大小
      if (response.data.size < 1024) {
        console.warn('⚠️ 文件大小异常:', response.data.size, '字节')
        const text = await new Response(response.data).text()
        try {
          const errorData = JSON.parse(text)
          throw new Error(errorData.message || '文件可能不存在或已损坏')
        } catch {
          throw new Error('文件大小异常，可能下载失败')
        }
      }

      return response.data
    } catch (error) {
      console.error('❌ 下载成果附件失败:', error)
      throw error
    }
  },

  // 获取成果附件URL
  async getFileUrlById(achievementId) {
    try {
      const blobData = await this.downloadFileById(achievementId)

      if (blobData) {
        const blob = new Blob([blobData], {
          type: 'application/octet-stream',
        })
        return window.URL.createObjectURL(blob)
      }

      return ''
    } catch (error) {
      console.error('获取成果附件URL失败:', error)
      return ''
    }
  },
}

export default {
  attackScoreApi,
  attackAchievementApi,
}
