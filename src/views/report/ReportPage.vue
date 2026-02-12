<template>
  <div class="report-management-container">
    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="main-filters">
        <!-- 报告标题搜索 -->
        <el-input
          v-model="filterParams.reportTitle"
          placeholder="搜索报告标题"
          clearable
          @input="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        />

        <!-- 项目选择 -->
        <el-select
          v-model="filterParams.projectId"
          placeholder="选择项目"
          clearable
          filterable
          @change="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        >
          <el-option
            v-for="project in projectList"
            :key="project.id"
            :label="project.projectName"
            :value="project.id"
          />
        </el-select>

        <!-- 报告类型筛选 -->
        <el-select
          v-model="filterParams.reportType"
          placeholder="报告类型"
          clearable
          @change="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        >
          <el-option
            v-for="type in reportTypeOptions"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>

        <!-- 状态筛选 -->
        <el-select
          v-model="filterParams.status"
          placeholder="报告状态"
          clearable
          @change="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        >
          <el-option
            v-for="status in statusOptions"
            :key="status.value"
            :label="status.label"
            :value="status.value"
          />
        </el-select>

        <!-- 操作按钮 -->
        <el-button-group class="action-buttons">
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 表格区域 -->
    <el-card class="table-card">
      <!-- 表格操作区域 -->
      <div class="table-actions">
        <el-button-group>
          <el-button type="primary" @click="handleAddReport">
            <el-icon><Plus /></el-icon>新增报告
          </el-button>
          <el-button @click="handleBatchSubmit" plain>
            <el-icon><Upload /></el-icon>批量提交
          </el-button>
          <el-button :disabled="!selectedRows.length" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>批量删除
          </el-button>
        </el-button-group>
      </div>

      <!-- 数据表格 -->
      <el-table
        :data="tableData"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        border
        stripe
        style="width: 100%; margin-top: 16px"
      >
        <!-- 选择列 -->
        <el-table-column type="selection" width="50" align="center" />

        <!-- 报告ID -->
        <el-table-column prop="id" label="报告ID" width="80" align="center" />

        <!-- 报告标题 -->
        <el-table-column
          prop="reportTitle"
          label="报告标题"
          min-width="200"
          show-overflow-tooltip
        />

        <!-- 所属项目 -->
        <el-table-column prop="projectName" label="所属项目" width="150" show-overflow-tooltip />

        <!-- 报告类型 -->
        <el-table-column prop="reportType" label="报告类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getReportTypeType(row.reportType)" effect="light">
              {{ getReportTypeText(row.reportType) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 报告状态 -->
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="light">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 附件名称 -->
        <el-table-column prop="attachmentName" label="附件名称" width="200" show-overflow-tooltip />

        <!-- 附件大小 -->
        <el-table-column prop="attachmentSize" label="附件大小" width="100" align="center">
          <template #default="{ row }">
            <span>{{ formatFileSize(row.attachmentSize) }}</span>
          </template>
        </el-table-column>

        <!-- 团队ID -->
        <el-table-column prop="teamId" label="团队ID" width="100" align="center" />

        <!-- 操作列 -->
        <el-table-column label="操作" width="180" fixed="right" align="left">
          <template #default="{ row }">
            <div class="icon-actions">
              <!-- 查看详情 -->
              <el-tooltip content="查看详情" placement="top">
                <el-icon class="action-icon view-icon" @click="handleViewDetail(row)">
                  <View />
                </el-icon>
              </el-tooltip>

              <!-- 下载 -->
              <el-tooltip content="下载" placement="top">
                <el-icon class="action-icon download-icon" @click="handleDownload(row)">
                  <Download />
                </el-icon>
              </el-tooltip>

              <!-- 编辑 -->
              <el-tooltip content="编辑" placement="top">
                <el-icon class="action-icon edit-icon" @click="handleEditReport(row)">
                  <Edit />
                </el-icon>
              </el-tooltip>
              <el-tooltip content="发布" placement="top" v-if="canSubmitReport(row)">
                <el-icon class="action-icon submit-icon" @click="handleSubmitReport(row)">
                  <Upload />
                </el-icon>
              </el-tooltip>
              <!-- 删除 -->
              <el-tooltip content="删除" placement="top">
                <el-icon class="action-icon delete-icon" @click="handleDelete(row)">
                  <Delete />
                </el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" direction="rtl" size="50%">
      <div class="drawer-content" v-if="drawerVisible">
        <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
          <el-card shadow="never" class="form-section">
            <template #header>
              <div class="card-header">
                <span>报告信息</span>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="报告标题" prop="reportTitle">
                  <el-input v-model="formData.reportTitle" placeholder="请输入报告标题" clearable />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="所属项目" prop="projectId">
                  <el-select
                    v-model="formData.projectId"
                    placeholder="请选择项目"
                    clearable
                    filterable
                    style="width: 100%"
                  >
                    <el-option
                      v-for="project in projectList"
                      :key="project.id"
                      :label="project.projectName"
                      :value="project.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="报告类型" prop="reportType">
                  <el-select
                    v-model="formData.reportType"
                    placeholder="请选择类型"
                    clearable
                    style="width: 100%"
                  >
                    <el-option
                      v-for="type in reportTypeOptions"
                      :key="type.value"
                      :label="type.label"
                      :value="type.value"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 文件上传 -->
            <el-form-item
              :label="drawerMode === 'add' ? '上传文件' : '更新文件'"
              :prop="drawerMode === 'add' ? 'file' : ''"
            >
              <el-upload
                ref="uploadRef"
                class="upload-demo"
                :auto-upload="false"
                :on-change="handleFileChange"
                :before-upload="beforeUpload"
                :limit="1"
                :accept="allowedFileTypes"
                :file-list="fileList"
              >
                <template #trigger>
                  <el-button type="primary">
                    {{ drawerMode === 'add' ? '选择文件' : '重新选择文件' }}
                  </el-button>
                </template>
                <template #tip>
                  <div class="el-upload__tip">
                    请上传PDF文件，单个文件不超过50MB
                    <div
                      v-if="drawerMode === 'edit' && currentDetail?.attachmentName"
                      class="current-file-info"
                    >
                      <el-tag size="small" type="info"
                        >当前文件: {{ currentDetail.attachmentName }}</el-tag
                      >
                      <el-tag size="small" type="success" style="margin-left: 8px">
                        大小: {{ formatFileSize(currentDetail.attachmentSize) }}
                      </el-tag>
                    </div>
                  </div>
                </template>
              </el-upload>

              <!-- 文件更新提示 -->
              <div v-if="drawerMode === 'edit'" class="edit-mode-tip">
                <el-text type="info" size="small">
                  {{ currentFile ? '将更新为新的文件' : '不选择文件则保持当前文件不变' }}
                </el-text>
              </div>
            </el-form-item>

            <el-form-item label="报告描述">
              <el-input
                v-model="formData.description"
                type="textarea"
                :rows="3"
                placeholder="请输入报告描述"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </el-card>
        </el-form>
      </div>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="saving">
            {{ drawerMode === 'add' ? '创建' : '更新' }}
          </el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="detailVisible"
      :title="'报告详情 - ID: ' + (currentDetail?.id || '未知')"
      direction="rtl"
      size="60%"
    >
      <div class="detail-content" v-if="currentDetail">
        <el-card shadow="never" class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="报告ID">{{
              currentDetail.id || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="报告标题">{{
              currentDetail.reportTitle || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="所属项目">{{
              currentDetail.projectName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="报告类型">
              <el-tag :type="getReportTypeType(currentDetail.reportType)">
                {{ getReportTypeText(currentDetail.reportType) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="报告状态">
              <el-tag :type="getStatusType(currentDetail.status)">
                {{ getStatusText(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="团队ID">{{
              currentDetail.teamId || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="附件名称">{{
              currentDetail.attachmentName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="附件大小">{{
              formatFileSize(currentDetail.attachmentSize)
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never" class="info-card" style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>报告描述</span>
            </div>
          </template>
          <div class="description-content">
            {{ currentDetail.description || '暂无描述' }}
          </div>
        </el-card>
      </div>
    </el-drawer>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Refresh, View, Edit, Download } from '@element-plus/icons-vue'
import { reportApi } from '@/api/services/report/reportApi.js'
import { projectApi } from '@/api/services/project/project.js'

// 状态变量
const loading = ref(false)
const saving = ref(false)
const drawerVisible = ref(false)
const detailVisible = ref(false)
const tableData = ref([])
const selectedRows = ref([])
const projectList = ref([])
const formRef = ref()
const uploadRef = ref()
const fileList = ref([])
const currentFile = ref(null)
const attachmentTypeOptions = [{ label: 'PDF', value: 'pdf' }]
// 分页配置
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

// 筛选参数
const filterParams = reactive({
  reportTitle: '',
  projectId: '',
  reportType: '',
  status: '',
  attachmentName: '',
  teamId: '',
})

// 抽屉模式
const drawerMode = ref('add') // 'add' | 'edit'
const drawerTitle = computed(() => (drawerMode.value === 'add' ? '新增报告' : '编辑报告'))

// 当前操作的数据
const currentDetail = ref(null)

// 表单数据
const formData = reactive({
  reportTitle: '',
  projectId: '',
  reportType: '',
  status: 'draft',
  teamId: 0,
  description: '',
})
// 检查是否可以提交/发布报告
const canSubmitReport = (row) => {
  // 只有草稿状态可以发布
  return row.status === 'draft' || row.status === 'reviewing'
}

// 提交/发布报告
const handleSubmitReport = async (row) => {
  try {
    // 确认对话框
    await ElMessageBox.confirm(`确定要提交报告"${row.reportTitle}"吗？`, '提交确认', {
      type: 'warning',
      confirmButtonText: '确定提交',
      cancelButtonText: '取消',
      distinguishCancelAndClose: true,
    })

    // 构建FormData
    const formDataObj = new FormData()

    // 如果有附件文件，需要重新上传
    if (row.attachmentName) {
      // 这里可以添加逻辑来获取原始文件
      // 暂时先添加一个空的文件字段
      formDataObj.append('file', new Blob())
    }

    // 构建参数
    const paramData = {
      id: row.id,
      reportTitle: row.reportTitle,
      projectId: row.projectId,
      reportType: row.reportType,
      status: 'submitted', // 提交后状态变为已提交
      teamId: row.teamId,
      description: row.description || '',
      attachmentName: row.attachmentName,
      attachmentType: row.attachmentType,
      attachmentSize: row.attachmentSize,
    }

    formDataObj.append('param', JSON.stringify(paramData))

    console.log('提交报告参数:', paramData)

    // 调用提交接口
    const result = await reportApi.submit(formDataObj)

    if (result && result.code === 200) {
      ElMessage.success('报告提交成功！状态已更新为"已提交"')

      // 刷新数据
      await fetchData()
    } else {
      const errorMsg = result?.message || '提交失败'
      ElMessage.error('提交失败: ' + errorMsg)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('提交报告失败:', error)
      ElMessage.error('提交失败: ' + error.message)
    }
  }
}

// 批量提交
const handleBatchSubmit = async () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要提交的报告')
    return
  }

  // 过滤可提交的报告
  const canSubmitRows = selectedRows.value.filter((row) => canSubmitReport(row))
  if (canSubmitRows.length === 0) {
    ElMessage.warning('选中的报告中没有可提交的项目')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要提交选中的 ${canSubmitRows.length} 个报告吗？`,
      '批量提交确认',
      {
        type: 'warning',
        confirmButtonText: '确定提交',
        cancelButtonText: '取消',
      },
    )

    const promises = canSubmitRows.map((row) => handleSingleSubmit(row))
    await Promise.all(promises)

    ElMessage.success(`成功提交 ${canSubmitRows.length} 个报告`)

    // 刷新数据
    await fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量提交失败:', error)
      ElMessage.error('批量提交失败: ' + error.message)
    }
  }
}

// 单个报告提交函数
const handleSingleSubmit = async (row) => {
  const formDataObj = new FormData()

  if (row.attachmentName) {
    formDataObj.append('file', new Blob())
  }

  const paramData = {
    id: row.id,
    reportTitle: row.reportTitle,
    projectId: row.projectId,
    reportType: row.reportType,
    status: 'submitted',
    teamId: row.teamId,
    description: row.description || '',
    attachmentName: row.attachmentName,
    attachmentType: row.attachmentType,
    attachmentSize: row.attachmentSize,
  }

  formDataObj.append('param', JSON.stringify(paramData))

  return reportApi.submit(formDataObj)
}
// 表单验证规则
const formRules = {
  reportTitle: [{ required: true, message: '请输入报告标题', trigger: 'blur' }],
  projectId: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  reportType: [{ required: true, message: '请选择报告类型', trigger: 'change' }],
  file: [
    {
      required: true,
      validator: (rule, value, callback) => {
        if (drawerMode.value === 'add' && !currentFile.value) {
          callback(new Error('请选择要上传的文件'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

// 选项配置
const reportTypeOptions = [
  { label: '总结报告', value: 'technical' },
  { label: '日报', value: 'progress' },
]

const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '已提交', value: 'submitted' },
  { label: '已通过', value: 'approved' },
  { label: '已拒绝', value: 'rejected' },
]
const allowedFileTypes = '.pdf'
// 工具函数
const getReportTypeType = (type) => {
  const typeMap = {
    technical: 'primary',
    progress: 'success',
  }
  return typeMap[type] || 'default'
}

const getReportTypeText = (type) => {
  const textMap = {
    technical: '总结报告',
    progress: '日报',
  }
  return textMap[type] || type
}

const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    submitted: 'primary',
    approved: 'success',
    rejected: 'danger',
  }
  return typeMap[status] || 'default'
}

const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    submitted: '已提交',
    approved: '已通过',
    rejected: '已拒绝',
  }
  return textMap[status] || status
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 数据获取函数
const fetchData = async () => {
  loading.value = true
  try {
    const requestData = {
      page: pagination.currentPage,
      limit: pagination.pageSize,
      data: { ...filterParams },
    }

    const result = await reportApi.getPageList(requestData)

    if (result && result.code === 200) {
      tableData.value = processTableData(result.data || [])
      pagination.total = result.count || 0
    } else {
      ElMessage.error('获取数据失败: ' + (result?.message || '服务器错误'))
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 获取项目列表
const fetchProjectList = async () => {
  try {
    const result = await projectApi.getPageList({
      page: 1,
      limit: 1000,
      data: {},
    })
    if (result && result.code === 200) {
      projectList.value = result.data || []
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

// 处理表格数据
const processTableData = (data) => {
  return data.map((item) => {
    const project = projectList.value.find((p) => p.id === item.projectId)
    return {
      ...item,
      projectName: project ? project.projectName : '未知项目',
    }
  })
}

// 搜索相关函数
const handleSearch = () => {
  pagination.currentPage = 1
  fetchData()
}

const handleReset = () => {
  Object.keys(filterParams).forEach((key) => {
    filterParams[key] = ''
  })
  pagination.currentPage = 1
  fetchData()
}

const handleRefresh = () => {
  fetchData()
  ElMessage.success('数据已刷新')
}

// 表格操作
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  fetchData()
}

const handleCurrentChange = (page) => {
  pagination.currentPage = page
  fetchData()
}

// 新增报告
const handleAddReport = () => {
  drawerMode.value = 'add'
  Object.keys(formData).forEach((key) => {
    formData[key] = key === 'status' ? 'draft' : key === 'teamId' ? 0 : ''
  })
  fileList.value = []
  currentFile.value = null
  drawerVisible.value = true
}

// 编辑报告
// 编辑报告
const handleEditReport = (row) => {
  drawerMode.value = 'edit'
  currentDetail.value = row

  console.log('编辑报告, ID:', row.id)

  // 使用原始数据填充表单
  formData.reportTitle = row.reportTitle || ''
  formData.projectId = row.projectId || ''
  formData.reportType = row.reportType || ''
  formData.status = row.status || 'draft'
  formData.teamId = row.teamId || 0
  formData.description = row.description || ''

  // 清空文件相关数据
  fileList.value = []
  currentFile.value = null

  drawerVisible.value = true
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    const result = await reportApi.getInfo({ id: row.id })
    if (result && result.code === 200) {
      currentDetail.value = result.data
      detailVisible.value = true
    } else {
      ElMessage.error('获取详情失败')
    }
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取详情失败: ' + error.message)
  }
}

// 下载报告
const handleDownload = async (row) => {
  try {
    loading.value = true
    const response = await reportApi.download({
      id: row.id,
      attachmentName: row.attachmentName,
    })

    if (response && response.data) {
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = row.attachmentName || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      ElMessage.success('开始下载...')
    }
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 删除报告
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除报告"${row.reportTitle}"吗?`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await reportApi.batchRemove([row.id])
    if (result && result.code === 200) {
      ElMessage.success('删除成功')
      await fetchData()
    } else {
      ElMessage.error('删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要删除的报告')
    return
  }

  try {
    const ids = selectedRows.value.map((item) => item.id)
    await ElMessageBox.confirm(`确定删除选中的 ${ids.length} 个报告吗?`, '批量删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await reportApi.batchRemove(ids)
    if (result && result.code === 200) {
      ElMessage.success(`成功删除 ${ids.length} 个报告`)
      selectedRows.value = []
      await fetchData()
    } else {
      ElMessage.error('批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败: ' + error.message)
    }
  }
}

// 文件选择变化处理
const handleFileChange = (file) => {
  console.log('文件选择变化:', file)
  currentFile.value = file
  fileList.value = [file]

  // 自动填充报告标题（如果为空）
  if (!formData.reportTitle && file.name) {
    formData.reportTitle = file.name.replace(/\.[^/.]+$/, '')
  }

  // 自动识别并设置附件类型
  const fileExtension = file.name.split('.').pop()?.toLowerCase()
  if (attachmentTypeOptions.some((opt) => opt.value === fileExtension)) {
    formData.attachmentType = fileExtension
    console.log('自动识别附件类型:', fileExtension)
  }
}

// 文件上传前检查
// 文件上传前检查
const beforeUpload = (file) => {
  console.log('文件上传前检查:', file)

  // 检查文件大小
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过50MB!')
    return false
  }

  // 检查文件类型 - 只允许PDF
  const fileExtension = file.name.split('.').pop()?.toLowerCase()
  if (fileExtension !== 'pdf') {
    ElMessage.error({
      message: '不支持的文件格式！\n仅支持PDF格式的文件',
      duration: 5000,
      showClose: true,
    })
    return false
  }

  return true
}

// 统一的保存函数
const handleSave = async () => {
  try {
    if (!formRef.value) return

    const valid = await formRef.value.validate()
    if (!valid) return

    saving.value = true

    if (drawerMode.value === 'add') {
      await handleAddReportApi()
    } else {
      // 编辑模式：根据是否有新文件选择不同的API
      if (currentFile.value) {
        console.log('检测到新文件，使用FormData格式上传')
        await handleEditWithFileUpload()
      } else {
        console.log('没有新文件，使用JSON格式更新基本信息')
        await handleEditWithoutFile()
      }
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

// 有文件更新的编辑
const handleEditWithFileUpload = async () => {
  try {
    const formDataObj = new FormData()
    const file = currentFile.value.raw || currentFile.value

    // 1. 添加文件
    formDataObj.append('file', file)

    // 2. 添加其他参数
    const paramData = {
      id: currentDetail.value.id,
      reportTitle: formData.reportTitle,
      projectId: formData.projectId,
      reportType: formData.reportType,
      status: formData.status,
      teamId: formData.teamId,
      description: formData.description || '',
    }

    formDataObj.append('param', JSON.stringify(paramData))

    console.log('FormData上传参数:', paramData)

    const result = await reportApi.modifyWithFormData(formDataObj)

    if (result && result.code === 200) {
      ElMessage.success('更新成功')
      drawerVisible.value = false
      await fetchData()
    } else {
      const errorMsg = result?.message || '更新失败'
      ElMessage.error('更新失败: ' + errorMsg)
    }
  } catch (error) {
    console.error('文件更新错误:', error)
    ElMessage.error('文件更新失败: ' + error.message)
  }
}

// 无文件更新的编辑
const handleEditWithoutFile = async () => {
  try {
    const updateData = {
      id: currentDetail.value.id,
      reportTitle: formData.reportTitle,
      projectId: formData.projectId,
      reportType: formData.reportType,
      status: formData.status,
      teamId: formData.teamId,
      description: formData.description || '',
    }

    console.log('JSON格式更新数据:', updateData)

    const result = await reportApi.modify(updateData)

    if (result && result.code === 200) {
      ElMessage.success('更新成功')
      drawerVisible.value = false
      await fetchData()
    } else {
      const errorMsg = result?.message || '更新失败'
      ElMessage.error('更新失败: ' + errorMsg)
    }
  } catch (error) {
    console.error('基本信息更新错误:', error)
    ElMessage.error('更新失败: ' + error.message)
  }
}
const handleAddReportApi = async () => {
  if (!currentFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  const formDataObj = new FormData()
  const file = currentFile.value.raw || currentFile.value
  formDataObj.append('file', file)

  const paramData = {
    reportTitle: formData.reportTitle,
    projectId: formData.projectId,
    reportType: formData.reportType,
    status: formData.status,
    teamId: formData.teamId,
    description: formData.description || '',
  }

  formDataObj.append('param', JSON.stringify(paramData))

  const result = await reportApi.add(formDataObj)
  if (result && result.code === 200) {
    ElMessage.success('创建成功')
    drawerVisible.value = false
    await fetchData()
  } else {
    ElMessage.error('创建失败: ' + (result?.message || '未知错误'))
  }
}

// 初始化
onMounted(() => {
  fetchProjectList().then(() => {
    fetchData()
  })
})

// 监听抽屉关闭
watch(drawerVisible, (newVal) => {
  if (!newVal) {
    if (formRef.value) {
      formRef.value.clearValidate()
    }
    fileList.value = []
    currentFile.value = null
  }
})
</script>
<style scoped lang="scss">
.report-management-container {
  padding: 16px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-section {
  background-color: #fff;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

  .main-filters {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    justify-content: flex-start;

    .keyword-input {
      width: 220px;
      margin-right: 16px;
      flex-shrink: 0;
    }

    .action-buttons {
      margin-left: 16px;
      flex-shrink: 0;
    }
  }
}

.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .table-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .table-right-actions {
      display: flex;
      gap: 8px;
    }
  }
}

.pagination-wrapper {
  margin-top: 20px;
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  background: #fff;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .name-text {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.icon-actions {
  display: flex;
  gap: 12px;
  justify-content: left;
  align-items: center;
}

.drawer-content {
  padding: 0;
  height: 100%;
  overflow-y: auto;

  .form-section {
    margin-bottom: 20px;
    border: none;

    :deep(.el-card__header) {
      border-bottom: 1px solid #f0f0f0;
      background-color: #fafafa;
      padding: 12px 20px;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
      color: #303133;
    }
  }
}

.detail-content {
  padding: 0;

  .detail-header {
    margin-bottom: 20px;

    h2 {
      margin: 0;
      color: #303133;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .info-card {
    margin-bottom: 20px;
    border: none;

    :deep(.el-card__body) {
      padding: 0;
    }
  }

  .description-content {
    padding: 20px;
    line-height: 1.6;
    color: #606266;
    background-color: #fafafa;
    border-radius: 4px;
    min-height: 100px;
  }
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #f0f0f0;
}

.upload-demo {
  :deep(.el-upload) {
    width: 100%;

    .el-button {
      width: 100%;
    }
  }

  .el-upload__tip {
    margin-top: 8px;
    font-size: 12px;
    color: #909399;
    line-height: 1.5;
  }
}

.upload-form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.edit-mode-tip {
  margin-top: 8px;

  .el-text {
    font-size: 12px;
  }
}

.current-file-info {
  margin-top: 8px;

  .el-tag {
    margin-right: 8px;
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .main-filters {
    flex-wrap: wrap;
    row-gap: 12px;
  }

  .action-buttons {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .report-management-container {
    padding: 12px;
  }

  .filter-section {
    padding: 12px;

    .main-filters {
      white-space: normal;

      .keyword-input {
        width: 100%;
        margin-right: 0;
        margin-bottom: 12px;
      }
    }
  }

  .table-actions {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;

    .table-right-actions {
      width: 100%;
      justify-content: flex-end;
    }
  }

  .icon-actions {
    gap: 8px;

    .action-icon {
      font-size: 14px;
    }
  }
}

// 抽屉样式优化
:deep(.el-drawer) {
  .el-drawer__header {
    margin-bottom: 20px;
    padding: 20px 20px 0;
    border-bottom: 1px solid #f0f0f0;
  }

  .el-drawer__body {
    padding: 20px;
  }
}

// 表格样式优化
:deep(.el-table) {
  th {
    background-color: #f5f7fa;
    color: #606266;
    font-weight: 600;
  }

  .el-table__row:hover {
    background-color: #f5f7fa !important;
  }
}

// 按钮组样式优化
:deep(.el-button-group) {
  .el-button {
    border-radius: 0;

    &:first-child {
      border-top-left-radius: 4px;
      border-bottom-left-radius: 4px;
    }

    &:last-child {
      border-top-right-radius: 4px;
      border-bottom-right-radius: 4px;
    }
  }
}

// 分页样式优化
:deep(.el-pagination) {
  .btn-prev,
  .btn-next,
  .number {
    background-color: transparent;
    border: 1px solid #dcdfe6;

    &:hover {
      color: #409eff;
    }

    &.active {
      background-color: #409eff;
      border-color: #409eff;
      color: #fff;
    }
  }
}

// 卡片阴影优化
:deep(.el-card) {
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.3s;

  &:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  }
}

// 滚动条样式优化
.drawer-content::-webkit-scrollbar {
  width: 6px;
}

.drawer-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.drawer-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.drawer-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

// 表单标签样式优化
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

// 上传区域特殊样式
.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 4px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
  background-color: #fafafa;

  &:hover {
    border-color: #409eff;
    background-color: #f0f7ff;
  }

  &.is-dragover {
    border-color: #409eff;
    background-color: #ecf5ff;
  }

  .upload-icon {
    font-size: 48px;
    color: #c0c4cc;
    margin-bottom: 16px;
  }

  .upload-text {
    color: #606266;
    margin-bottom: 8px;
  }

  .upload-hint {
    color: #909399;
    font-size: 12px;
  }
}
// 当前文件信息样式
.current-file-info {
  margin-top: 8px;

  .el-tag {
    margin-right: 8px;
  }
}

// 编辑模式提示
.edit-mode-tip {
  margin-top: 8px;

  .el-text {
    font-size: 12px;
  }
}

// 上传表单提示
.upload-form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
