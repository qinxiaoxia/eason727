// src/api/attackRequest.js
import request from '@/utils/request'

const BASE_URL = '/result'

export const attackRequestApi = {
  async add(data, files) {
    try {
      const formData = new FormData()

      // 添加文件
      if (files && files.length > 0) {
        const actualFiles = files.map((file) => file.raw || file)
        actualFiles.forEach((file) => {
          if (file instanceof File) {
            formData.append('file', file)
          }
        })
      }

      // 构建完整的 param 对象
      const paramData = {
        attackTeamId: Number(data.attackTeamId) || 0,
        attackTeamName: data.attackTeamName || '',
        defenseTeamId: Number(data.defenseTeamId) || 0,
        defenseOrganization: data.defenseOrganization || '',
        systemName: data.systemName || '',
        targetIp: data.targetIp || '',
        targetPort: Number(data.targetPort) || 0,
        targetUrl: data.targetUrl || '',
        projectId: Number(data.projectId) || 0,
        attackPlan: data.attackPlan || '',
        status: 'draft',
      }

      console.log('📤 发送的param数据:', paramData)
      formData.append('param', JSON.stringify(paramData))

      const response = await request({
        url: 'result/attackRequest/add',
        method: 'post',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      console.log('✅ API响应:', response)
      return response
    } catch (error) {
      console.error('❌ 新增失败:', error)
      throw error
    }
  },
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

      console.log('📤 修改请求到:', 'result/attackRequest/modify')
      console.log('📊 请求参数:', data)

      const response = await request({
        url: 'result/attackRequest/modify',
        method: 'post',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      console.log('✅ 修改响应:', response)
      return response.data
    } catch (error) {
      console.error('❌ 修改攻击申请失败:', error)
      throw error
    }
  },

  async submit(data, files) {
    try {
      const formData = new FormData()

      // 添加文件（如果需要）
      if (files && files.length > 0) {
        files.forEach((file) => {
          formData.append('file', file)
        })
      }

      // 提交时的参数
      const paramData = {
        id: data.id,
        attackTeamId: Number(data.attackTeamId) || 0,
        attackTeamName: data.attackTeamName || '',
        defenseTeamId: Number(data.defenseTeamId) || 0,
        defenseOrganization: data.defenseOrganization || '',
        systemName: data.systemName || '',
        targetIp: data.targetIp || '',
        targetPort: Number(data.targetPort) || 0,
        targetUrl: data.targetUrl || '',
        projectId: Number(data.projectId) || 0,
        attackPlan: data.attackPlan || '',
        status: 'pending', // 提交后状态变为待审核
      }

      console.log('📤 提交参数:', paramData)
      formData.append('param', JSON.stringify(paramData))

      const response = await request({
        url: 'result/attackRequest/submit',
        method: 'post',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      return response.data
    } catch (error) {
      console.error('❌ 提交失败:', error)
      throw error
    }
  },

  // 其他接口保持不变（分页、详情等不需要文件上传的接口）
  async getPageList(params) {
    try {
      const response = await request({
        url: 'result/attackRequest/page',
        method: 'post',
        data: params,
      })

      console.log('📊 分页列表响应:', response)

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
      console.error('获取分页列表失败:', error)
      throw error
    }
  },

  async getInfo(data) {
    try {
      const response = await request({
        url: 'result/attackRequest/info',
        method: 'post',
        data: data,
      })
      return response.data
    } catch (error) {
      console.error('获取详情失败:', error)
      throw error
    }
  },

  async batchRemove(ids) {
    try {
      const response = await request({
        url: 'result/attackRequest/removes',
        method: 'post',
        data: ids,
      })

      console.log('batchRemove 原始响应:', response) // 添加调试日志

      // 确保返回正确的数据结构
      if (response && response.data) {
        return response.data // 直接返回后端的数据
      }

      return response
    } catch (error) {
      console.error('批量删除失败:', error)
      throw error
    }
  },

  async approve(data) {
    try {
      const response = await request({
        url: 'result/attackRequest/approve',
        method: 'post',
        data: data,
      })
      return response.data
    } catch (error) {
      console.error('审核失败:', error)
      throw error
    }
  },
  // 修改下载文件方法，使用 AttackRequestVo 参数格式
  async downloadFileById(requestId) {
    try {
      console.log('📥 下载文件 (通过ID):', requestId)

      // 按照后端接口要求，构建 AttackRequestVo 参数
      const param = {
        id: requestId,
      }

      const response = await request({
        url: 'result/attackRequest/download',
        method: 'post',
        data: param, // 直接传递对象，让后端验证
        responseType: 'blob',
      })

      console.log('📄 响应详情:', {
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
        // 如果是JSON响应，说明有错误
        const text = await new Response(response.data).text()
        const errorData = JSON.parse(text)
        console.error('❌ 后端返回错误:', errorData)
        throw new Error(errorData.message || '文件下载失败')
      }

      // 检查文件大小是否合理
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
      console.error('❌ 下载文件失败:', error)
      throw error
    }
  },
  // 修改获取文件URL方法
  async getFileUrlById(requestId) {
    try {
      // 通过ID获取文件
      const blobData = await this.downloadFileById(requestId)

      if (blobData) {
        // 创建blob URL
        const blob = new Blob([blobData], {
          type: 'application/octet-stream', // 默认类型，浏览器会自动识别
        })
        return window.URL.createObjectURL(blob)
      }

      return ''
    } catch (error) {
      console.error('获取文件URL失败:', error)
      return ''
    }
  },
}
