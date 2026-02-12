<template>
  <div class="penalty-score-container">
    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="main-filters">
        <!-- 关键词搜索 -->
        <el-input
          v-model="filterParams.keyword"
          placeholder="搜索队伍/项目"
          clearable
          @input="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        />

        <!-- 时间筛选 -->
        <div class="time-filter-group">
          <el-select
            v-model="selectedTimeField"
            placeholder="更新时间"
            class="time-field-select"
            style="width: 120px"
            @change="handleTimeFieldChange"
          >
            <el-option label="更新时间" value="updateTime" />
            <el-option label="创建时间" value="createTime" />
          </el-select>
          <TimeRangePicker
            v-model:time-field="selectedTimeField"
            :immediate="true"
            show-time-field="false"
            class="time-range-picker"
            @change="handleTimeRangeChange"
            @confirm="handleTimeConfirm"
            @clear="handleTimeClear"
          />
        </div>

        <!-- 操作按钮 -->
        <el-button-group class="action-buttons">
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
          <el-button @click="showMoreFilters = !showMoreFilters">
            <el-icon><Filter /></el-icon>{{ showMoreFilters ? '收起' : '更多' }}
          </el-button>
        </el-button-group>
      </div>

      <!-- 更多筛选 -->
      <el-collapse-transition>
        <div v-show="showMoreFilters" class="advanced-filters">
          <el-row :gutter="16">
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.teamId"
                placeholder="队伍ID"
                type="number"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.projectId"
                placeholder="项目ID"
                type="number"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-select
                v-model="filterParams.penaltyType"
                placeholder="扣分类型"
                clearable
                @change="handleSearch"
                class="filter-item"
              >
                <el-option label="技术违规" value="technical" />
                <el-option label="行为违规" value="behavior" />
                <el-option label="安全违规" value="security" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-select
                v-model="filterParams.status"
                placeholder="状态"
                clearable
                @change="handleSearch"
                class="filter-item"
              >
                <el-option label="待处理" value="pending" />
                <el-option label="已确认" value="confirmed" />
                <el-option label="已撤销" value="cancelled" />
              </el-select>
            </el-col>
          </el-row>
        </div>
      </el-collapse-transition>
    </div>

    <el-card class="table-card">
      <!-- 表格操作区域 -->
      <div class="table-actions">
        <el-button-group>
          <el-button type="primary" @click="handleAddPenalty">
            <el-icon><Plus /></el-icon>新增扣分
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

      <!-- 数据表格 -->
      <el-table
        :data="tableData"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        border
        stripe
        style="width: 100%; margin-top: 16px"
        key="penalty-table"
      >
        <!-- 选择列 -->
        <el-table-column type="selection" width="50" align="center" />
        <!-- 队伍名称 -->
        <el-table-column prop="teamName" label="队伍名称" min-width="180" align="center">
          <template #default="{ row }">
            {{ getTeamName(row.teamId) || '-' }}
          </template>
        </el-table-column>

        <!-- 队伍类型 -->
        <el-table-column prop="teamType" label="队伍类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getTeamTypeTag(row.teamType)">
              {{ getTeamTypeText(row.teamType) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 项目名称 -->
        <el-table-column prop="projectName" label="项目名称" min-width="180" align="center">
          <template #default="{ row }">
            {{ getProjectName(row.projectId) || '-' }}
          </template>
        </el-table-column>

        <!-- 扣分类型 -->
        <el-table-column prop="penaltyType" label="扣分类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getPenaltyTypeTag(row.penaltyType)" effect="light">
              {{ getPenaltyTypeText(row.penaltyType) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 扣分分值 -->
        <el-table-column prop="penaltyScore" label="扣分分值" width="100" align="center">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: bold">-{{ row.penaltyScore }}</span>
          </template>
        </el-table-column>

        <!-- 简要原因 -->
        <el-table-column
          prop="briefReason"
          label="简要原因"
          min-width="200"
          show-overflow-tooltip
        />

        <!-- 详细原因 -->
        <el-table-column
          prop="penaltyReason"
          label="详细原因"
          min-width="250"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span v-if="row.penaltyReason" class="text-ellipsis" :title="row.penaltyReason">
              {{ row.penaltyReason }}
            </span>
            <span v-else class="text-muted">暂无说明</span>
          </template>
        </el-table-column>

        <!-- 状态 -->
        <el-table-column prop="status" label="状态" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="light">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 创建时间 -->
        <el-table-column prop="createTime" label="创建时间" width="160" align="center" sortable>
          <template #default="{ row }">
            <el-tooltip :content="formatFullTime(row.createTime)" placement="top">
              <span>{{ formatTimeAgo(row.createTime) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="icon-actions">
              <!-- 查看详情 -->
              <el-tooltip content="查看详情" placement="top">
                <el-icon class="action-icon view-icon" @click="handleViewDetail(row)">
                  <View />
                </el-icon>
              </el-tooltip>
              <!-- 编辑 -->
              <el-tooltip content="编辑" placement="top">
                <el-icon
                  v-if="row.status === 'pending'"
                  class="action-icon edit-icon"
                  @click="handleEditPenalty(row)"
                >
                  <Edit />
                </el-icon>
              </el-tooltip>
              <!-- 确认 -->
              <el-tooltip content="确认" placement="top">
                <el-icon
                  v-if="row.status === 'pending'"
                  class="action-icon confirm-icon"
                  @click="handleConfirmPenalty(row)"
                >
                  <Check />
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
    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      direction="rtl"
      size="50%"
      class="penalty-drawer"
      :close-on-click-modal="true"
    >
      <div class="drawer-content" v-if="drawerVisible">
        <el-card shadow="never" class="form-section">
          <template #header>
            <div class="card-header">
              <span>扣分信息</span>
            </div>
          </template>
          <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="队伍" prop="teamId" required>
                  <el-select
                    v-model="formData.teamId"
                    placeholder="请选择队伍"
                    filterable
                    clearable
                    @change="handleTeamChange"
                  >
                    <el-option
                      v-for="team in teamList"
                      :key="team.id"
                      :label="team.teamName"
                      :value="team.id"
                    >
                      <div>
                        <div>{{ team.teamName }}</div>
                        <div style="font-size: 12px; color: #909399">
                          {{ team.teamShortName }} - {{ getTeamTypeText(team.teamType) }}
                        </div>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="队伍类型" prop="teamType" required>
                  <el-select v-model="formData.teamType" placeholder="请选择队伍类型">
                    <el-option label="攻击队伍" value="attack" />
                    <el-option label="防守队伍" value="defense" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="项目" prop="projectId">
                  <el-select
                    v-model="formData.projectId"
                    placeholder="请选择项目"
                    filterable
                    clearable
                  >
                    <el-option
                      v-for="project in projectList"
                      :key="project.id"
                      :label="project.projectName"
                      :value="project.id"
                    >
                      <div>
                        <div>{{ project.projectName }}</div>
                        <div style="font-size: 12px; color: #909399">
                          {{ project.organization }} - {{ project.status }}
                        </div>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="扣分类型" prop="penaltyType" required>
                  <el-select v-model="formData.penaltyType" placeholder="请选择扣分类型">
                    <el-option label="技术违规" value="technical" />
                    <el-option label="行为违规" value="behavior" />
                    <el-option label="安全违规" value="security" />
                    <el-option label="其他" value="other" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="扣分分值" prop="penaltyScore" required>
                  <el-input
                    v-model.number="formData.penaltyScore"
                    placeholder="请输入扣分分值"
                    type="number"
                    clearable
                  >
                    <template #prefix>-</template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="状态" prop="status">
                  <el-select v-model="formData.status" placeholder="请选择状态">
                    <el-option label="待处理" value="pending" />
                    <el-option label="已确认" value="confirmed" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="简要原因" prop="briefReason" required>
              <el-input
                v-model="formData.briefReason"
                placeholder="请输入简要原因"
                maxlength="100"
                show-word-limit
                clearable
              />
            </el-form-item>

            <el-form-item label="详细原因" prop="penaltyReason">
              <el-input
                v-model="formData.penaltyReason"
                type="textarea"
                :rows="4"
                placeholder="请输入详细原因说明"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </el-card>
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
      :title="`扣分详情 - ID: ${currentDetail?.id || '未知'}`"
      direction="rtl"
      size="60%"
      class="detail-drawer"
    >
      <div class="detail-content" v-if="currentDetail">
        <div class="detail-header">
          <h2>扣分详情</h2>
        </div>
        <el-card shadow="never" class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="扣分 ID">{{
              currentDetail.id || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="队伍名称">{{
              getTeamName(currentDetail.teamId) || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="队伍类型">
              <el-tag :type="getTeamTypeTag(currentDetail.teamType)">
                {{ getTeamTypeText(currentDetail.teamType) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="项目名称">{{
              getProjectName(currentDetail.projectId) || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="扣分类型">
              <el-tag :type="getPenaltyTypeTag(currentDetail.penaltyType)">
                {{ getPenaltyTypeText(currentDetail.penaltyType) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="扣分分值">
              <span style="color: #f56c6c; font-weight: bold"
                >-{{ currentDetail.penaltyScore || 0 }}</span
              >
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(currentDetail.status)">
                {{ getStatusText(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{
              formatFullTime(currentDetail.createTime)
            }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{
              formatFullTime(currentDetail.updateTime)
            }}</el-descriptions-item>
            <el-descriptions-item label="简要原因" :span="2">{{
              currentDetail.briefReason || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="详细原因" :span="2">{{
              currentDetail.penaltyReason || '无'
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </el-drawer>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Refresh, Filter, View, Edit, Check } from '@element-plus/icons-vue'
import TimeRangePicker from '@/components/TimeRangePicker.vue'
import { penaltyScoreApi } from '@/api/services/panaltyscore/panaltyScore'
import teamApi from '@/api/services/team/team' // 导入队伍接口
import { projectApi } from '@/api/services/project/project' // 导入项目接口

// 状态
const loading = ref(false)
const saving = ref(false)
const showMoreFilters = ref(false)
const drawerVisible = ref(false)
const detailVisible = ref(false)
const tableData = ref([])
const selectedRows = ref([])
const formRef = ref()

// 队伍和项目列表
const teamList = ref([])
const projectList = ref([])

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

// 筛选参数
const filterParams = reactive({
  keyword: '',
  teamId: '',
  projectId: '',
  penaltyType: '',
  status: '',
})

// 时间筛选
const selectedTimeField = ref('updateTime')
const searchTimeRange = reactive({
  hasTimeRange: 0,
  timeField: 'updateTime',
  minTime: '',
  maxTime: '',
})

// 抽屉模式
const drawerMode = ref('add') // 'add' | 'edit'
const drawerTitle = computed(() => (drawerMode.value === 'add' ? '新增扣分' : '编辑扣分'))

// 表单数据
const formData = reactive({
  teamId: '',
  teamType: '',
  projectId: '',
  penaltyType: '',
  penaltyScore: 0,
  briefReason: '',
  penaltyReason: '',
  status: 'pending',
})

// 表单验证规则
const formRules = {
  teamId: [{ required: true, message: '请选择队伍', trigger: 'change' }],
  teamType: [{ required: true, message: '请选择队伍类型', trigger: 'change' }],
  penaltyType: [{ required: true, message: '请选择扣分类型', trigger: 'change' }],
  penaltyScore: [{ required: true, message: '请输入扣分分值', trigger: 'blur' }],
  briefReason: [{ required: true, message: '请输入简要原因', trigger: 'blur' }],
}

// 当前操作的数据
const currentDetail = ref(null)

// 获取队伍列表
const fetchTeamList = async () => {
  try {
    const result = await teamApi.getPageList({
      page: 1,
      limit: 1000, // 获取所有队伍
      data: {},
    })
    if (result && result.code === 200) {
      teamList.value = result.data || []
    }
  } catch (error) {
    console.error('获取队伍列表失败:', error)
    ElMessage.error('获取队伍列表失败')
  }
}

// 获取项目列表
const fetchProjectList = async () => {
  try {
    const result = await projectApi.getPageList({
      page: 1,
      limit: 1000, // 获取所有项目
      data: {},
    })
    if (result && result.code === 200) {
      projectList.value = result.data || []
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
    ElMessage.error('获取项目列表失败')
  }
}

// 根据队伍ID获取队伍名称
const getTeamName = (teamId) => {
  const team = teamList.value.find((item) => item.id === teamId)
  return team ? team.teamName : ''
}

// 根据项目ID获取项目名称
const getProjectName = (projectId) => {
  const project = projectList.value.find((item) => item.id === projectId)
  return project ? project.projectName : ''
}

// 队伍选择变化时自动填充队伍类型
const handleTeamChange = (teamId) => {
  const selectedTeam = teamList.value.find((team) => team.id === teamId)
  if (selectedTeam) {
    formData.teamType = selectedTeam.teamType
  }
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      limit: pagination.pageSize,
      data: { ...filterParams },
    }
    const result = await penaltyScoreApi.getPageList(params)
    if (result && result.code === 200) {
      tableData.value = result.data || []
      pagination.total = result.total || 0
    } else {
      tableData.value = []
      pagination.total = 0
      ElMessage.warning('获取数据失败')
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败:' + error.message)
  } finally {
    loading.value = false
  }
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

// 时间筛选
const handleTimeFieldChange = (value) => {
  selectedTimeField.value = value
  handleSearch()
}

const handleTimeRangeChange = (timeData) => {
  if (timeData && timeData.startTime && timeData.endTime) {
    searchTimeRange.hasTimeRange = 1
    searchTimeRange.minTime = timeData.startStr
    searchTimeRange.maxTime = timeData.endStr
    handleSearch()
  } else {
    searchTimeRange.hasTimeRange = 0
    handleSearch()
  }
}

const handleTimeConfirm = (timeData) => {
  console.log('时间确认:', timeData)
}

const handleTimeClear = () => {
  searchTimeRange.hasTimeRange = 0
  handleSearch()
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

// 新增扣分
const handleAddPenalty = () => {
  drawerMode.value = 'add'
  // 重置表单数据
  Object.keys(formData).forEach((key) => {
    formData[key] = ''
  })
  formData.penaltyScore = 0
  formData.status = 'pending'
  drawerVisible.value = true
}

// 编辑扣分
const handleEditPenalty = (row) => {
  drawerMode.value = 'edit'
  currentDetail.value = row
  // 填充表单数据
  Object.keys(formData).forEach((key) => {
    if (row[key] !== undefined) {
      formData[key] = row[key]
    }
  })
  drawerVisible.value = true
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    const result = await penaltyScoreApi.getInfo({ id: row.id })
    currentDetail.value = result.data || result
    detailVisible.value = true
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取详情失败:' + error.message)
  }
}

// 确认扣分
const handleConfirmPenalty = async (row) => {
  try {
    await ElMessageBox.confirm('确定确认此扣分记录吗?', '确认扣分', {
      type: 'warning',
      confirmButtonText: '确定确认',
      cancelButtonText: '取消',
    })

    const result = await penaltyScoreApi.confirm({
      id: row.id,
      status: 'confirmed',
    })

    if (result && result.code === 200) {
      ElMessage.success('扣分确认成功')
      fetchData()
    } else {
      ElMessage.error(result?.message || '确认失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('确认失败:' + error.message)
    }
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除扣分记录吗?', '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await penaltyScoreApi.batchRemove([row.id])
    if (result && result.code === 200) {
      ElMessage.success('删除成功')
      fetchData()
    } else {
      ElMessage.error(result?.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败:' + error.message)
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要删除的扣分记录')
    return
  }

  try {
    const ids = selectedRows.value.map((item) => item.id)
    await ElMessageBox.confirm(`确定删除选中的${ids.length}条扣分记录吗?`, '批量删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await penaltyScoreApi.batchRemove(ids)
    if (result && result.code === 200) {
      ElMessage.success(`成功删除${ids.length}条扣分记录`)
      selectedRows.value = []
      fetchData()
    } else {
      ElMessage.error(result?.message || '批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败:' + error.message)
    }
  }
}

// 保存
const handleSave = async () => {
  try {
    saving.value = true

    // 表单验证
    if (!formRef.value) return
    const valid = await formRef.value.validate()
    if (!valid) return

    const saveData = {
      teamId: Number(formData.teamId),
      teamType: formData.teamType,
      projectId: Number(formData.projectId),
      penaltyType: formData.penaltyType,
      penaltyScore: Number(formData.penaltyScore),
      briefReason: formData.briefReason.trim(),
      penaltyReason: formData.penaltyReason?.trim() || '',
      status: formData.status,
    }

    // 如果是编辑模式，添加ID
    if (drawerMode.value === 'edit' && currentDetail.value?.id) {
      saveData.id = currentDetail.value.id
    }

    let result
    if (drawerMode.value === 'edit') {
      result = await penaltyScoreApi.modify(saveData)
    } else {
      result = await penaltyScoreApi.add(saveData)
    }

    if (result && result.code === 200) {
      ElMessage.success(drawerMode.value === 'add' ? '创建成功' : '更新成功')
      drawerVisible.value = false
      fetchData()
    } else {
      const errorMsg = result?.message || '保存失败'
      ElMessage.error(`保存失败: ${errorMsg}`)
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败:' + error.message)
  } finally {
    saving.value = false
  }
}

// 状态处理函数
const getStatusType = (status) => {
  const typeMap = {
    pending: 'warning',
    confirmed: 'success',
    cancelled: 'info',
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    pending: '待处理',
    confirmed: '已确认',
    cancelled: '已撤销',
  }
  return textMap[status] || status
}

const getTeamTypeTag = (teamType) => {
  const typeMap = {
    attack: 'danger',
    defense: 'primary',
  }
  return typeMap[teamType] || 'info'
}

const getTeamTypeText = (teamType) => {
  const textMap = {
    attack: '攻击队伍',
    defense: '防守队伍',
  }
  return textMap[teamType] || teamType
}

const getPenaltyTypeTag = (penaltyType) => {
  const typeMap = {
    technical: 'warning',
    behavior: 'danger',
    security: 'error',
    other: 'info',
  }
  return typeMap[penaltyType] || 'info'
}

const getPenaltyTypeText = (penaltyType) => {
  const textMap = {
    technical: '技术违规',
    behavior: '行为违规',
    security: '安全违规',
    other: '其他',
  }
  return textMap[penaltyType] || penaltyType
}

const formatTimeAgo = (timeStr) => {
  if (!timeStr) return '-'
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    if (diffDays < 30) return `${diffDays}天前`
    return date.toLocaleDateString('zh-CN')
  } catch {
    return timeStr
  }
}

const formatFullTime = (timeStr) => {
  if (!timeStr) return '-'
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return timeStr
  }
}

// 初始化
onMounted(() => {
  fetchTeamList()
  fetchProjectList()
  fetchData()
})
</script>

<style scoped lang="scss">
.penalty-score-container {
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
}

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
  }

  .time-field-select {
    width: 120px;
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
    transition: all 0.3s;

    &:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
  }
}

.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.table-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-right-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  margin-top: 20px;
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  background: #fff;
}

.id-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .id-text {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .copy-icon {
    cursor: pointer;
    color: #909399;
    transition: color 0.3s;

    &:hover {
      color: #409eff;
    }
  }
}

.icon-actions {
  display: flex;
  gap: 12px;
  justify-content: left;
  align-items: center;
}

.text-ellipsis {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-muted {
  color: #909399;
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
}

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

// 响应式调整
@media (max-width: 1200px) {
  .main-filters {
    flex-wrap: wrap;
    row-gap: 12px;

    .action-buttons {
      margin-left: 0;
      width: 100%;
      justify-content: flex-end;
    }
  }
}

@media (max-width: 768px) {
  .penalty-score-container {
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
  }

  .table-right-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .icon-actions {
    gap: 8px;

    .action-icon {
      font-size: 14px;
    }
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

// 输入框聚焦效果
:deep(.el-input) {
  .el-input__inner {
    transition: all 0.3s;

    &:focus {
      border-color: #409eff;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
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
</style>
