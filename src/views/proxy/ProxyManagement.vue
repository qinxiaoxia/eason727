<template>
  <div class="proxy-management-container">
    <!--搜索区域-->
    <el-card class="search-card" shadow="never">
      <el-form :model="queryParams" inline>
        <el-form-item label="代理服务器">
          <el-input
            v-model="queryParams.data.proxyServer"
            placeholder="请输入代理服务器"
            clearable
            style="width: 220px"
            @input="handleSearch"
            @keyup.enter="handleImmediateSearch"
            @clear="handleReset"
          />
        </el-form-item>
        <el-form-item label="协议类型">
          <el-select
            v-model="queryParams.data.protocol"
            placeholder="请选择协议类型"
            clearable
            style="width: 220px"
            @change="handleSearch"
          >
            <el-option label="HTTP" value="http" />
            <el-option label="HTTPS" value="https" />
            <el-option label="SOCKS5" value="socks5" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select
            v-model="queryParams.data.projectId"
            placeholder="请选择项目"
            clearable
            filterable
            style="width: 220px"
            @change="handleSearch"
          >
            <el-option
              v-for="project in projectOptions"
              :key="project.id"
              :label="project.projectName"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属队伍">
          <el-select
            v-model="queryParams.data.teamId"
            placeholder="请选择队伍"
            clearable
            filterable
            style="width: 220px"
            @change="handleSearch"
          >
            <el-option
              v-for="team in teamOptions"
              :key="team.id"
              :label="team.teamName"
              :value="team.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!--操作区域-->
    <el-card class="operation-card" shadow="never">
      <div class="operation-container">
        <div class="operation-left">
          <el-button type="primary" @click="handleAdd" class="action-btn">
            <el-icon><Plus /></el-icon>
            新增代理
          </el-button>
          <el-button
            :disabled="selectedRows.length === 0"
            @click="handleBatchDelete"
            class="action-btn"
          >
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
          <el-upload
            action="/mgr/proxyPool/import"
            :headers="uploadHeaders"
            :show-file-list="false"
            :before-upload="beforeUpload"
            :on-success="handleImportSuccess"
            :on-error="handleImportError"
          >
            <el-button type="success" class="action-btn">
              <el-icon><Upload /></el-icon>
              导入代理
            </el-button>
          </el-upload>
        </div>
        <div class="operation-stats">
          <el-tag type="info">共{{ total }}个代理</el-tag>
          <el-tag v-if="selectedRows.length > 0" type="warning">
            已选{{ selectedRows.length }}项
          </el-tag>
          <el-button @click="handleRefresh" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!--表格区域-->
    <el-card shadow="never" class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        @selection-change="handleSelectionChange"
        stripe
        style="width: 100%"
        class="proxy-table"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="代理ID" width="100" />
        <el-table-column
          prop="proxyServer"
          label="代理服务器"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column prop="protocol" label="协议类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getProtocolTag(row.protocol)" effect="light">
              {{ getProtocolText(row.protocol) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="proxyAccount" label="代理账号" width="150" show-overflow-tooltip />
        <el-table-column prop="projectName" label="所属项目" width="150">
          <template #default="{ row }">
            <span>{{ getProjectDisplayName(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="teamName" label="所属队伍" width="150">
          <template #default="{ row }">
            <span>{{ getTeamDisplayName(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="left">
          <template #default="{ row }">
            <div class="icon-actions">
              <el-tooltip content="查看详情" placement="top">
                <el-icon class="action-icon" @click="handleViewDetail(row)">
                  <View />
                </el-icon>
              </el-tooltip>
              <el-tooltip content="编辑" placement="top">
                <el-icon class="action-icon" @click="handleEdit(row)">
                  <Edit />
                </el-icon>
              </el-tooltip>
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
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.limit"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
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
      size="600px"
      class="proxy-drawer"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="代理服务器" prop="proxyServer">
          <el-input
            v-model="formData.proxyServer"
            placeholder="请输入代理服务器地址"
            maxlength="100"
            class="custom-input"
          />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input
            v-model.number="formData.port"
            placeholder="请输入端口号"
            type="number"
            min="1"
            max="65535"
            class="custom-input"
          />
        </el-form-item>
        <el-form-item label="协议类型" prop="protocol">
          <el-select v-model="formData.protocol" placeholder="请选择协议类型" class="custom-input">
            <el-option label="HTTP" value="http" />
            <el-option label="HTTPS" value="https" />
            <el-option label="SOCKS5" value="socks5" />
          </el-select>
        </el-form-item>
        <el-form-item label="代理账号" prop="proxyAccount">
          <el-input
            v-model="formData.proxyAccount"
            placeholder="请输入代理账号"
            maxlength="50"
            class="custom-input"
          />
        </el-form-item>
        <el-form-item label="代理密码" prop="proxyPassword">
          <el-input
            v-model="formData.proxyPassword"
            placeholder="请输入代理密码"
            type="password"
            maxlength="50"
            show-password
            class="custom-input"
          />
        </el-form-item>
        <el-form-item label="所属项目" prop="projectId">
          <el-select
            v-model="formData.projectId"
            placeholder="请选择项目"
            filterable
            clearable
            class="custom-input"
            @change="handleProjectSelectChange"
          >
            <el-option
              v-for="project in projectOptions"
              :key="project.id"
              :label="project.projectName"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属队伍" prop="teamId">
          <el-select
            v-model="formData.teamId"
            placeholder="请选择队伍"
            filterable
            clearable
            class="custom-input"
            @change="handleTeamSelectChange"
          >
            <el-option
              v-for="team in teamOptions"
              :key="team.id"
              :label="team.teamName"
              :value="team.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <div class="footer-left">
            <el-tag v-if="drawerMode === 'edit'" type="info" size="large">
              代理ID: {{ formData.id }}
            </el-tag>
          </div>
          <div class="footer-right">
            <el-button @click="drawerVisible = false" class="cancel-btn">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving" class="save-btn">
              <el-icon><Check /></el-icon>保存
            </el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <!--详情抽屉-->
    <el-drawer
      v-model="detailDrawerVisible"
      title="代理详情"
      direction="rtl"
      size="800px"
      class="detail-drawer"
    >
      <el-descriptions :column="2" border v-if="currentProxyDetail">
        <el-descriptions-item label="代理ID">{{
          currentProxyDetail.id || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="代理服务器">{{
          currentProxyDetail.proxyServer || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="端口">{{
          currentProxyDetail.port || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="协议类型">
          <el-tag :type="getProtocolTag(currentProxyDetail.protocol)" effect="light">
            {{ getProtocolText(currentProxyDetail.protocol) || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="代理账号">{{
          currentProxyDetail.proxyAccount || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="代理密码">
          <span style="font-family: monospace">{{
            currentProxyDetail.proxyPassword ? '••••••' : '-'
          }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="所属项目">
          {{ getProjectDisplayName(currentProxyDetail) || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="所属队伍">
          {{ getTeamDisplayName(currentProxyDetail) || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="detailDrawerVisible = false">关闭</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Plus, Delete, View, Edit, Check, Upload } from '@element-plus/icons-vue'

// 导入API
import proxyApi from '@/api/services/proxy/proxy'
import teamApi from '@/api/services/team/team'
import { projectApi } from '@/api/services/project/project'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const total = ref(0)
const drawerVisible = ref(false)
const drawerTitle = ref('')
const drawerMode = ref('add')
const selectedRows = ref([])
const detailDrawerVisible = ref(false)
const currentProxyDetail = ref(null)
const formRef = ref()

// 队伍和项目数据
const allTeams = ref([])
const allProjects = ref([])

// 表单数据
const formData = reactive({
  id: '',
  proxyServer: '',
  port: '',
  protocol: '',
  proxyAccount: '',
  proxyPassword: '',
  projectId: '',
  teamId: '',
  projectName: '',
  teamName: '',
})

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  data: {
    proxyServer: '',
    protocol: '',
    projectId: '',
    teamId: '',
  },
  hasTimeRange: 0,
})

// 表单验证规则
const rules = {
  proxyServer: [{ required: true, message: '代理服务器不能为空', trigger: 'blur' }],
  port: [
    { required: true, message: '端口不能为空', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口必须在1-65535之间', trigger: 'blur' },
  ],
  protocol: [{ required: true, message: '协议类型不能为空', trigger: 'change' }],
}

// 上传headers
const uploadHeaders = reactive({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
})

// 计算属性
const projectOptions = computed(() => {
  return allProjects.value.map((project) => ({
    id: project.id,
    projectName: project.projectName || `项目${project.id}`,
  }))
})

const teamOptions = computed(() => {
  return allTeams.value.map((team) => ({
    id: team.id,
    teamName: team.teamName || `队伍${team.id}`,
  }))
})

// 协议类型标签映射
const getProtocolTag = (protocol) => {
  const protocolMap = {
    http: 'primary',
    https: 'success',
    socks5: 'warning',
  }
  return protocolMap[protocol] || 'info'
}

const getProtocolText = (protocol) => {
  const textMap = {
    http: 'HTTP',
    https: 'HTTPS',
    socks5: 'SOCKS5',
  }
  return textMap[protocol] || protocol
}

// 根据ID获取项目名称
const getProjectNameById = (projectId) => {
  if (!projectId) return ''
  const project = allProjects.value.find((p) => p.id === projectId)
  return project ? project.projectName : `项目${projectId}`
}

// 根据ID获取队伍名称
const getTeamNameById = (teamId) => {
  if (!teamId) return ''
  const team = allTeams.value.find((t) => t.id === teamId)
  return team ? team.teamName : `队伍${teamId}`
}

// 获取项目显示名称
const getProjectDisplayName = (row) => {
  return row.projectName || getProjectNameById(row.projectId) || '未分配'
}

// 获取队伍显示名称
const getTeamDisplayName = (row) => {
  return row.teamName || getTeamNameById(row.teamId) || '未分配'
}

// 项目选择变化处理
const handleProjectSelectChange = (projectId) => {
  const project = allProjects.value.find((p) => p.id === projectId)
  formData.projectName = project ? project.projectName : ''
}

// 队伍选择变化处理
const handleTeamSelectChange = (teamId) => {
  const team = allTeams.value.find((t) => t.id === teamId)
  formData.teamName = team ? team.teamName : ''
}

// 加载所有项目和队伍数据
const loadAllProjectsAndTeams = async () => {
  try {
    // 加载所有项目
    const projectParams = {
      page: 1,
      limit: 1000,
      data: {},
    }
    const projectResult = await projectApi.getPageList(projectParams)
    if (projectResult && projectResult.code === 200) {
      allProjects.value = projectResult.data || []
    }

    // 加载所有队伍
    const teamParams = {
      page: 1,
      limit: 1000,
      data: {},
    }
    const teamResult = await teamApi.getPageList(teamParams)
    if (teamResult && teamResult.code === 200) {
      allTeams.value = teamResult.data || []
    }
  } catch (error) {
    console.error('加载所有项目和队伍数据失败:', error)
  }
}

// 获取代理列表
const getPageList = async () => {
  loading.value = true
  try {
    const response = await proxyApi.getPageList(queryParams)
    if (response && response.code === 200) {
      // 处理数据，将ID转换为名称
      tableData.value = (response.data || []).map((item) => ({
        ...item,
        projectName: getProjectNameById(item.projectId),
        teamName: getTeamNameById(item.teamId),
      }))
      total.value = response.count || 0
    } else {
      tableData.value = []
      total.value = 0
      ElMessage.error(response?.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取代理列表失败:', error)
    ElMessage.error('获取数据失败')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 新增代理
const handleAdd = () => {
  drawerMode.value = 'add'
  drawerTitle.value = '新增代理'
  Object.keys(formData).forEach((key) => {
    if (key === 'port') {
      formData[key] = ''
    } else {
      formData[key] = ''
    }
  })
  drawerVisible.value = true
}

// 编辑代理
const handleEdit = async (row) => {
  drawerMode.value = 'edit'
  drawerTitle.value = '编辑代理'
  Object.keys(formData).forEach((key) => {
    if (row[key] !== undefined && row[key] !== null) {
      formData[key] = row[key]
    } else {
      formData[key] = ''
    }
  })
  drawerVisible.value = true
}

// 查看详情
const handleViewDetail = (row) => {
  currentProxyDetail.value = { ...row }
  detailDrawerVisible.value = true
}

// 保存代理
const handleSave = async () => {
  try {
    if (!formRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }

    await formRef.value.validate()
    saving.value = true

    // 准备提交数据
    const submitData = { ...formData }
    if (submitData.port) {
      submitData.port = Number(submitData.port)
    }
    if (submitData.projectId) {
      submitData.projectId = Number(submitData.projectId)
    }
    if (submitData.teamId) {
      submitData.teamId = Number(submitData.teamId)
    }

    let response
    if (drawerMode.value === 'edit') {
      response = await proxyApi.modify(submitData)
    } else {
      response = await proxyApi.add(submitData)
    }

    if (response && response.code === 200) {
      ElMessage.success(drawerMode.value === 'add' ? '新增成功' : '编辑成功')
      drawerVisible.value = false
      getPageList()
    } else {
      ElMessage.error(response?.message || '操作失败')
    }
  } catch (error) {
    console.error('保存代理失败:', error)
    ElMessage.error('保存失败:' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  queryParams.page = 1
  getPageList()
}

const handleImmediateSearch = () => {
  queryParams.page = 1
  getPageList()
}

const handleReset = () => {
  Object.assign(queryParams, {
    page: 1,
    limit: 20,
    data: {
      proxyServer: '',
      protocol: '',
      projectId: '',
      teamId: '',
    },
    hasTimeRange: 0,
  })
  getPageList()
}

const handleRefresh = () => {
  getPageList()
  ElMessage.success('数据已刷新')
}

// 表格选择变化
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 分页处理
const handleSizeChange = (newSize) => {
  queryParams.limit = newSize
  queryParams.page = 1
  getPageList()
}

const handleCurrentChange = (newPage) => {
  queryParams.page = newPage
  getPageList()
}

// 文件上传处理
const beforeUpload = (file) => {
  const isExcel =
    file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
    file.type === 'application/vnd.ms-excel'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isExcel) {
    ElMessage.error('只能上传Excel文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过10MB!')
    return false
  }
  return true
}

const handleImportSuccess = (response) => {
  if (response && response.code === 200) {
    ElMessage.success('导入成功')
    getPageList()
  } else {
    ElMessage.error(response?.message || '导入失败')
  }
}

const handleImportError = (error) => {
  console.error('导入失败:', error)
  ElMessage.error('导入失败:' + (error.message || '未知错误'))
}

// 批量删除
const handleBatchDelete = async () => {
  // 实现批量删除逻辑
}

// 单个删除
const handleDelete = async () => {
  // 实现单个删除逻辑
}

// 初始化
onMounted(() => {
  getPageList()
  loadAllProjectsAndTeams()
})
</script>

<style scoped lang="scss">
.proxy-management-container {
  background-color: #f5f7fa;
  min-height: calc(100vh - 84px);
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;

  :deep(.el-card__body) {
    padding: 20px;
  }
}

.operation-card {
  margin-bottom: 20px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;

  :deep(.el-card__body) {
    padding: 20px;
  }

  .operation-container {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .operation-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .operation-stats {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
}

.table-card {
  border-radius: 8px;
  border: 1px solid #e4e7ed;

  :deep(.el-card__body) {
    padding: 0;

    .proxy-table {
      :deep(.el-table__header) {
        th {
          background-color: #f8fafc;
          font-weight: 600;
          color: #374151;
          border-bottom: 2px solid #e5e7eb;
        }
      }

      :deep(.el-table__body) {
        tr:hover > td {
          background-color: #f3f4f6 !important;
        }
      }
    }
  }
}

.icon-actions {
  display: flex;
  gap: 12px;
  justify-content: left;
  align-items: center;
}

.pagination-container {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  background: #fff;
}

.proxy-drawer {
  :deep(.el-drawer) {
    box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);

    .el-drawer__header {
      padding: 24px;
      margin-bottom: 0;
      border-bottom: 1px solid #f0f0f0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;

      .el-drawer__title {
        font-weight: 600;
        font-size: 18px;
        color: white;
      }

      .el-drawer__close-btn {
        color: white;

        &:hover {
          color: #f0f0f0;
        }
      }
    }

    .el-drawer__body {
      padding: 24px;
      background: #f8fafc;
    }
  }
}

.custom-input {
  :deep(.el-input__wrapper) {
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    transition: all 0.3s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

    &:hover {
      border-color: #cbd5e0;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }

    &.is-focus {
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;

  .cancel-btn {
    border-radius: 8px;
    padding: 10px 24px;
    border: 1px solid #d1d5db;
    color: #6b7280;
    background-color: #ffffff;
    transition: all 0.3s ease;
    font-weight: 500;

    &:hover {
      border-color: #3b82f6;
      color: #3b82f6;
      background-color: #f0f9ff;
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
    }

    &:active {
      transform: translateY(0);
    }
  }

  .save-btn {
    border-radius: 8px;
    padding: 10px 24px;
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    border: none;
    color: #ffffff;
    font-weight: 500;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
      background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
    }

    &:active {
      transform: translateY(0);
    }

    &:disabled {
      background: #9ca3af;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;

      &:hover {
        background: #9ca3af;
        transform: none;
        box-shadow: none;
      }
    }
  }

  .footer-left {
    display: flex;
    align-items: center;
    gap: 12px;

    .el-tag {
      border-radius: 16px;
      font-weight: 500;
      padding: 4px 12px;

      &.el-tag--info {
        background: #f0f9ff;
        border-color: #e0f2fe;
        color: #0369a1;
      }
    }
  }
}

.detail-drawer {
  :deep(.el-drawer) {
    box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);

    .el-drawer__header {
      padding: 24px;
      margin-bottom: 0;
      border-bottom: 1px solid #f0f0f0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    .el-drawer__body {
      padding: 24px;
    }
  }
}

// 响应式适配
@media (max-width: 768px) {
  .proxy-management-container {
    padding: 16px;
  }

  .operation-container {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .proxy-drawer,
  .detail-drawer {
    :deep(.el-drawer) {
      width: 95% !important;

      .el-drawer__header {
        padding: 16px 20px;
      }

      .el-drawer__body {
        padding: 16px 20px;
      }
    }
  }
}

@media (max-width: 480px) {
  .proxy-management-container {
    padding: 8px;
  }

  .operation-container .operation-left {
    flex-direction: column;
    align-items: stretch;
  }

  .pagination-container {
    :deep(.el-pagination) {
      justify-content: center;

      .btn-prev,
      .btn-next,
      .el-pager li {
        min-width: 32px;
        height: 32px;
        line-height: 32px;
      }
    }
  }

  .icon-actions {
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px;

    .action-icon {
      width: 24px;
      height: 24px;
    }
  }
}

// 加载状态优化
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.8);

  .el-loading-spinner {
    path {
      stroke: #3b82f6;
    }
  }
}

// 表格行高亮效果
.highlight-row {
  background-color: #f0f9ff !important;

  td {
    background-color: #f0f9ff !important;
  }
}

// 状态标签动画
.status-tag {
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
}

// 图标悬停效果增强
.action-icon {
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    background: rgba(59, 130, 246, 0.1);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    transition: all 0.3s ease;
    z-index: -1;
  }

  &:hover::before {
    width: 40px;
    height: 40px;
  }

  &.delete-icon:hover::before {
    background: rgba(239, 68, 68, 0.1);
  }
}

// 表单样式优化
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #374151;
}

:deep(.el-textarea__inner) {
  border-radius: 6px;
}

:deep(.el-select) {
  width: 100%;
}

// 统计标签样式
.operation-stats {
  .el-tag {
    border-radius: 16px;
    font-weight: 500;

    &.el-tag--info {
      background: #f0f9ff;
      border-color: #e0f2fe;
      color: #0369a1;
    }

    &.el-tag--warning {
      background: #fffbeb;
      border-color: #fef3c7;
      color: #92400e;
    }
  }
}

// 卡片阴影优化
.search-card,
.operation-card,
.table-card {
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
  }
}

// 按钮组样式
.operation-left {
  .action-btn {
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
  }
}

// 分页器样式优化
.pagination-container {
  :deep(.el-pagination) {
    .btn-prev,
    .btn-next,
    .el-pager li {
      border-radius: 6px;
      margin: 0 2px;

      &:hover {
        color: #3b82f6;
      }

      &.active {
        background-color: #3b82f6;
        color: white;
      }
    }
  }
}

// 搜索表单响应式
@media (max-width: 768px) {
  .search-card {
    :deep(.el-form) {
      .el-form-item {
        width: 100%;
        margin-right: 0;

        .el-input,
        .el-select {
          width: 100% !important;
        }
      }
    }
  }
}

// 表格空状态
:deep(.el-table__empty-block) {
  padding: 40px 0;

  .el-table__empty-text {
    color: #9ca3af;
    font-size: 14px;
  }
}

// 加载状态文字
:deep(.el-loading-text) {
  color: #6b7280;
  margin-top: 8px;
}

// 已选资产标签样式
:deep(.el-tag) {
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
}

// 代理密码显示样式
.proxy-password {
  font-family: monospace;
  letter-spacing: 2px;
}

// 协议标签特殊样式
.protocol-tag {
  &.http {
    background: #ebf5ff;
    border-color: #bee3f8;
    color: #2b6cb0;
  }

  &.https {
    background: #f0fff4;
    border-color: #9ae6b4;
    color: #276749;
  }

  &.socks5 {
    background: #fffaf0;
    border-color: #fbd38d;
    color: #744210;
  }
}
</style>
