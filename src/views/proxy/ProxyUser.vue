<template>
  <div class="user-proxy-management-container">
    <!--搜索区域-->
    <el-card class="search-card" shadow="never">
      <el-form :model="queryParams" inline>
        <el-form-item label="代理账号">
          <el-input
            v-model="queryParams.data.proxyAccount"
            placeholder="请输入代理账号"
            clearable
            style="width: 220px"
            @input="handleSearch"
            @keyup.enter="handleImmediateSearch"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="外部代理">
          <el-select
            v-model="queryParams.data.proxyId"
            placeholder="请选择外部代理"
            clearable
            filterable
            style="width: 220px"
            @change="handleProxySelectChange"
          >
            <el-option
              v-for="proxy in proxyOptions"
              :key="proxy.id"
              :label="getProxyDisplayName(proxy)"
              :value="proxy.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select
            v-model="queryParams.data.projectId"
            placeholder="请选择项目"
            clearable
            filterable
            style="width: 220px"
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
        <el-form-item label="所属队伍">
          <el-select
            v-model="queryParams.data.teamId"
            placeholder="请选择队伍"
            clearable
            filterable
            style="width: 220px"
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
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>新增用户代理
          </el-button>
          <el-button
            :disabled="selectedRows.length === 0"
            @click="handleBatchDelete"
            class="action-btn"
          >
            <el-icon><Delete /></el-icon>批量删除
          </el-button>
          <el-upload
            action="/mgr/userProxy/import"
            :headers="uploadHeaders"
            :show-file-list="false"
            :before-upload="beforeUpload"
            :on-success="handleImportSuccess"
            :on-error="handleImportError"
          >
            <el-button type="success" class="action-btn">
              <el-icon><Upload /></el-icon>导入用户代理
            </el-button>
          </el-upload>
        </div>
        <div class="operation-stats">
          <el-tag type="info">共{{ total }}个用户代理</el-tag>
          <el-tag v-if="selectedRows.length > 0" type="warning">
            已选{{ selectedRows.length }}项
          </el-tag>
          <el-button @click="handleRefresh" :loading="loading">
            <el-icon><Refresh /></el-icon>刷新
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
        class="user-proxy-table"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column prop="id" label="ID" width="60" align="center" />

        <el-table-column prop="proxyAccount" label="代理账号" width="120" show-overflow-tooltip />
        <el-table-column prop="proxyPassword" label="代理密码" width="120" align="center">
          <template #default="{ row }">
            <span style="font-family: monospace; color: #666">
              {{ row.proxyPassword ? '●●●●●●' : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="port" label="端口" width="80" align="center" />

        <el-table-column prop="proxyName" label="外部代理" min-width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag :type="getProxyTagType(row)" effect="light">
              {{ row.proxyName || getProxyNameById(row.proxyId) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="serverApi" label="服务API" min-width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tooltip :content="row.serverApi" placement="top" v-if="row.serverApi">
              <span class="api-text">{{ formatApiUrl(row.serverApi) }}</span>
            </el-tooltip>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getStatusTagType(row.status)"
              effect="light"
              :style="{
                color: getStatusColor(row.status),
                borderColor: getStatusColor(row.status),
              }"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="projectName" label="所属项目" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag type="primary" effect="plain">
              {{ getProjectDisplayName(row) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="teamName" label="所属队伍" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag type="success" effect="plain">
              {{ getTeamDisplayName(row) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="userName" label="用户" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag type="info" effect="plain">
              {{ getUserDisplayName(row) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160" fixed="right" align="left">
          <template #default="{ row }">
            <div class="icon-actions">
              <el-tooltip content="查看详情" placement="top">
                <el-icon class="action-icon view-icon" @click="handleViewDetail(row)">
                  <View />
                </el-icon>
              </el-tooltip>
              <el-tooltip content="编辑" placement="top">
                <el-icon class="action-icon edit-icon" @click="handleEdit(row)">
                  <Edit />
                </el-icon>
              </el-tooltip>
              <el-tooltip v-if="row.status !== 'running'" content="启动代理" placement="top">
                <el-icon class="action-icon start-icon" @click="handleStart(row)">
                  <VideoPlay />
                </el-icon>
              </el-tooltip>
              <el-tooltip v-if="row.status === 'running'" content="停止代理" placement="top">
                <el-icon class="action-icon stop-icon" @click="handleStop(row)">
                  <VideoPause />
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
    <el-drawer
      v-if="detailDrawerVisible"
      v-model="detailDrawerVisible"
      title="用户代理详情"
      direction="rtl"
      size="800px"
      class="detail-drawer"
      :before-close="handleDetailClose"
    >
      <div class="detail-content" v-if="currentDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ currentDetail.id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="代理账号">{{
            currentDetail.proxyAccount || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="代理密码">
            <span style="font-family: monospace">
              {{ currentDetail.proxyPassword ? '●●●●●●' : '-' }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="端口">{{ currentDetail.port || '-' }}</el-descriptions-item>
          <el-descriptions-item label="外部代理">
            {{ getProxyNameById(currentDetail.proxyId) }}
          </el-descriptions-item>
          <el-descriptions-item label="服务API">
            <el-tooltip
              :content="currentDetail.serverApi"
              placement="top"
              v-if="currentDetail.serverApi"
            >
              <span class="api-text">{{ formatApiUrl(currentDetail.serverApi) }}</span>
            </el-tooltip>
            <span v-else>-</span>
          </el-descriptions-item>

          <!-- 新增：状态 -->
          <el-descriptions-item label="状态">
            <el-tag
              :type="getStatusTagType(currentDetail.status)"
              effect="light"
              :style="{
                color: getStatusColor(currentDetail.status),
                borderColor: getStatusColor(currentDetail.status),
              }"
            >
              {{ getStatusText(currentDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="所属项目">
            {{ getProjectDisplayName(currentDetail) }}
          </el-descriptions-item>
          <el-descriptions-item label="所属队伍">
            {{ getTeamDisplayName(currentDetail) }}
          </el-descriptions-item>
          <el-descriptions-item label="用户">
            {{ getUserDisplayName(currentDetail) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatTime(currentDetail.createTime) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatTime(currentDetail.updateTime) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 操作按钮 -->
        <div class="detail-actions" style="margin-top: 20px; text-align: center">
          <el-button
            v-if="currentDetail.status !== 'running'"
            type="success"
            @click="handleStart(currentDetail)"
          >
            <el-icon><VideoPlay /></el-icon>启动代理
          </el-button>
          <el-button
            v-if="currentDetail.status === 'running'"
            type="warning"
            @click="handleStop(currentDetail)"
          >
            <el-icon><VideoPause /></el-icon>停止代理
          </el-button>
          <el-button type="primary" @click="handleEdit(currentDetail)">
            <el-icon><Edit /></el-icon>编辑
          </el-button>
        </div>
      </div>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="detailDrawerVisible = false">关闭</el-button>
        </div>
      </template>
    </el-drawer>
    <!--新增/编辑抽屉-->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      direction="rtl"
      size="600px"
      class="user-proxy-drawer"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="外部代理" prop="proxyId">
          <el-select
            v-model="formData.proxyId"
            placeholder="请选择外部代理"
            filterable
            clearable
            class="custom-input"
            @change="handleProxySelectChange"
          >
            <el-option
              v-for="proxy in proxyOptions"
              :key="proxy.id"
              :label="getProxyDisplayName(proxy)"
              :value="proxy.id"
            />
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
        <el-form-item label="服务API" prop="serverApi">
          <el-input
            v-model="formData.serverApi"
            placeholder="请输入服务API地址，如：http://api.example.com"
            maxlength="500"
            class="custom-input"
            :rows="2"
            type="textarea"
          />
          <div class="form-tip">请输入完整的API地址，包含协议头（http:// 或 https://）</div>
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

        <el-form-item label="用户" prop="userId">
          <el-select
            v-model="formData.userId"
            placeholder="请选择用户"
            filterable
            clearable
            class="custom-input"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="getUserDisplayLabel(user)"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <div class="footer-left">
            <el-tag v-if="drawerMode === 'edit'" type="info" size="large">
              用户代理ID: {{ formData.id }}
            </el-tag>
          </div>
          <div class="footer-right">
            <el-button @click="drawerVisible = false" class="cancel-btn">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving" class="save-btn">
              <el-icon><Check /></el-icon>{{ drawerMode === 'add' ? '新增' : '更新' }}
            </el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Refresh, Edit, Check, Upload } from '@element-plus/icons-vue'

// 导入API
import userProxyApi from '@/api/services/proxy/proxyUser'
import proxyApi from '@/api/services/proxy/proxy'
import { projectApi } from '@/api/services/project/project'
import teamApi from '@/api/services/team/team'
import userApi from '@/api/services/system/user'

// 响应式数据
const isMounted = ref(false)
const loading = ref(false)
const saving = ref(false)
const drawerVisible = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedRows = ref([])
const formRef = ref()
const proxyList = ref([])
const projectList = ref([])
const teamList = ref([])
const userList = ref([])
const currentDetail = ref(null)
const detailDrawerVisible = ref(false)

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  data: {
    // 添加 data 属性
    proxyAccount: '',
    proxyId: '',
    projectId: '',
    teamId: '',
    userId: '',
    serverApi: '',
    status: '',
  },
})

// 表单数据
const formData = reactive({
  id: '',
  proxyId: '',
  proxyAccount: '',
  proxyPassword: '',
  port: '',
  projectId: '',
  teamId: '',
  userId: '',
  serverApi: '', // 新增字段
  status: 'stopped',
})
// 状态映射
const statusMap = {
  running: { text: '运行中', type: 'success', color: '#67c23a' },
  stopped: { text: '已停止', type: 'info', color: '#909399' },
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  return statusMap[status]?.type || 'info'
}

// 获取状态显示文本
const getStatusText = (status) => {
  return statusMap[status]?.text || status || '未知'
}

// 获取状态颜色
const getStatusColor = (status) => {
  return statusMap[status]?.color || '#909399'
}
const formatTime = (time) => {
  if (!time) return '-'
  try {
    // 如果是时间戳
    if (typeof time === 'number') {
      return new Date(time).toLocaleString('zh-CN')
    }
    // 如果是字符串
    if (typeof time === 'string') {
      // 尝试解析日期字符串
      const date = new Date(time)
      if (!isNaN(date.getTime())) {
        return date.toLocaleString('zh-CN')
      }
      // 如果无法解析，返回原字符串
      return time
    }
    return '-'
  } catch (error) {
    console.warn('时间格式化失败:', time, error)
    return time || '-'
  }
}

const safeAsyncOperation = async (asyncFn) => {
  if (!isMounted.value) {
    console.warn('组件已卸载，取消操作')
    return
  }
  return await asyncFn()
}
const handleViewDetail = async (row) => {
  return safeAsyncOperation(async () => {
    try {
      loading.value = true
      const result = await userProxyApi.getInfo({ id: row.id })

      if (result && result.code === 200) {
        currentDetail.value = result.data
        detailDrawerVisible.value = true
      } else {
        ElMessage.error(result?.message || '获取详情失败')
      }
    } catch (error) {
      console.error('获取详情失败:', error)
      if (!error.message?.includes('cancel')) {
        ElMessage.error('获取详情失败')
      }
    } finally {
      loading.value = false
    }
  })
}
const handleDetailClose = (done) => {
  // 异步清理数据
  nextTick(() => {
    currentDetail.value = null
    done()
  })
}
// 启动代理
const handleStart = async (row) => {
  await safeAsyncOperation(async () => {
    try {
      await ElMessageBox.confirm(`确定要启动用户代理 "${row.proxyAccount}" 吗？`, '启动确认', {
        type: 'warning',
        confirmButtonText: '确定启动',
        cancelButtonText: '取消',
      })

      const result = await userProxyApi.start({ id: row.id })
      if (result && result.code === 200) {
        ElMessage.success('启动成功')
        getPageList()
      } else {
        ElMessage.error(result?.message || '启动失败')
      }
    } catch {
      // 用户取消，不报错
    }
  }, '启动代理')
}

// 停止代理
const handleStop = async (row) => {
  await safeAsyncOperation(async () => {
    try {
      await ElMessageBox.confirm(`确定要停止用户代理 "${row.proxyAccount}" 吗？`, '停止确认', {
        type: 'warning',
        confirmButtonText: '确定停止',
        cancelButtonText: '取消',
      })

      const result = await userProxyApi.stop({ id: row.id })
      if (result && result.code === 200) {
        ElMessage.success('停止成功')
        getPageList()
      } else {
        ElMessage.error(result?.message || '停止失败')
      }
    } catch {
      // 用户取消，不报错
    }
  }, '停止代理')
}

// 抽屉模式
const drawerMode = ref('add')
const drawerTitle = computed(() => (drawerMode.value === 'add' ? '新增用户代理' : '编辑用户代理'))

// 表单验证规则
const rules = {
  proxyId: [{ required: true, message: '请选择外部代理', trigger: 'change' }],
  proxyAccount: [{ required: true, message: '请输入代理账号', trigger: 'blur' }],
  proxyPassword: [{ required: true, message: '请输入代理密码', trigger: 'blur' }],
  serverApi: [
    {
      required: true,
      message: '请输入服务API',
      trigger: 'blur',
    },
    {
      validator: (rule, value, callback) => {
        if (value && !validateApiUrl(value)) {
          callback(new Error('请输入有效的API地址（http:// 或 https:// 开头）'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口必须在1-65535之间', trigger: 'blur' },
  ],
  projectId: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  teamId: [{ required: true, message: '请选择所属队伍', trigger: 'change' }],
  userId: [{ required: true, message: '请选择用户', trigger: 'change' }],
}

// 上传headers
const uploadHeaders = reactive({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
})

// 计算属性
const proxyOptions = computed(() => proxyList.value)
const projectOptions = computed(() => projectList.value)
const teamOptions = computed(() => teamList.value)
const userOptions = computed(() => userList.value)

// 获取代理显示名称
const getProxyDisplayName = (proxy) => {
  if (!proxy) return '未知代理'
  return `${proxy.proxyServer}:${proxy.port} (${proxy.protocol?.toUpperCase()})`
}

// 根据代理ID获取代理名称
const getProxyNameById = (proxyId) => {
  if (!proxyId) return '未知代理'
  const proxy = proxyList.value.find((p) => p.id === proxyId)
  return proxy ? getProxyDisplayName(proxy) : `代理${proxyId}`
}

// 获取代理标签类型
const getProxyTagType = (row) => {
  const proxy = proxyList.value.find((p) => p.id === row.proxyId)
  if (!proxy) return 'info'

  const protocolMap = {
    http: 'primary',
    https: 'success',
    socks5: 'warning',
  }
  return protocolMap[proxy.protocol] || 'info'
}

// 获取项目显示名称
const getProjectDisplayName = (row) => {
  if (row.projectName) return row.projectName
  const project = projectList.value.find((p) => p.id === row.projectId)
  return project ? project.projectName : row.projectId ? `项目${row.projectId}` : '未分配'
}

// 获取队伍显示名称
const getTeamDisplayName = (row) => {
  if (row.teamName) return row.teamName
  const team = teamList.value.find((t) => t.id === row.teamId)
  return team ? team.teamName : row.teamId ? `队伍${row.teamId}` : '未分配'
}

// 获取用户显示名称
const getUserDisplayName = (row) => {
  if (row.userName) return row.userName
  const user = userList.value.find((u) => u.id === row.userId)
  return user ? user.userName || user.nickName : row.userId ? `用户${row.userId}` : '未分配'
}

// 获取用户显示标签
const getUserDisplayLabel = (user) => {
  if (!user) return '未知用户'
  return user.userName || user.nickName || `用户${user.id}`
}

// 加载代理列表
const loadProxyList = async () => {
  try {
    const result = await proxyApi.getPageList({
      page: 1,
      limit: 1000,
      data: {},
    })
    if (result && result.code === 200) {
      proxyList.value = result.data || []
    }
  } catch (error) {
    console.error('加载代理列表失败:', error)
    proxyList.value = []
  }
}

// 加载项目列表
const loadProjectList = async () => {
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
    console.error('加载项目列表失败:', error)
    projectList.value = []
  }
}

// 加载队伍列表
const loadTeamList = async () => {
  try {
    const result = await teamApi.getPageList({
      page: 1,
      limit: 1000,
      data: {},
    })
    if (result && result.code === 200) {
      teamList.value = result.data || []
    }
  } catch (error) {
    console.error('加载队伍列表失败:', error)
    teamList.value = []
  }
}

// 加载用户列表
const loadUserList = async () => {
  try {
    const result = await userApi.getPageList({
      page: 1,
      limit: 1000,
      data: {},
    })
    if (result && result.code === 200) {
      userList.value = result.data || []
    }
  } catch (error) {
    console.error('加载用户列表失败:', error)
    userList.value = []
  }
}

const getPageList = async () => {
  loading.value = true
  try {
    const result = await userProxyApi.getPageList(queryParams)
    if (result && result.code === 200) {
      // 处理数据，添加显示名称
      tableData.value = (result.data || []).map((item) => ({
        ...item,
        proxyName: getProxyNameById(item.proxyId),
        projectName: getProjectDisplayName(item),
        teamName: getTeamDisplayName(item),
        userName: getUserDisplayName(item),
        // 确保状态字段存在
      }))
      total.value = result.count || 0
    } else {
      tableData.value = []
      total.value = 0
      ElMessage.error(result?.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}
onMounted(() => {
  isMounted.value = true
  console.log('组件已挂载')

  // 初始化数据
  Promise.all([loadProxyList(), loadProjectList(), loadTeamList(), loadUserList()]).then(() => {
    if (isMounted.value) {
      getPageList()
    }
  })
})

onUnmounted(() => {
  isMounted.value = false
  console.log('组件已卸载')
})
// 新增用户代理
const handleAdd = () => {
  drawerMode.value = 'add'
  Object.keys(formData).forEach((key) => {
    if (key === 'port') {
      formData[key] = ''
    } else {
      formData[key] = ''
    }
  })
  drawerVisible.value = true
}

// 编辑用户代理
const handleEdit = (row) => {
  drawerMode.value = 'edit'
  Object.keys(formData).forEach((key) => {
    if (row[key] !== undefined && row[key] !== null) {
      formData[key] = row[key]
    } else {
      formData[key] = ''
    }
  })
  drawerVisible.value = true
}

// 保存用户代理
const handleSave = async () => {
  try {
    if (!formRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }

    await formRef.value.validate()
    saving.value = true

    const submitData = { ...formData }
    if (submitData.port) {
      submitData.port = Number(submitData.port)
    }

    let result
    if (drawerMode.value === 'edit') {
      result = await userProxyApi.modify(submitData)
    } else {
      result = await userProxyApi.add(submitData)
    }

    if (result && result.code === 200) {
      ElMessage.success(drawerMode.value === 'add' ? '新增成功' : '编辑成功')
      drawerVisible.value = false
      getPageList()
    } else {
      ElMessage.error(result?.message || '操作失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败:' + error.message)
  } finally {
    saving.value = false
  }
}
// API地址格式化函数
const formatApiUrl = (url) => {
  if (!url) return '-'
  // 简化显示，只显示域名部分
  try {
    const urlObj = new URL(url)
    return `${urlObj.protocol}//${urlObj.hostname}${urlObj.port ? ':' + urlObj.port : ''}`
  } catch {
    // 如果不是标准URL，显示前30个字符
    return url.length > 30 ? url.substring(0, 30) + '...' : url
  }
}

// 验证API地址
const validateApiUrl = (url) => {
  if (!url) return false
  try {
    new URL(url)
    return url.startsWith('http://') || url.startsWith('https://')
  } catch {
    return false
  }
}
// 删除用户代理
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个用户代理吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })

    const result = await userProxyApi.batchRemove([id])
    if (result && result.code === 200) {
      ElMessage.success('删除成功')
      getPageList()
    } else {
      ElMessage.error(result?.message || '删除失败')
    }
  } catch {
    // 用户取消
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要删除的用户代理')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个用户代理吗？`,
      '批量删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      },
    )

    const ids = selectedRows.value.map((item) => item.id)
    const result = await userProxyApi.batchRemove(ids)
    if (result && result.code === 200) {
      ElMessage.success(`成功删除 ${selectedRows.value.length} 个用户代理`)
      selectedRows.value = []
      getPageList()
    } else {
      ElMessage.error(result?.message || '删除失败')
    }
  } catch {
    // 用户取消
  }
}

// 搜索处理
const handleSearch = () => {
  queryParams.page = 1
  getPageList()
}

const handleImmediateSearch = () => {
  handleSearch()
}

const handleReset = () => {
  Object.assign(queryParams, {
    page: 1,
    limit: 20,
    data: {
      proxyAccount: '',
      proxyId: '',
      projectId: '',
      serverApi: '', // 新增
      status: '', // 新增
      teamId: '',
      userId: '',
    },
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

// 选择变化处理
const handleProxySelectChange = (proxyId) => {
  // 实际使用proxyId参数
  console.log('选择的代理ID:', proxyId)
}

const handleProjectSelectChange = (projectId) => {
  // 记录选择日志
  console.log('选择的项目ID:', projectId)
}

const handleTeamSelectChange = (teamId) => {
  // 记录选择日志
  console.log('选择的队伍ID:', teamId)
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

// 初始化
onMounted(async () => {
  // 并行加载所有数据
  await Promise.all([loadProxyList(), loadProjectList(), loadTeamList(), loadUserList()])
  getPageList()
})
</script>

<style scoped lang="scss">
.user-proxy-management-container {
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
  }
}

.pagination-container {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  background: #fff;
}

.icon-actions {
  display: flex;
  gap: 12px;
  justify-content: left;
  align-items: center;
}

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
}

.el-drawer__body {
  padding: 24px;
  background: #f8fafc;
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

    &:disabled {
      background: #9ca3af;
      cursor: not-allowed;
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

// 响应式适配
@media (max-width: 768px) {
  .user-proxy-management-container {
    padding: 16px;
  }

  .operation-container {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .user-proxy-drawer {
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
  .user-proxy-management-container {
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
.api-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  color: #409eff;
  cursor: pointer;
  word-break: break-all;
}

.api-text:hover {
  text-decoration: underline;
}

.no-data {
  color: #c0c4cc;
  font-style: italic;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 状态标签样式 */
.status-running {
  background-color: #f0f9ff;
  border-color: #a0cfff;
  color: #409eff;
}

.status-stopped {
  background-color: #f4f4f5;
  border-color: #d3d4d6;
  color: #909399;
}
</style>
