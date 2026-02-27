<template>
  <div class="node-config-panel">
    <div class="panel-header">
      <h3>成果节点配置</h3>
      <div class="header-actions">
        <el-button v-if="!isAudited" type="success" size="small" @click="handleApprove"
          >审核通过</el-button
        >
        <el-button v-if="!isAudited" type="danger" size="small" @click="handleReject"
          >审核驳回</el-button
        >
        <el-button type="primary" size="small" @click="handleSave">保存配置</el-button>
        <el-button type="danger" size="small" @click="handleDelete">删除节点</el-button>
      </div>
    </div>

    <div class="panel-content">
      <el-tabs v-model="activeTab" type="card" class="config-tabs">
        <!-- 基本信息标签页 -->
        <el-tab-pane label="基本信息" name="basic">
          <div class="tab-content">
            <el-form :model="formData" label-width="100px" size="normal">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="成果名称" required>
                    <el-input
                      v-model="formData.achievementName"
                      placeholder="请输入成果名称"
                      maxlength="256"
                      show-word-limit
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="资产名称">
                    <el-input
                      v-model="formData.assetName"
                      placeholder="请输入资产名称"
                      maxlength="256"
                      show-word-limit
                    />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="资产IP">
                    <el-input v-model="formData.assetIP" placeholder="请输入资产IP地址" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="网络层级">
                    <el-select
                      v-model="formData.networkLevel"
                      placeholder="请选择网络层级"
                      style="width: 100%"
                    >
                      <el-option label="互联网区" value="internet" />
                      <el-option label="DMZ区" value="dmz" />
                      <el-option label="核心区" value="core" />
                      <el-option label="办公区" value="office" />
                      <el-option label="测试区" value="test" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="成果状态">
                    <el-select
                      v-model="formData.status"
                      placeholder="请选择状态"
                      style="width: 100%"
                    >
                      <el-option label="草稿" value="draft" />
                      <el-option label="待审核" value="pending" />
                      <el-option label="已批准" value="approved" />
                      <el-option label="已拒绝" value="rejected" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="详细说明">
                <el-input
                  v-model="formData.description"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入成果详细说明"
                  maxlength="1000"
                  show-word-limit
                />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 分数信息标签页 -->
        <el-tab-pane label="分数信息" name="score">
          <div class="tab-content">
            <el-form :model="formData" label-width="100px" size="normal">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="预判分数">
                    <el-input
                      v-model="formData.predictedScore"
                      :min="0"
                      :max="100"
                      placeholder="预判分数"
                      style="width: 100%"
                      controls-position="right"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="实际得分">
                    <el-input
                      v-model="formData.actualScore"
                      :min="0"
                      :max="100"
                      placeholder="实际得分"
                      style="width: 100%"
                      controls-position="right"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="评分确认人">
                <el-input
                  v-model="formData.scoreVerifiedBy"
                  placeholder="请输入评分确认人"
                  maxlength="256"
                  show-word-limit
                />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 附件信息标签页 -->
        <el-tab-pane label="附件信息" name="attachment">
          <div class="tab-content">
            <el-form :model="formData" label-width="100px" size="normal">
              <el-form-item label="附件名称">
                <el-input
                  v-model="formData.attachmentName"
                  placeholder="附件名称(PDF类型)"
                  maxlength="256"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="文件上传">
                <el-upload
                  v-model:file-list="fileList"
                  :multiple="false"
                  :limit="1"
                  :before-upload="beforeUpload"
                  :on-change="handleFileChange"
                  :on-remove="handleRemove"
                  :on-preview="handlePreview"
                  :auto-upload="false"
                  class="file-upload"
                >
                  <el-button type="primary" class="upload-button">
                    <el-icon class="upload-icon"><Upload /></el-icon>
                    点击上传
                  </el-button>
                  <template #tip>
                    <div class="upload-tip">支持 PDF 格式，不超过 10MB</div>
                  </template>
                  <template #file="{ file }">
                    <div class="file-item">
                      <span class="file-name">{{ file.name }}</span>
                      <span class="file-actions">
                        <el-icon class="preview-icon" @click.stop="handlePreview(file)"
                          ><View
                        /></el-icon>
                        <el-icon class="remove-icon" @click.stop="handleRemove(file)"
                          ><Delete
                        /></el-icon>
                      </span>
                    </div>
                  </template>
                </el-upload>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>

  <!-- 文件预览对话框 -->
  <el-dialog
    v-model="previewDialogVisible"
    :title="'文件预览 - ' + previewFileName"
    width="80%"
    top="10vh"
  >
    <div class="preview-container">
      <iframe
        v-if="previewFileUrl"
        :src="previewFileUrl"
        class="pdf-preview"
        frameborder="0"
      ></iframe>
      <div v-else class="no-file">
        <el-icon><InfoFilled /></el-icon>
        <span>没有可预览的文件</span>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="previewDialogVisible = false">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox, ElDialog } from 'element-plus'
