<template>
  <div class="appeal-management-container">
    <!--筛选区域-->
    <div class="filter-section">
      <div class="main-filters">
        <!--关键词搜索-->
        <el-input
          v-model="filterParams.data.appealTitle"
          placeholder="搜索申诉标题"
          clearable
          @input="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        />
        <!--项目选择-->
        <el-select
          v-model="filterParams.data.projectId"
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
        <!--队伍选择-->
        <el-select
          v-model="filterParams.data.teamId"
          placeholder="选择队伍"
          clearable
          filterable
          @change="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        >
          <el-option
            v-for="team in teamList"
            :key="team.id"
            :label="team.teamName"
            :value="team.id"
          />
        </el-select>
        <!--申诉类型筛选-->
        <el-select
          v-model="filterParams.data.appealType"
          placeholder="申诉类型"
          clearable
          @change="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        >
          <el-option
            v-for="type in appealTypeOptions"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>
        <!--状态筛选-->
        <el-select
          v-model="filterParams.data.status"
          placeholder="状态筛选"
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
                v-model="filterParams.data.appealDescription"
                placeholder="申诉描述"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.data.reviewOpinion"
                placeholder="审核意见"
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
          <el-button type="primary" @click="handleAddAppeal">
            <el-icon><Plus /></el-icon>新增申诉
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
        key="appeal-table"
      >
        <!--选择列-->
        <el-table-column type="selection" width="50" align="center" />

        <!--申诉ID-->
        <el-table-column prop="id" label="申诉ID" width="80" align="center" />

        <!--申诉标题-->
        <el-table-column prop="appealTitle" label="申诉标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="name-cell">
              <el-tooltip :content="row.appealTitle" placement="top">
                <span class="name-text">{{ row.appealTitle }}</span>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>

        <!--申诉类型-->
        <el-table-column prop="appealType" label="申诉类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getAppealTypeTagType(row.appealType)" effect="light">
              {{ getAppealTypeText(row.appealType) }}
            </el-tag>
          </template>
        </el-table-column>

        <!--状态-->
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" effect="light">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!--所属项目-->
        <el-table-column prop="projectName" label="所属项目" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag type="primary" effect="plain">
              {{ row.projectName || getProjectName(row.projectId) }}
            </el-tag>
          </template>
        </el-table-column>

        <!--所属队伍-->
        <el-table-column prop="teamName" label="所属队伍" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag type="success" effect="plain">
              {{ row.teamName || getTeamName(row.teamId) }}
            </el-tag>
          </template>
        </el-table-column>

        <!--申诉描述-->
        <el-table-column
          prop="appealDescription"
          label="申诉描述"
          min-width="250"
          show-overflow-tooltip
        />

        <!--附件名称-->
        <el-table-column prop="attachmentName" label="附件名称" width="200" show-overflow-tooltip />

        <!--审核意见-->
        <el-table-column
          prop="reviewOpinion"
          label="审核意见"
          min-width="200"
          show-overflow-tooltip
        />

        <!--审核时间-->
        <el-table-column prop="reviewTime" label="审核时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.reviewTime) }}
          </template>
        </el-table-column>

        <!--操作列-->
        <el-table-column label="操作" width="170" fixed="right" align="left">
          <template #default="{ row }">
            <div class="icon-actions">
              <!--查看详情-->
              <el-tooltip content="查看详情" placement="top">
                <el-icon class="action-icon view-icon" @click="handleViewDetail(row)">
                  <View />
                </el-icon>
              </el-tooltip>

              <!--下载附件-->
              <el-tooltip content="下载附件" placement="top">
                <el-icon class="action-icon download-icon" @click="handleDownload(row)">
                  <Download />
                </el-icon>
              </el-tooltip>

              <!--提交申诉（草稿状态显示）-->
              <el-tooltip v-if="row.status === 'draft'" content="提交申诉" placement="top">
                <el-icon class="action-icon submit-icon" @click="handleSubmitAppeal(row)">
                  <Upload />
                </el-icon>
              </el-tooltip>

              <!--编辑（草稿状态显示）-->
              <el-tooltip v-if="row.status === 'draft'" content="编辑" placement="top">
                <el-icon class="action-icon edit-icon" @click="handleEditAppeal(row)">
                  <Edit />
                </el-icon>
              </el-tooltip>

              <!--审核通过（待审核状态显示）-->
              <el-tooltip v-if="row.status === 'pending'" content="审核通过" placement="top">
                <el-icon class="action-icon approve-icon" @click="handleApprove(row)">
                  <Check />
                </el-icon>
              </el-tooltip>

              <!--审核驳回（待审核状态显示）-->
              <el-tooltip v-if="row.status === 'pending'" content="审核驳回" placement="top">
                <el-icon class="action-icon reject-icon" @click="handleReject(row)">
                  <Close />
                </el-icon>
              </el-tooltip>

              <!--删除-->
              <el-tooltip content="删除" placement="top">
                <el-icon class="action-icon delete-icon" @click="handleDelete(row.id)">
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
          layout="total, sizes, prev, pager, next, jumper"
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
      class="appeal-drawer"
      :close-on-click-modal="true"
    >
      <div class="drawer-content" v-if="drawerVisible">
        <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
          <!--基础信息-->
          <el-card shadow="never" class="form-section">
            <template #header>
              <div class="card-header">
                <span>申诉信息</span>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="申诉标题" prop="appealTitle">
                  <el-input v-model="formData.appealTitle" placeholder="请输入申诉标题" clearable />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="申诉类型" prop="appealType">
                  <el-select
                    v-model="formData.appealType"
                    placeholder="请选择申诉类型"
                    clearable
                    style="width: 100%"
                  >
                    <el-option
                      v-for="type in appealTypeOptions"
                      :key="type.value"
                      :label="type.label"
                      :value="type.value"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
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
              <el-col :span="12">
                <el-form-item label="所属队伍" prop="teamId">
                  <el-select
                    v-model="formData.teamId"
                    placeholder="请选择队伍"
                    clearable
                    filterable
                    style="width: 100%"
                  >
                    <el-option
                      v-for="team in teamList"
                      :key="team.id"
                      :label="team.teamName"
                      :value="team.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!--文件上传区域-->
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item
                  :label="drawerMode === 'add' ? '上传附件' : '更新附件'"
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

            <el-form-item label="申诉描述" prop="appealDescription">
              <el-input
                v-model="formData.appealDescription"
                type="textarea"
                :rows="4"
                placeholder="请输入申诉描述"
                maxlength="1000"
                show-word-limit
              />
            </el-form-item>
          </el-card>
        </el-form>
      </div>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleSave"
            :loading="saving"
            v-if="drawerMode === 'add'"
          >
            保存草稿
          </el-button>
          <el-button
            type="success"
            @click="handleSaveAndSubmit"
            :loading="saving"
            v-if="drawerMode === 'add'"
          >
            保存并提交
          </el-button>
          <el-button
            type="primary"
            @click="handleSave"
            :loading="saving"
            v-if="drawerMode === 'edit'"
          >
            更新
          </el-button>
        </div>
      </template>
    </el-drawer>

    <!--详情抽屉-->
    <el-drawer
      v-model="detailVisible"
      :title="'申诉详情 - ID:' + (currentDetail?.id || '未知')"
      direction="rtl"
      size="60%"
      class="detail-drawer"
    >
      <div class="detail-content" v-if="currentDetail">
        <div class="detail-header">
          <h2>申诉详情</h2>
        </div>

        <el-card shadow="never" class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="申诉ID">{{
              currentDetail.id || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="申诉标题">{{
              currentDetail.appealTitle || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="申诉类型">
              <el-tag :type="getAppealTypeTagType(currentDetail.appealType)">
                {{ getAppealTypeText(currentDetail.appealType) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusTagType(currentDetail.status)">
                {{ getStatusText(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="所属项目">
              {{ getProjectName(currentDetail.projectId) || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="所属队伍">
              {{ getTeamName(currentDetail.teamId) || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="附件名称">{{
              currentDetail.attachmentName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="审核人ID">{{
              currentDetail.reviewerId || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="审核时间">{{
              formatTime(currentDetail.reviewTime)
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <span>申诉描述</span>
            </div>
          </template>
          <div class="description-content">
            {{ currentDetail.appealDescription || '暂无描述' }}
          </div>
        </el-card>

        <el-card shadow="never" class="info-card" v-if="currentDetail.reviewOpinion">
          <template #header>
            <div class="card-header">
              <span>审核意见</span>
            </div>
          </template>
          <div class="description-content">
            {{ currentDetail.reviewOpinion }}
          </div>
        </el-card>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Delete,
  Refresh,
  Filter,
  View,
  Edit,
  Download,
  Upload,
  Check,
  Close,
} from '@element-plus/icons-vue'

// 导入API
import appealApi from '@/api/services/attack/appeal'
import { projectApi } from '@/api/services/project/project'
import teamApi from '@/api/services/team/team'

// 状态变量
const loading = ref(false)
const saving = ref(false)
const showMoreFilters = ref(false)
const drawerVisible = ref(false)
const detailVisible = ref(false)
const tableData = ref([])
const selectedRows = ref([])
const projectList = ref([])
const teamList = ref([])
const formRef = ref()
const uploadRef = ref()
const fileList = ref([])
const currentFile = ref(null)
const currentDetail = ref(null)

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

// 筛选参数
const filterParams = reactive({
  data: {
    appealTitle: '',
    projectId: '',
    teamId: '',
    appealType: '',
    status: '',
    appealDescription: '',
    reviewOpinion: '',
  },
})

// 抽屉模式
const drawerMode = ref('add')
const drawerTitle = computed(() => (drawerMode.value === 'add' ? '新增申诉' : '编辑申诉'))

// 表单数据
const formData = reactive({
  appealTitle: '',
  appealType: '',
  appealDescription: '',
  projectId: '',
  teamId: '',
  attachmentName: '',
  status: 'draft', // 默认草稿状态
})

// 申诉类型选项
const appealTypeOptions = [
  { label: '分数申诉', value: 'score' },
  { label: '违规申诉', value: 'rule' },
]

// 状态选项
const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '待审核', value: 'pending' },
  { label: '已通过', value: 'approved' },
  { label: '已驳回', value: 'rejected' },
]

// 允许的文件类型
const allowedFileTypes = '.pdf,.jpg,.png,.jpeg'

// 表单验证规则
const formRules = {
  appealTitle: [{ required: true, message: '请输入申诉标题', trigger: 'blur' }],
  appealType: [{ required: true, message: '请选择申诉类型', trigger: 'change' }],
  appealDescription: [{ required: true, message: '请输入申诉描述', trigger: 'blur' }],
  projectId: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  teamId: [{ required: true, message: '请选择所属队伍', trigger: 'change' }],
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

// 获取申诉列表
// 获取申诉列表
const fetchData = async () => {
  loading.value = true
  try {
    // 修改请求数据结构，符合后端 SearchInfo 格式
    const requestData = {
      page: pagination.currentPage,
      limit: pagination.pageSize,
      data: {
        ...filterParams.data,
      },
      // 可能需要添加这些字段
      hasTimeRange: 0,
      timeField: 'createTime',
      minTime: '',
      maxTime: '',
    }

    console.log('请求参数:', requestData)

    // 修改：使用 data 而不是 params
    const result = await appealApi.getPageList(requestData)
    console.log('接口返回结果:', result)

    if (result && result.code === 200) {
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
      console.log('项目列表加载成功:', projectList.value.length)
    } else {
      console.error('获取项目列表失败:', result?.message)
      projectList.value = []
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
    projectList.value = []
  }
}

// 获取队伍列表
const fetchTeamList = async () => {
  try {
    const result = await teamApi.getPageList({
      page: 1,
      limit: 1000,
      data: {},
    })
    if (result && result.code === 200) {
      teamList.value = result.data || []
      console.log('队伍列表加载成功:', teamList.value.length)
    }
  } catch (error) {
    console.error('获取队伍列表失败:', error)
    teamList.value = []
  }
}

// 处理表格数据，添加项目名称和队伍名称
const processTableData = (data) => {
  return data.map((item) => {
    const project = projectList.value.find((p) => p.id === item.projectId)
    const team = teamList.value.find((t) => t.id === item.teamId)

    return {
      ...item,
      projectName: project ? project.projectName : '未知项目',
      teamName: team ? team.teamName : '未知队伍',
    }
  })
}

// 根据项目ID获取项目名称
const getProjectName = (projectId) => {
  if (!projectId) return '未知项目'
  const project = projectList.value.find((p) => p.id === projectId)
  return project ? project.projectName : `项目${projectId}`
}

// 根据队伍ID获取队伍名称
const getTeamName = (teamId) => {
  if (!teamId) return '未知队伍'
  const team = teamList.value.find((t) => t.id === teamId)
  return team ? team.teamName : `队伍${teamId}`
}

// 申诉类型标签样式
const getAppealTypeTagType = (type) => {
  const typeMap = {
    score: 'primary',
    rule: 'success',
    technical: 'warning',
    other: 'info',
  }
  return typeMap[type] || 'default'
}

// 申诉类型显示文本
const getAppealTypeText = (type) => {
  const textMap = {
    score: '分数申诉',
    rule: '违规申诉',
  }
  return textMap[type] || type
}

// 状态标签样式
const getStatusTagType = (status) => {
  const typeMap = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
  }
  return typeMap[status] || 'default'
}

// 状态显示文本
const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    pending: '待审核',
    approved: '已通过',
    rejected: '已驳回',
  }
  return textMap[status] || status
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

// 搜索处理
const handleSearch = () => {
  pagination.currentPage = 1
  fetchData()
}

const handleReset = () => {
  Object.keys(filterParams.data).forEach((key) => {
    filterParams.data[key] = ''
  })
  pagination.currentPage = 1
  fetchData()
}

const handleRefresh = () => {
  fetchData()
  ElMessage.success('数据已刷新')
}

// 表格选择变化
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 分页处理
const handleSizeChange = (newSize) => {
  pagination.pageSize = newSize
  pagination.currentPage = 1
  fetchData()
}

const handleCurrentChange = (newPage) => {
  pagination.currentPage = newPage
  fetchData()
}

// 新增申诉
const handleAddAppeal = () => {
  drawerMode.value = 'add'
  // 重置表单数据
  Object.keys(formData).forEach((key) => {
    if (key === 'status') {
      formData[key] = 'draft'
    } else {
      formData[key] = ''
    }
  })
  fileList.value = []
  currentFile.value = null
  drawerVisible.value = true
}

// 编辑申诉
const handleEditAppeal = (row) => {
  if (row.status !== 'draft') {
    ElMessage.warning('只有草稿状态的申诉才能编辑')
    return
  }

  drawerMode.value = 'edit'
  currentDetail.value = row

  // 填充表单数据
  Object.keys(formData).forEach((key) => {
    if (row[key] !== undefined && row[key] !== null) {
      formData[key] = row[key]
    } else if (key === 'status') {
      formData[key] = 'draft'
    } else {
      formData[key] = ''
    }
  })

  fileList.value = []
  currentFile.value = null
  drawerVisible.value = true
}

// 查看详情
// 查看详情
const handleViewDetail = async (row) => {
  try {
    loading.value = true

    // 确保传递 projectId 和 teamId
    const params = {
      id: row.id,
      projectId: row.projectId, // 确保这个值不为null
      teamId: row.teamId, // 确保这个值不为null
    }

    console.log('详情请求参数:', params)
    const result = await appealApi.getInfo(params)

    if (result && result.code === 200) {
      currentDetail.value = result.data
      detailVisible.value = true
    } else {
      ElMessage.error('获取详情失败:' + (result?.message || '未知错误'))
    }
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取详情失败:' + error.message)
  } finally {
    loading.value = false
  }
}

// 文件选择变化
const handleFileChange = (file) => {
  console.log('文件选择变化:', file)
  currentFile.value = file
  fileList.value = [file]

  // 自动填充附件名称
  if (file.name) {
    formData.attachmentName = file.name
  }
}

// 文件上传前检查
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
  const allowedExtensions = ['pdf', 'jpg', 'png', 'jpeg']
  if (!allowedExtensions.includes(fileExtension)) {
    ElMessage.error('不支持的文件格式! 仅支持: PDF、JPG、PNG、JPEG格式的文件')
    return false
  }

  return true
}

// 保存申诉（草稿）
const handleSave = async () => {
  try {
    if (!formRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }

    // 表单验证
    await formRef.value.validate()
    saving.value = true

    let result
    if (drawerMode.value === 'add') {
      // 新增申诉
      if (!currentFile.value) {
        ElMessage.warning('请选择要上传的文件')
        saving.value = false
        return
      }

      const formDataObj = new FormData()
      const file = currentFile.value.raw || currentFile.value
      formDataObj.append('file', file)

      const paramData = {
        appealTitle: formData.appealTitle,
        appealType: formData.appealType,
        appealDescription: formData.appealDescription,
        projectId: formData.projectId,
        teamId: formData.teamId,
        status: 'draft', // 保存为草稿
      }

      formDataObj.append('param', JSON.stringify(paramData))
      console.log('新增申诉参数:', paramData)

      result = await appealApi.add(formDataObj)
    } else {
      // 编辑申诉
      if (currentFile.value) {
        // 有文件更新，使用FormData格式
        const formDataObj = new FormData()
        const file = currentFile.value.raw || currentFile.value
        formDataObj.append('file', file)

        const paramData = {
          id: currentDetail.value.id,
          appealTitle: formData.appealTitle,
          appealType: formData.appealType,
          appealDescription: formData.appealDescription,
          projectId: formData.projectId,
          teamId: formData.teamId,
          status: 'draft',
        }

        formDataObj.append('param', JSON.stringify(paramData))
        result = await appealApi.modify(formDataObj)
      } else {
        // 无文件更新，使用JSON格式
        const updateData = {
          id: currentDetail.value.id,
          appealTitle: formData.appealTitle,
          appealType: formData.appealType,
          appealDescription: formData.appealDescription,
          projectId: formData.projectId,
          teamId: formData.teamId,
          status: 'draft',
        }
        result = await appealApi.modify(updateData)
      }
    }

    if (result && result.code === 200) {
      ElMessage.success(drawerMode.value === 'add' ? '保存草稿成功' : '更新成功')
      drawerVisible.value = false
      fetchData()
    } else {
      ElMessage.error('操作失败:' + (result?.message || '未知错误'))
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败:' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 保存并提交
const handleSaveAndSubmit = async () => {
  try {
    if (!formRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }

    await formRef.value.validate()
    saving.value = true

    if (!currentFile.value) {
      ElMessage.warning('请选择要上传的文件')
      saving.value = false
      return
    }

    const formDataObj = new FormData()
    const file = currentFile.value.raw || currentFile.value
    formDataObj.append('file', file)

    const paramData = {
      appealTitle: formData.appealTitle,
      appealType: formData.appealType,
      appealDescription: formData.appealDescription,
      projectId: formData.projectId,
      teamId: formData.teamId,
      status: 'pending', // 提交后状态为待审核
    }

    formDataObj.append('param', JSON.stringify(paramData))
    console.log('提交申诉参数:', paramData)

    const result = await appealApi.submit(formDataObj)

    if (result && result.code === 200) {
      ElMessage.success('申诉提交成功')
      drawerVisible.value = false
      fetchData()
    } else {
      ElMessage.error('提交失败:' + (result?.message || '未知错误'))
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败:' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 提交申诉（从列表操作）
const handleSubmitAppeal = async (row) => {
  try {
    if (row.status !== 'draft') {
      ElMessage.warning('只有草稿状态的申诉才能提交')
      return
    }

    await ElMessageBox.confirm(`确定要提交申诉"${row.appealTitle}"吗？`, '提交确认', {
      type: 'warning',
      confirmButtonText: '确定提交',
      cancelButtonText: '取消',
    })

    const result = await appealApi.submit({
      id: row.id,
      status: 'pending',
    })

    if (result && result.code === 200) {
      ElMessage.success('申诉提交成功')
      fetchData()
    } else {
      ElMessage.error('提交失败:' + (result?.message || '未知错误'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('提交失败:' + (error.message || '未知错误'))
    }
  }
}

// 审核通过
const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要通过申诉"${row.appealTitle}"吗？`, '审核通过确认', {
      type: 'warning',
      confirmButtonText: '确定通过',
      cancelButtonText: '取消',
    })

    const result = await appealApi.approve({
      id: row.id,
      status: 'approved',
      reviewOpinion: '审核通过',
    })

    if (result && result.code === 200) {
      ElMessage.success('审核通过成功')
      fetchData()
    } else {
      ElMessage.error('审核失败:' + (result?.message || '未知错误'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('审核失败:' + (error.message || '未知错误'))
    }
  }
}

// 审核驳回
const handleReject = async (row) => {
  try {
    const { value: reviewOpinion } = await ElMessageBox.prompt('请输入驳回理由', '审核驳回', {
      type: 'warning',
      confirmButtonText: '确定驳回',
      cancelButtonText: '取消',
      inputType: 'textarea',
      inputPlaceholder: '请输入驳回理由...',
      inputValidator: (value) => {
        if (!value || value.trim().length === 0) {
          return '驳回理由不能为空'
        }
        return true
      },
    })

    const result = await appealApi.reject({
      id: row.id,
      status: 'rejected',
      reviewOpinion: reviewOpinion.trim(),
    })

    if (result && result.code === 200) {
      ElMessage.success('申诉已驳回')
      fetchData()
    } else {
      ElMessage.error('操作失败:' + (result?.message || '未知错误'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败:' + (error.message || '未知错误'))
    }
  }
}

// 下载附件
const handleDownload = async (row) => {
  try {
    loading.value = true
    if (!row.attachmentName) {
      ElMessage.warning('该申诉没有附件')
      return
    }

    const result = await appealApi.download({
      id: row.id,
    })

    if (result && result.data) {
      const blob = new Blob([result.data], {
        type: result.headers['content-type'] || 'application/octet-stream',
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
    ElMessage.error('下载失败:' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 删除申诉
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个申诉吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await appealApi.batchRemove([id])
    if (result && result.code === 200) {
      ElMessage.success('删除成功')
      fetchData()
    } else {
      ElMessage.error('删除失败:' + (result?.message || '未知错误'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败:' + (error.message || '未知错误'))
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要删除的申诉')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个申诉吗？`,
      '批量删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
      },
    )

    const ids = selectedRows.value.map((item) => item.id)
    const result = await appealApi.batchRemove(ids)
    if (result && result.code === 200) {
      ElMessage.success(`成功删除 ${selectedRows.value.length} 个申诉`)
      selectedRows.value = []
      fetchData()
    } else {
      ElMessage.error('删除失败:' + (result?.message || '未知错误'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败:' + (error.message || '未知错误'))
    }
  }
}

// 监听抽屉关闭
watch(drawerVisible, (newVal) => {
  if (!newVal) {
    if (formRef.value) {
      formRef.value.clearValidate()
    }
    fileList.value = []
    currentFile.value = null
    currentDetail.value = null
  }
})

// 初始化
onMounted(async () => {
  console.log('===开始加载申诉管理页面===')
  // 先加载项目列表和队伍列表
  await Promise.all([fetchProjectList(), fetchTeamList()])
  // 再加载申诉数据
  await fetchData()
  console.log('===页面初始化完成===')
})
</script>

<style scoped lang="scss">
.appeal-management-container {
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

    .action-buttons {
      margin-left: 16px;
      flex-shrink: 0;
    }
  }

  .advanced-filters {
    padding: 12px 0;
    border-top: 1px solid #f0f0f0;
    margin-top: 12px;

    .filter-item {
      width: 100%;
    }
  }
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
  padding: 0 20px;
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
.action-buttons {
  margin-left: 16px;
  flex-shrink: 0;
}
.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #f0f0f0;
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

.upload-form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.current-file-info {
  margin-top: 8px;
}

.edit-mode-tip {
  margin-top: 8px;
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
  .appeal-management-container {
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

  .icon-actions {
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;

    .action-icon {
      padding: 6px;
      font-size: 14px;
    }
  }
}

// 抽屉样式优化
:deep(.el-drawer) {
  .el-drawer__header {
    margin-bottom: 20px;
    padding: 24px 24px 0;
    border-bottom: 1px solid #f0f0f0;

    .el-drawer__title {
      font-weight: 600;
      font-size: 18px;
    }
  }

  .el-drawer__body {
    padding: 24px;
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
</style>
