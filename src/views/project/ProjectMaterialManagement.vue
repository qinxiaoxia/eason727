<template>
  <div class="project-material-container">
    <!--筛选区域-->
    <div class="filter-section">
      <div class="main-filters">
        <!--关键词搜索-->
        <el-input
          v-model="filterParams.materialName"
          placeholder="搜索材料名称"
          clearable
          @input="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        />
        <!--项目选择-->
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
        <!--材料分类筛选-->
        <el-select
          v-model="filterParams.category"
          placeholder="材料分类"
          clearable
          @change="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        >
          <el-option
            v-for="category in categoryOptions"
            :key="category.value"
            :label="category.label"
            :value="category.value"
          />
        </el-select>
        <!--操作按钮-->
        <el-button-group class="action-buttons">
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
          <el-button @click="showMoreFilters = !showMoreFilters">
            <el-icon><Filter /></el-icon>{{ showMoreFilters ? '收起' : '更多' }}
          </el-button>
        </el-button-group>
      </div>
      <!--更多筛选-->
      <el-collapse-transition>
        <div v-show="showMoreFilters" class="advanced-filters">
          <el-row :gutter="16">
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.attachmentType"
                placeholder="附件类型"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.description"
                placeholder="材料描述"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
          </el-row>
        </div>
      </el-collapse-transition>
    </div>
    <!--表格区域-->
    <el-card class="table-card">
      <!--表格操作区域-->
      <div class="table-actions">
        <el-button-group>
          <el-button type="primary" @click="handleAddMaterial">
            <el-icon><Plus /></el-icon>新增材料
          </el-button>
          <el-button :disabled="!selectedRows.length" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>批量删除
          </el-button>
        </el-button-group>
        <div class="table-right-actions">
          <el-button @click="handleRefresh" plain>
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>
      <!--数据表格-->
      <el-table
        :data="tableData"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        border
        stripe
        style="width: 100%; margin-top: 16px"
        key="material-table"
      >
        <!--选择列-->
        <el-table-column type="selection" width="50" align="center" />
        <!--材料ID-->
        <el-table-column prop="id" label="材料 ID" min-width="80" align="center" />
        <!--材料名称-->
        <el-table-column prop="materialName" label="材料名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="name-cell">
              <el-tooltip :content="row.materialName" placement="top">
                <span class="name-text">{{ row.materialName }}</span>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        <!--所属项目-->
        <el-table-column prop="projectName" label="所属项目" width="180" show-overflow-tooltip />
        <!--材料分类-->
        <el-table-column prop="category" label="材料分类" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)" effect="light">
              {{ getCategoryText(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <!--附件名称-->
        <el-table-column prop="attachmentName" label="附件名称" width="200" show-overflow-tooltip />
        <!--附件类型-->
        <el-table-column prop="attachmentType" label="附件类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.attachmentType" :type="getAttachmentTypeTagType(row.attachmentType)">
              {{ getAttachmentTypeText(row.attachmentType) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <!--附件大小-->
        <!--附件大小-->
        <el-table-column prop="attachmentSize" label="附件大小" width="120" align="center">
          <template #default="{ row }">
            <span>{{ formatFileSize(row.attachmentSize) }}</span>
          </template>
        </el-table-column>
        <!--材料描述-->
        <el-table-column
          prop="description"
          label="材料描述"
          min-width="250"
          show-overflow-tooltip
        />
        <!--操作列-->
        <el-table-column label="操作" width="140" fixed="right" align="left">
          <template #default="{ row }">
            <div class="icon-actions">
              <!--查看详情-->
              <el-tooltip content="查看详情" placement="top">
                <el-icon class="action-icon view-icon" @click="handleViewDetail(row)">
                  <View />
                </el-icon>
              </el-tooltip>
              <!--下载-->
              <el-tooltip content="下载" placement="top">
                <el-icon class="action-icon download-icon" @click="handleDownload(row)">
                  <Download />
                </el-icon>
              </el-tooltip>
              <!--编辑-->
              <el-tooltip content="编辑" placement="top">
                <el-icon class="action-icon edit-icon" @click="handleEditMaterial(row)">
                  <Edit />
                </el-icon>
              </el-tooltip>
              <!--删除-->
              <el-tooltip content="删除" placement="top">
                <el-icon class="action-icon delete-icon" @click="handleDelete(row)">
                  <Delete />
                </el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <!--分页-->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total,sizes,prev, pager,next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    <!--新增/编辑抽屉-->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      direction="rtl"
      size="50%"
      class="material-drawer"
      :close-on-click-modal="true"
    >
      <div class="drawer-content" v-if="drawerVisible">
        <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
          <!--基础信息-->
          <el-card shadow="never" class="form-section">
            <template #header>
              <div class="card-header">
                <span>基础信息</span>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="材料名称" prop="materialName">
                  <el-input
                    v-model="formData.materialName"
                    placeholder="请输入材料名称"
                    clearable
                  />
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
                <el-form-item label="材料分类" prop="category">
                  <el-select
                    v-model="formData.category"
                    placeholder="请选择分类"
                    clearable
                    style="width: 100%"
                  >
                    <el-option
                      v-for="category in categoryOptions"
                      :key="category.value"
                      :label="category.label"
                      :value="category.value"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!--文件上传区域 - 新增和编辑都显示-->
            <el-row :gutter="20">
              <el-col :span="24">
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
                        请上传文件（PDF、JPG、PNG、JPEG格式），单个文件不超过50MB
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
                  <div class="upload-form-tip" v-if="fileList[0]">
                    默认使用文件名: {{ fileList[0]?.name?.replace(/\.[^/.]+$/, '') }}
                  </div>
                  <div v-if="drawerMode === 'edit'" class="edit-mode-tip">
                    <el-text type="info" size="small">
                      {{ currentFile ? '将更新为新的文件' : '不选择文件则保持当前文件不变' }}
                    </el-text>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="材料描述" prop="description">
              <el-input
                v-model="formData.description"
                type="textarea"
                :rows="3"
                placeholder="请输入材料描述"
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
    <!--详情抽屉-->
    <el-drawer
      v-model="detailVisible"
      :title="'材料详情 - ID:' + (currentDetail?.id || '未知')"
      direction="rtl"
      size="60%"
      class="detail-drawer"
    >
      <div class="detail-content" v-if="currentDetail">
        <div class="detail-header">
          <h2>材料详情</h2>
        </div>

        <el-card shadow="never" class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="材料 ID">{{
              currentDetail.id || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="材料名称">{{
              currentDetail.materialName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="所属项目">
              {{ getProjectName(currentDetail.projectId) || currentDetail.projectName || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="材料分类">
              <el-tag :type="getCategoryType(currentDetail.category)">
                {{ getCategoryText(currentDetail.category) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="附件名称">{{
              currentDetail.attachmentName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="附件类型">
              <el-tag :type="getAttachmentTypeTagType(currentDetail.attachmentType)">
                {{ getAttachmentTypeText(currentDetail.attachmentType) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="附件大小">{{
              formatFileSize(currentDetail.attachmentSize)
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <span>材料描述</span>
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
import { Plus, Delete, Refresh, Filter, View, Edit, Download } from '@element-plus/icons-vue'
import { projectMaterialApi } from '@/api/services/project/projectMaterial.js'
import { projectApi } from '@/api/services/project/project.js'

//状态变量
const loading = ref(false)
const saving = ref(false)
const showMoreFilters = ref(false)
const drawerVisible = ref(false)
const detailVisible = ref(false)
const tableData = ref([])
const selectedRows = ref([])
const projectList = ref([])
const formRef = ref()
const uploadRef = ref()
const fileList = ref([])
const currentFile = ref(null)

//分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

//筛选参数
const filterParams = reactive({
  materialName: '',
  projectId: '',
  projectName: '',
  category: '',
  attachmentType: '',
  description: '',
})

const searchTimeRange = reactive({
  hasTimeRange: 0,
  timeField: 'createTime',
  minTime: '',
  maxTime: '',
})

//抽屉模式
const drawerMode = ref('add')
const drawerTitle = computed(() => (drawerMode.value === 'add' ? '新增材料' : '编辑材料'))

//表单数据
const formData = reactive({
  materialName: '',
  projectId: '',
  category: '',
  attachmentType: '',
  description: '',
  projectName: '',
})
const allowedFileTypes = computed(() => {
  return attachmentTypeOptions.map((opt) => `.${opt.value}`).join(',')
})
//表单验证规则
const formRules = {
  materialName: [{ required: true, message: '请输入材料名称', trigger: 'blur' }],
  projectId: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  category: [{ required: true, message: '请选择材料分类', trigger: 'change' }],
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
// 附件类型标签样式
const getAttachmentTypeTagType = (type) => {
  const typeMap = {
    pdf: 'primary',
    jpg: 'success',
    png: 'warning',
    jpeg: 'info',
  }
  return typeMap[type] || 'default'
}
// 附件类型显示文本
const getAttachmentTypeText = (type) => {
  return attachmentTypeMap[type] || type
}
//材料分类选项
const categoryOptions = [
  { label: '项目文档', value: 'document' },
  { label: '技战法', value: 'word' },
  { label: '测试报告', value: 'test' },
  { label: '会议记录', value: 'meeting' },
  { label: '其他', value: 'other' },
]
const attachmentTypeOptions = [
  { label: 'PDF', value: 'pdf' },
  { label: 'JPG', value: 'jpg' },
  { label: 'PNG', value: 'png' },
  { label: 'JPEG', value: 'jpeg' },
]
const attachmentTypeMap = {
  pdf: 'PDF',
  jpg: 'JPG',
  png: 'PNG',
  jpeg: 'JPEG',
}
//当前操作的数据
const currentDetail = ref(null)

//=======数据获取函数=======
const fetchData = async () => {
  loading.value = true
  try {
    // 确保项目列表已加载
    if (projectList.value.length === 0) {
      await fetchProjectList()
    }

    const requestData = {
      page: pagination.currentPage,
      limit: pagination.pageSize,
      data: {
        materialName: filterParams.materialName,
        projectId: filterParams.projectId,
        category: filterParams.category,
        attachmentType: filterParams.attachmentType,
        description: filterParams.description,
      },
      hasTimeRange: searchTimeRange.hasTimeRange,
      timeField: searchTimeRange.timeField,
      minTime: searchTimeRange.minTime,
      maxTime: searchTimeRange.maxTime,
    }

    console.log('请求参数:', requestData)
    const result = await projectMaterialApi.getPageList(requestData)
    console.log('接口返回结果:', result)

    if (result && result.code === 200) {
      // 处理数据，添加项目名称（确保使用最新的项目列表）
      const processedData = processTableData(result.data || [])
      tableData.value = processedData
      pagination.total = result.count || 0
      console.log('处理后的数据:', processedData)
    } else {
      ElMessage.error('获取数据失败:' + (result?.message || '服务器错误'))
      tableData.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败:' + error.message)
  } finally {
    loading.value = false
  }
}

//获取项目列表
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

//========搜索相关函数========
const handleSearch = () => {
  pagination.currentPage = 1
  fetchData()
}

const handleReset = () => {
  Object.keys(filterParams).forEach((key) => {
    filterParams[key] = ''
  })
  searchTimeRange.hasTimeRange = 0
  searchTimeRange.minTime = ''
  searchTimeRange.maxTime = ''
  pagination.currentPage = 1
  fetchData()
}

const handleRefresh = () => {
  fetchData()
  ElMessage.success('数据已刷新')
}

//========表格操作========
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

const handleAddMaterial = () => {
  drawerMode.value = 'add'
  Object.keys(formData).forEach((key) => {
    formData[key] = ''
  })
  fileList.value = []
  currentFile.value = null
  drawerVisible.value = true
}

// 编辑材料
const handleEditMaterial = (row) => {
  drawerMode.value = 'edit'
  currentDetail.value = row

  console.log('编辑材料，ID:', row.id)

  // 使用原始数据填充表单
  formData.materialName = row.materialName || ''
  formData.projectId = row.projectId || ''
  formData.category = row.category || ''
  formData.attachmentType = row.attachmentType || ''
  formData.description = row.description || ''

  // 清空文件相关数据
  fileList.value = []
  currentFile.value = null

  drawerVisible.value = true
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    console.log('查看详情，行数据:', row)

    // 构建请求参数，确保包含项目ID
    const requestData = {
      id: row.id,
      projectId: row.projectId, // 添加项目ID
    }

    console.log('详情请求参数:', requestData)

    const result = await projectMaterialApi.getInfo(requestData)

    if (result && result.code === 200 && result.data) {
      currentDetail.value = result.data
      detailVisible.value = true
      console.log('详情数据获取成功:', result.data)
    } else {
      console.error('获取详情失败:', result)
      ElMessage.error('获取详情失败: ' + (result?.message || '未知错误'))
    }
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取详情失败: ' + error.message)
  }
}
const processTableData = (data) => {
  return data.map((item) => {
    // 查找项目名称
    const project = projectList.value.find((proj) => proj.id === item.projectId)
    return {
      ...item,
      projectName: project ? project.projectName : '未知项目', // 添加项目名称字段
    }
  })
}
const handleDownload = async (row) => {
  try {
    loading.value = true

    // 构造请求参数
    const requestData = {
      id: row.id,
      attachmentName: row.attachmentName,
      attachmentSize: row.attachmentSize,
      attachmentType: row.attachmentType,
      category: row.category,
      materialName: row.materialName,
      projectId: row.projectId,
    }

    // 调用下载接口
    const response = await projectMaterialApi.download(requestData)

    // 处理响应
    if (response && response.data) {
      const blob = new Blob([response.data], {
        type: response.headers['content-type'] || 'application/octet-stream',
      })

      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = row.attachmentName || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      ElMessage.success('开始下载...')
    } else {
      ElMessage.error('下载失败: 服务器未返回有效数据')
    }
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除材料"${row.materialName}"吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })
    const result = await projectMaterialApi.batchRemove([row.id])
    if (result && result.code === 200) {
      ElMessage.success('删除成功')
      await fetchData()
    } else {
      const errorMsg = result?.message || '删除失败'
      ElMessage.error('删除失败:' + errorMsg)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败:' + error.message)
    }
  }
}

const handleBatchDelete = async () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要删除的材料')
    return
  }
  try {
    const ids = selectedRows.value.map((item) => item.id)
    await ElMessageBox.confirm(`确定删除选中的${ids.length}个材料吗？`, '批量删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })
    const result = await projectMaterialApi.batchRemove(ids)
    if (result && result.code === 200) {
      ElMessage.success(`成功删除${ids.length}个材料`)
      selectedRows.value = []
      await fetchData()
    } else {
      const errorMsg = result?.message || '批量删除失败'
      ElMessage.error('批量删除失败:' + errorMsg)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败:' + error.message)
    }
  }
}

// 统一的保存函数
const handleSave = async () => {
  try {
    if (!formRef.value) return

    const valid = await formRef.value.validate()
    if (!valid) return

    saving.value = true

    if (drawerMode.value === 'add') {
      await handleAddMaterialApi()
    } else {
      await handleEditMaterialApi()
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}
const handleAddMaterialApi = async () => {
  if (!currentFile.value) {
    ElMessage.warning('请选择要上传的文件')
    saving.value = false
    return
  }

  const formDataObj = new FormData()
  const file = currentFile.value.raw || currentFile.value
  formDataObj.append('file', file)

  const paramData = {
    projectId: formData.projectId,
    category: formData.category,
    materialName: formData.materialName,
    description: formData.description || '',
    attachmentType: formData.attachmentType,
  }

  formDataObj.append('param', JSON.stringify(paramData))

  console.log('新增请求参数:', paramData)

  const result = await projectMaterialApi.upload(formDataObj)

  if (result && result.code === 200) {
    ElMessage.success('创建成功')
    drawerVisible.value = false
    await fetchData()
  } else {
    const errorMsg = result?.message || '创建失败'
    ElMessage.error('创建失败:' + errorMsg)
  }
}
// 在文件上传函数中添加详细调试
const handleEditWithFileUpload = async () => {
  try {
    const formDataObj = new FormData()
    const file = currentFile.value.raw || currentFile.value

    console.log('=== 文件上传详细调试 ===')
    console.log('原始文件名:', file.name)
    console.log('文件大小:', file.size)
    console.log('文件类型:', file.type)

    // 1. 添加文件
    formDataObj.append('file', file)

    // 2. 添加其他参数
    const paramData = {
      id: currentDetail.value.id,
      projectId: formData.projectId,
      category: formData.category,
      materialName: formData.materialName,
      description: formData.description || '',
      attachmentType: formData.attachmentType || file.name.split('.').pop()?.toLowerCase() || '',
      attachmentName: file.name, // 明确指定文件名
      attachmentSize: file.size, // 明确指定文件大小
    }

    console.log('上传参数详情:', paramData)

    formDataObj.append('param', JSON.stringify(paramData))

    // 调试FormData内容
    console.log('FormData内容:')
    for (let [key, value] of formDataObj.entries()) {
      console.log(`${key}:`, value)
    }

    const result = await projectMaterialApi.modifyWithFormData(formDataObj)

    if (result && result.code === 200) {
      console.log('✅ 上传成功，等待数据刷新...')

      ElMessage.success(
        `文件更新成功！\n原文件: ${currentDetail.value.attachmentName}\n新文件: ${file.name}`,
      )
      drawerVisible.value = false

      // 延迟刷新，确保后端处理完成
      setTimeout(async () => {
        await fetchData()

        // 检查更新结果
        const updatedItem = tableData.value.find((item) => item.id === currentDetail.value.id)
        if (updatedItem) {
          console.log('=== 更新后数据验证 ===')
          console.log('期望文件名:', file.name)
          console.log('实际文件名:', updatedItem.attachmentName)
          console.log('期望大小:', file.size)
          console.log('实际大小:', updatedItem.attachmentSize)
          console.log('完整数据:', updatedItem)

          if (updatedItem.attachmentName !== file.name) {
            console.warn('⚠️ 文件名不一致！后端可能对文件名进行了处理')
          }
          if (updatedItem.attachmentSize !== file.size) {
            console.warn('⚠️ 文件大小不一致！')
          }
        }
      }, 1000)
    }
  } catch (error) {
    console.error('文件更新错误:', error)
    ElMessage.error('文件更新失败: ' + error.message)
  }
}
// 编辑材料API调用
const handleEditMaterialApi = async () => {
  console.log('=== 编辑模式 ===')

  if (currentFile.value) {
    console.log('检测到新文件，使用FormData格式上传')
    await handleEditWithFileUpload()
  } else {
    console.log('没有新文件，使用JSON格式更新基本信息')
    await handleEditWithoutFile()
  }
}

// 编辑时不更新文件，只更新基本信息（JSON格式）
const handleEditWithoutFile = async () => {
  const updateData = {
    id: currentDetail.value.id,
    projectId: formData.projectId,
    category: formData.category,
    materialName: formData.materialName,
    description: formData.description || '',
    attachmentType: currentDetail.value.attachmentType,
    attachmentName: currentDetail.value.attachmentName,
    attachmentSize: currentDetail.value.attachmentSize,
  }

  console.log('JSON格式更新:', updateData)

  try {
    const result = await projectMaterialApi.modify(updateData)

    if (result && result.code === 200) {
      ElMessage.success('基本信息更新成功')
      drawerVisible.value = false
      await fetchData()
    } else {
      const errorMsg = result?.message || '更新失败'
      ElMessage.error('更新失败:' + errorMsg)
    }
  } catch (error) {
    console.error('基本信息更新错误:', error)
    ElMessage.error('更新失败: ' + error.message)
  }
}
const beforeUpload = (file) => {
  console.log('文件上传前检查:', file)

  // 检查文件大小
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过50MB!')
    return false
  }

  // 检查文件类型
  const fileExtension = file.name.split('.').pop()?.toLowerCase()
  const allowedExtensions = attachmentTypeOptions.map((opt) => opt.value)

  if (!allowedExtensions.includes(fileExtension)) {
    ElMessage.error({
      message: `不支持的文件格式！\n仅支持：${allowedExtensions.join(', ').toUpperCase()} 格式的文件`,
      duration: 5000,
      showClose: true,
    })
    return false
  }

  return true
}
const handleFileChange = (file) => {
  console.log('文件选择变化:', file)
  currentFile.value = file
  fileList.value = [file]

  // 自动填充材料名称（如果为空）
  if (!formData.materialName && file.name) {
    formData.materialName = file.name.replace(/\.[^/.]+$/, '')
  }

  // 自动识别并设置附件类型
  const fileExtension = file.name.split('.').pop()?.toLowerCase()
  if (attachmentTypeOptions.some((opt) => opt.value === fileExtension)) {
    formData.attachmentType = fileExtension
    console.log('自动识别附件类型:', fileExtension)
  }
}
// 根据项目ID获取项目名称
const getProjectName = (projectId) => {
  if (!projectId) return '未知项目'
  const project = projectList.value.find((proj) => proj.id === projectId)
  return project ? project.projectName : '未知项目'
}

//========工具函数========
const getCategoryType = (category) => {
  const typeMap = {
    document: 'primary',
    test: 'warning',
    word: 'success',
    meeting: 'info',
    other: 'default',
  }
  return typeMap[category] || 'default'
}

const getCategoryText = (category) => {
  const textMap = {
    document: '项目文档',
    word: '技战法',
    test: '测试报告',
    meeting: '会议记录',
    other: '其他',
  }
  return textMap[category] || category
}

// 处理带单位的文件大小
const parseFileSize = (sizeStr) => {
  if (!sizeStr) return 0

  // 如果是数字，直接返回
  if (!isNaN(sizeStr)) return Number(sizeStr)

  // 处理带单位的字符串
  const units = {
    B: 1,
    KB: 1024,
    MB: 1024 * 1024,
    GB: 1024 * 1024 * 1024,
    TB: 1024 * 1024 * 1024 * 1024,
  }

  const match = sizeStr.match(/^([\d.]+)\s*([KMGTP]?B)$/i)
  if (match) {
    const value = parseFloat(match[1])
    const unit = match[2].toUpperCase()
    return value * (units[unit] || 1)
  }

  return 0
}

// 修改格式化函数支持字符串输入
const formatFileSize = (input) => {
  // 先解析输入
  const bytes = typeof input === 'string' ? parseFileSize(input) : Number(input)

  if (!bytes || bytes === 0) return '0 B'
  if (isNaN(bytes) || bytes < 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const index = Math.min(i, sizes.length - 1)

  let sizeValue = bytes / Math.pow(k, index)

  if (index === 0) {
    return Math.round(sizeValue) + ' ' + sizes[index]
  } else {
    if (sizeValue < 10) {
      return sizeValue.toFixed(2) + ' ' + sizes[index]
    } else if (sizeValue < 100) {
      return sizeValue.toFixed(1) + ' ' + sizes[index]
    } else {
      return Math.round(sizeValue) + ' ' + sizes[index]
    }
  }
}

onMounted(async () => {
  console.log('=== 开始加载项目材料管理页面 ===')

  // 先加载项目列表
  await fetchProjectList()

  const urlParams = new URLSearchParams(window.location.search)
  const projectId = urlParams.get('projectId')
  const projectNameFromUrl = urlParams.get('projectName') // 从URL获取的项目名称（备用）
  const action = urlParams.get('action')

  console.log('🔍 URL参数:', { projectId, projectNameFromUrl, action })

  if (projectId) {
    console.log('🎯 检测到项目ID，开始处理预填逻辑...')

    // 根据 projectId 查找对应的 projectName
    const project = projectList.value.find((p) => p.id === parseInt(projectId))
    const projectName = project ? project.projectName : projectNameFromUrl

    if (projectName) {
      // 将 projectName 填充到搜索栏
      filterParams.projectName = projectName
      console.log('📝 设置筛选条件 - 名称:', projectName)

      // 延迟执行，确保DOM更新完成
      setTimeout(() => {
        console.log('🔍 开始搜索...')
        handleSearch()

        if (action === 'add') {
          console.log('🎯 检测到添加操作，准备打开新增抽屉...')

          // 延迟打开抽屉，确保搜索完成
          setTimeout(() => {
            console.log('📂 打开新增材料抽屉...')
            handleAddMaterial()

            // 填充表单数据
            formData.projectName = projectName
            console.log('📝 预填表单数据 - 名称:', projectName)

            ElMessage.success(`✅ 已为您预填项目: ${projectName}`)
            console.log('✅ 预填完成')
          }, 800)
        }
      }, 300)
    } else {
      console.warn('⚠️ 未找到对应的项目名称')
    }
  } else {
    console.log('ℹ️ 没有项目ID参数，正常初始化')
    fetchData()
  }
})
//监听抽屉关闭事件
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
.project-material-container {
  padding: 16px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.filter-section {
  background-color: #fff;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

  .main-filters {
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    justify-content: flex-start;
    width: 100%;
    gap: 16px;
    .keyword-input {
      width: 220px;
      margin-right: 16px;
      flex-shrink: 0;
    }

    .time-filter-group {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 350px;
      flex-shrink: 0;

      .time-field-select {
        width: 120px;
        flex-shrink: 0;
      }
    }

    .action-buttons {
      margin-left: 16px;
      flex-shrink: 0;
    }
  }
}
.main-filters {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  justify-content: flex-start;
  width: 100%;
}

.keyword-input {
  width: 220px;
  margin-right: 16px;
  flex-shrink: 0;
}
.action-buttons {
  margin-left: 16px;
  flex-shrink: 0;
}
.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: auto;

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
}

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

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
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

.upload-form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
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
  .project-material-container {
    padding: 12px;
  }

  .filter-section {
    padding: 12px;
  }

  .main-filters {
    white-space: normal;
  }

  .keyword-input {
    width: 100%;
    margin-right: 0;
    margin-bottom: 12px;
  }

  .time-filter-group {
    min-width: auto;
    width: 100%;
    flex-wrap: wrap;
  }

  .advanced-filters {
    .el-col {
      margin-bottom: 12px;
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

  .action-icon {
    font-size: 14px;
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

// 选择框样式优化
:deep(.el-select) {
  width: 100%;
}

// 卡片阴影优化
:deep(.el-card) {
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.3s;

  &:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  }
}

// 上传组件样式优化
:deep(.upload-demo) {
  width: 100%;

  .el-upload {
    width: 100%;

    .el-button {
      width: 100%;
    }
  }

  .el-upload__tip {
    margin-top: 8px;
    font-size: 12px;
    color: #909399;
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
.current-file-info {
  margin-top: 8px;

  .el-tag {
    margin-right: 8px;
  }
}

.current-file-info {
  margin-top: 8px;

  .el-tag {
    margin-right: 8px;
  }
}

.edit-mode-tip {
  margin-top: 8px;

  .el-text {
    font-size: 12px;
  }
}

.upload-form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.upload-demo {
  :deep(.el-upload) {
    width: 100%;

    .el-button {
      width: 100%;
    }
  }

  .el-upload__tip {
    font-size: 12px;
    color: #909399;
    line-height: 1.5;
  }
}
</style>