import { Upload, View, Delete } from '@element-plus/icons-vue'
import { attackAchievementApi } from '@/api/services/attack/attackScore'

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update', 'delete'])

// 判断是否已审核
const isAudited = computed(() => {
  return formData.value.status === 'approved' || formData.value.status === 'rejected'
})

// 当前激活的标签页
const activeTab = ref('basic')

// 文件列表
const fileList = ref([])

// 文件预览
const previewDialogVisible = ref(false)
const previewFileUrl = ref('')
const previewFileName = ref('')

// 表单数据
const formData = ref({
  // 基本信息
  achievementName: '',
  assetName: '',
  assetIP: '',
  assetId: 0,
  networkLevel: '',
  status: 'draft',
  description: '',

  // 分数信息
  predictedScore: 0,
  actualScore: 0,
  scoreVerifiedBy: '',

  // 附件信息
  attachmentName: '',

  // 关联信息
  upstreamNodeId: '',
  attackTeamId: 0,
  projectId: 0,
  resultId: 0,

  // 时间信息
  createTime: '',
  updateTime: '',
})

// 存储节点数据的响应式引用
const nodeDataRef = ref({})

// 调试节点信息
const debugNodeInfo = () => {
  console.log('=== X6 节点调试信息 ===')
  console.log('节点对象:', props.node)
  console.log('节点ID:', props.node.id)
  console.log('节点类型:', props.node.constructor.name)
  console.log(
    '可用方法:',
    Object.keys(props.node).filter((key) => typeof props.node[key] === 'function'),
  )

  // 检查常用的 X6 方法
  const x6Methods = ['getData', 'setData', 'attr', 'prop', 'getAttr', 'setAttr', 'setAttrs']
  x6Methods.forEach((method) => {
    console.log(`${method} 方法:`, typeof props.node[method])
  })

  console.log('节点数据:', props.node.getData ? props.node.getData() : '无 getData 方法')
  console.log('节点属性:', props.node.attr ? props.node.attr() : '无 attr 方法')
  console.log('========================')
}

// 安全的节点数据获取 - 不修改 props
const getNodeData = () => {
  if (!props.node) return {}

  try {
    // 尝试不同的 X6 数据获取方式
    if (typeof props.node.getData === 'function') {
      return props.node.getData() || {}
    } else if (typeof props.node.prop === 'function') {
      return props.node.prop('data') || {}
    } else if (props.node.store && props.node.store.data) {
      return props.node.store.data || {}
    } else {
      return props.node.data || {}
    }
  } catch (error) {
    console.error('获取节点数据失败:', error)
    return {}
  }
}

// 安全的属性获取
const getNodeAttr = (path) => {
  if (!props.node) return ''

  try {
    if (typeof props.node.attr === 'function') {
      return props.node.attr(path) || ''
    } else if (typeof props.node.getAttr === 'function') {
      return props.node.getAttr(path) || ''
    } else if (props.node.attrs) {
      // 从 attrs 对象中获取 - 只读操作，不修改
      const pathParts = path.split('/')
      let value = props.node.attrs
      for (const part of pathParts) {
        if (value && value[part] !== undefined) {
          value = value[part]
        } else {
          return ''
        }
      }
      return value || ''
    }
    return ''
  } catch (error) {
    console.error('获取节点属性失败:', error)
    return ''
  }
}

// 初始化表单数据
// 初始化表单数据
const initFormData = () => {
  if (!props.node) return

  try {
    const nodeData = getNodeData()
    const currentTime = new Date().toISOString().replace('T', ' ').substring(0, 19)
    const nodeLabel =
      getNodeAttr('label/text') || getNodeAttr('text/text') || nodeData.achievementName || ''

    formData.value = {
      // 基本信息
      achievementName: nodeData.achievementName || nodeLabel,
      assetName: nodeData.assetName || '',
      assetIP: nodeData.assetIP || '',
      assetId: nodeData.assetId || 0,
      networkLevel: nodeData.networkLevel || '',
      status: nodeData.status || 'draft',
      description: nodeData.description || '',

      // 分数信息
      predictedScore: nodeData.predictedScore || 0,
      actualScore: nodeData.actualScore || 0,
      scoreVerifiedBy: nodeData.scoreVerifiedBy || '',

      // 附件信息
      attachmentName: nodeData.attachmentName || '',

      // 关联信息
      resultId: nodeData.resultId || 0,

      // 时间信息
      createTime: nodeData.createTime || currentTime,
      updateTime: nodeData.updateTime || currentTime,
    }

    // 初始化文件列表（关键修改）
    if (nodeData.attachmentName) {
      fileList.value = [
        {
          name: nodeData.attachmentName,
          url: nodeData.attachmentUrl || '',
        },
      ]
    } else {
      fileList.value = []
    }

    // 保存节点数据引用
    nodeDataRef.value = { ...nodeData }

    // 初始化后更新节点样式，确保颜色正确显示对应状态
    updateNodeStyle()
  } catch (error) {
    console.error('初始化表单数据失败:', error)
  }
}
// 审核通过
const handleApprove = async () => {
  try {
    const nodeData = getNodeData()
    const nodeName = formData.value.achievementName || '未知节点'

    await ElMessageBox.confirm(`确定审核通过节点"${nodeName}"吗?`, '审核确认', {
      type: 'success',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })

    const result = await attackAchievementApi.approve({ id: nodeData.id })
    if (result) {
      ElMessage.success('审核通过成功')
      formData.value.status = 'approved'
      updateNodeStyle()

      // 更新节点数据
      if (props.node && typeof props.node.setData === 'function') {
        const updatedData = { ...nodeData, status: 'approved' }
        props.node.setData(updatedData)
      }

      emit('update', { ...formData.value, status: 'approved' })
    } else {
      ElMessage.error('审核失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('审核通过失败:', error)
      ElMessage.error('审核通过失败: ' + (error.message || '未知错误'))
    }
  }
}

// 审核驳回
const handleReject = async () => {
  try {
    const nodeData = getNodeData()
    const nodeName = formData.value.achievementName || '未知节点'

    await ElMessageBox.confirm(`确定审核驳回节点"${nodeName}"吗?`, '审核确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })

    const result = await attackAchievementApi.reject({ id: nodeData.id })
    if (result) {
      ElMessage.success('审核驳回成功')
      formData.value.status = 'rejected'
      updateNodeStyle()

      // 更新节点数据
      if (props.node && typeof props.node.setData === 'function') {
        const updatedData = { ...nodeData, status: 'rejected' }
        props.node.setData(updatedData)
      }

      emit('update', { ...formData.value, status: 'rejected' })
    } else {
      ElMessage.error('审核失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('审核驳回失败:', error)
      ElMessage.error('审核驳回失败: ' + (error.message || '未知错误'))
    }
  }
}

const handleSave = async () => {
  if (!props.node) return

  try {
    // 验证必填项
    if (!formData.value.achievementName.trim()) {
      ElMessage.warning('请输入成果名称')
      return
    }

    const nodeData = getNodeData()
    const saveData = {
      achievementName: formData.value.achievementName.trim(),
      assetName: formData.value.assetName || '',
      assetIP: formData.value.assetIP || '',
      assetId: Number(formData.value.assetId) || 0,
      networkLevel: formData.value.networkLevel || '',
      status: formData.value.status || 'draft',
      description: formData.value.description || '',
      predictedScore: Number(formData.value.predictedScore) || 0,
      actualScore: Number(formData.value.actualScore) || 0,
      scoreVerifiedBy: formData.value.scoreVerifiedBy || '',
      resultId: Number(formData.value.resultId) || 0, // 确保关联成绩ID
      projectId: Number(formData.value.projectId) || 0,
      attackTeamId: Number(formData.value.attackTeamId) || 0,
      updateTime: new Date().toISOString().replace('T', ' ').substring(0, 19),
    }

    // 提取文件
    const files = []
    if (fileList.value && fileList.value.length > 0) {
      fileList.value.forEach((fileObj) => {
        if (fileObj.raw && fileObj.raw instanceof File) {
          files.push(fileObj.raw)
        }
      })
    }

    let result

    if (nodeData.id) {
      // 更新成果
      saveData.id = nodeData.id
      result = await attackAchievementApi.modify(saveData, files)
    } else {
      // 创建成果
      result = await attackAchievementApi.add(saveData, files)

      // 如果创建成功，更新节点ID
      if (result && result.data && result.data.id) {
        // 触发父组件更新节点ID
        emit('node-id-update', {
          node: props.node,
          newId: result.data.id,
        })
      }
    }

    if (result) {
      ElMessage.success(nodeData.id ? '成果更新成功' : '成果创建成功')

      // 提取接口返回的文件信息
      const returnedData = result.data || {}
      const attachmentInfo = {
        attachmentName: returnedData.attachmentName || formData.value.attachmentName || '',
        attachmentUrl: returnedData.attachmentUrl || '',
      }

      // 更新节点数据
      const updatedData = {
        ...saveData,
        ...attachmentInfo,
        id: returnedData.id || nodeData.id,
      }

      // 直接更新节点的data
      if (props.node && typeof props.node.setData === 'function') {
        props.node.setData(updatedData)
        console.log('✅ 节点数据已直接更新:', updatedData)
      }

      // 更新节点显示
      updateNodeDisplay()

      // 更新文件列表
      if (attachmentInfo.attachmentName) {
        fileList.value = [
          {
            name: attachmentInfo.attachmentName,
            url: attachmentInfo.attachmentUrl || '',
          },
        ]
      }

      // 通知父组件
      emit('update', updatedData)
    } else {
      ElMessage.error('保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(`保存失败: ${error.message || '未知错误'}`)
  }
}

// 删除节点
const handleDelete = async () => {
  if (!props.node) return

  try {
    const nodeData = getNodeData()
    const nodeName = formData.value.achievementName || '未知节点'

    await ElMessageBox.confirm(`确定删除节点"${nodeName}"吗？此操作不可撤销。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    if (nodeData.id) {
      // 从后端删除
      await attackAchievementApi.batchRemove([nodeData.id])
    }

    // 触发父组件删除事件
    emit('delete')
    ElMessage.success(`节点"${nodeName}"已删除`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 更新节点显示 - 使用 X6 方法，不修改 props
const updateNodeDisplay = () => {
  if (!props.node) return

  try {
    // 更新节点标签 - 使用 X6 标准的 attr 方法
    if (typeof props.node.attr === 'function') {
      props.node.attr({
        label: {
          text: formData.value.achievementName,
        },
      })
    } else if (typeof props.node.setAttrs === 'function') {
      props.node.setAttrs({
        label: {
          text: formData.value.achievementName,
        },
      })
    }

    // 根据状态更新节点颜色
    updateNodeStyle()
  } catch (error) {
    console.error('更新节点显示失败:', error)
  }
}

// 更新节点样式 - 使用 X6 方法
const updateNodeStyle = () => {
  if (!props.node) return

  const status = formData.value.status
  let color = '#409eff' // 默认蓝色

  switch (status) {
    case 'approved':
      color = '#67c23a' // 绿色 - 已批准
      break
    case 'rejected':
      color = '#f56c6c' // 红色 - 已拒绝
      break
    case 'pending':
      color = '#e6a23c' // 黄色 - 待审核
      break
    case 'draft':
    default:
      color = '#909399' // 灰色 - 草稿
      break
  }

  // 设置节点样式
  if (typeof props.node.attr === 'function') {
    props.node.attr({
      body: {
        fill: color,
        stroke: color,
        strokeWidth: 2,
      },
    })
  }
}

// 文件上传处理
// 文件上传前的验证
const beforeUpload = (file) => {
  const isPDF = file.type === 'application/pdf'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isPDF) {
    ElMessage.error('只能上传 PDF 格式的文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return true
}

// 文件预览
const handlePreview = async (file) => {
  try {
    console.log('预览文件:', file)

    if (file.url) {
      // 如果有URL，直接预览
      previewFileUrl.value = file.url
      previewFileName.value = file.name
      previewDialogVisible.value = true
    } else if (file.raw) {
      // 如果是本地文件，创建临时URL
      const tempUrl = URL.createObjectURL(file.raw)
      previewFileUrl.value = tempUrl
      previewFileName.value = file.name
      previewDialogVisible.value = true
    } else if (props.node) {
      // 如果是已保存的文件，尝试从节点数据中获取
      const nodeData = getNodeData()
      if (nodeData.attachmentUrl) {
        previewFileUrl.value = nodeData.attachmentUrl
        previewFileName.value = nodeData.attachmentName || file.name
        previewDialogVisible.value = true
      } else {
        ElMessage.warning('文件预览失败：没有可用的文件URL')
      }
    } else {
      ElMessage.warning('文件预览失败：文件信息不完整')
    }
  } catch (error) {
    console.error('预览文件失败:', error)
    ElMessage.error('文件预览失败: ' + (error.message || '未知错误'))
  }
}

// 文件移除处理
const handleRemove = () => {
  formData.value.attachmentName = ''
  fileList.value = []
  ElMessage.info('文件已移除')
}

const handleFileChange = (file) => {
  console.log('文件选择变化:', file)
  // 自动填充附件名称
  if (!formData.value.attachmentName && file.name) {
    formData.value.attachmentName = file.name
  }
}

// 监听节点变化
watch(
  () => props.node,
  (newNode) => {
    console.log('节点发生变化:', newNode)
    initFormData()
    debugNodeInfo() // 调试信息
  },
  { immediate: true },
)

onMounted(() => {
  nextTick(() => {
    initFormData()
    debugNodeInfo() // 调试信息
  })
})
</script>

<style scoped lang="scss">
.node-config-panel {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;

  h3 {
    margin: 0;
    color: #303133;
    font-size: 18px;
    font-weight: 600;
  }
}

.panel-content {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  overflow: hidden;
}

.config-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;

  :deep(.el-tabs__content) {
    flex: 1;
    overflow-y: auto;
  }

  :deep(.el-tabs__header) {
    margin: 0;
    padding: 0 20px;
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;
  }

  :deep(.el-tabs__nav-wrap) {
    &::after {
      background-color: transparent;
    }
  }

  :deep(.el-tabs__item) {
    padding: 0 20px;
    height: 40px;
    line-height: 40px;
    font-weight: 500;

    &.is-active {
      background: #fff;
      border-bottom-color: #fff;
    }
  }
}

.tab-content {
  padding: 20px;
  min-height: 400px;
}

.file-upload {
  width: 100%;

  .upload-button {
    width: 100%;
    height: 40px;

    .upload-icon {
      margin-right: 8px;
    }
  }

  .upload-tip {
    margin-top: 8px;
    font-size: 12px;
    color: #909399;
    line-height: 1.4;
  }
}

/* 表单项样式优化 */
:deep(.el-form-item) {
  margin-bottom: 20px;

  .el-form-item__label {
    font-weight: 500;
    color: #606266;
    padding-right: 12px;
  }

  .el-form-item__content {
    line-height: 1.4;
  }
}

/* 数字输入框样式优化 */
:deep(.el-input-number) {
  width: 100%;

  .el-input__inner {
    text-align: left;
  }
}

/* 日期选择器样式优化 */
:deep(.el-date-editor) {
  width: 100%;

  .el-input__inner {
    border-radius: 6px;
  }
}

/* 文本域样式优化 */
:deep(.el-textarea) {
  .el-textarea__inner {
    border-radius: 6px;
    resize: vertical;
    min-height: 80px;
  }
}

/* 上传组件样式优化 */
:deep(.el-upload) {
  width: 100%;

  .el-upload-dragger {
    width: 100%;
    border-radius: 6px;
    border: 2px dashed #d9d9d9;

    &:hover {
      border-color: #409eff;
    }
  }
}

/* 滚动条样式优化 */
.tab-content::-webkit-scrollbar {
  width: 6px;
}

.tab-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.tab-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.tab-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .node-config-panel {
    padding: 8px;
  }

  .panel-header {
    padding: 12px 16px;
    margin-bottom: 12px;
    flex-direction: column;
    gap: 12px;
    align-items: stretch;

    h3 {
      text-align: center;
    }
  }

  .config-tabs {
    :deep(.el-tabs__header) {
      padding: 0 12px;
    }

    :deep(.el-tabs__item) {
      padding: 0 12px;
      font-size: 14px;
    }
  }

  .tab-content {
    padding: 16px;
  }

  :deep(.el-form-item) {
    margin-bottom: 16px;
  }

  :deep(.el-col) {
    margin-bottom: 8px;
  }
}
.header-actions {
  display: flex;
  gap: 8px;

  .el-button {
    &.el-button--success {
      background-color: #67c23a;
      border-color: #67c23a;
    }

    &.el-button--danger {
      background-color: #f56c6c;
      border-color: #f56c6c;
    }
  }
}

/* 文件上传样式 */
.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-top: 8px;
  transition: all 0.3s;

  &:hover {
    background: #ecf5ff;
  }
}

.file-name {
  font-size: 14px;
  color: #606266;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.preview-icon,
.remove-icon {
  cursor: pointer;
  font-size: 16px;
  transition: color 0.3s;

  &:hover {
    color: #409eff;
  }
}

.remove-icon:hover {
  color: #f56c6c;
}

/* 文件预览样式 */
.preview-container {
  width: 100%;
  height: 70vh;
  position: relative;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.pdf-preview {
  width: 100%;
  height: 100%;
}

.no-file {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  font-size: 16px;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
