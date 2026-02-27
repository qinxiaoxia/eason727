<template>
  <div class="scoring-item-container">
    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="main-filters">
        <!-- 关键词搜索 -->
        <el-input
          v-model="filterParams.keyword"
          placeholder="搜索评分项名称"
          clearable
          @input="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        />

        <!-- 项目筛选 -->
        <el-select
          v-model="filterParams.projectId"
          placeholder="选择项目"
          filterable
          clearable
          @change="handleSearch"
          class="keyword-input"
          style="width: 200px"
        >
          <el-option
            v-for="project in projectList"
            :key="project.id"
            :label="project.projectName"
            :value="project.id"
          />
        </el-select>

        <!-- 规则筛选 -->
        <el-select
          v-model="filterParams.ruleId"
          placeholder="选择评分规则"
          filterable
          clearable
          @change="handleSearch"
          class="keyword-input"
          style="width: 200px"
        >
          <el-option
            v-for="rule in ruleList"
            :key="rule.id"
            :label="rule.ruleName"
            :value="rule.id"
          />
        </el-select>

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
                v-model="filterParams.attackTeamId"
                placeholder="攻击队伍ID"
                type="number"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.defenseTeamId"
                placeholder="防守队伍ID"
                type="number"
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

    <!-- 表格区域 -->
    <el-card class="table-card">
      <!-- 表格操作区域 -->
      <div class="table-actions">
        <el-button-group>
          <el-button type="primary" @click="handleAddItem">
            <el-icon><Plus /></el-icon>新增评分项
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
        key="scoring-item-table"
      >
        <!-- 选择列 -->
        <el-table-column type="selection" width="50" align="center" />

        <!-- 评分项ID -->
        <el-table-column prop="id" label="序号" min-width="60"> </el-table-column>

        <!-- 评分项名称 -->
        <el-table-column prop="itemName" label="评分项名称" min-width="200" show-overflow-tooltip />

        <!-- 项目名称 -->
        <el-table-column prop="projectName" label="所属项目" min-width="180" align="center">
          <template #default="{ row }">
            {{ getProjectName(row.projectId) || '-' }}
          </template>
        </el-table-column>

        <!-- 评分规则 -->
        <el-table-column prop="ruleName" label="评分规则" min-width="200" align="center">
          <template #default="{ row }">
            {{ getRuleName(row.ruleId) || '-' }}
          </template>
        </el-table-column>

        <!-- 攻击队伍 -->
        <el-table-column prop="attackTeamName" label="攻击队伍" min-width="150" align="center">
          <template #default="{ row }">
            {{ getTeamName(row.attackTeamId) || '-' }}
          </template>
        </el-table-column>

        <!-- 防守队伍 -->
        <el-table-column prop="defenseTeamName" label="防守队伍" min-width="150" align="center">
          <template #default="{ row }">
            {{ getTeamName(row.defenseTeamId) || '-' }}
          </template>
        </el-table-column>

        <!-- 实际得分 -->
        <el-table-column prop="actualScore" label="实际得分" width="120" align="center">
          <template #default="{ row }">
            <span :class="getScoreClass(row.actualScore)">
              {{ formatScore(row.actualScore) }}
            </span>
          </template>
        </el-table-column>

        <!-- 最终得分 -->
        <el-table-column prop="finalScore" label="最终得分" width="120" align="center">
          <template #default="{ row }">
            <span :class="getScoreClass(row.finalScore)">
              {{ formatScore(row.finalScore) }}
            </span>
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
                <el-icon class="action-icon edit-icon" @click="handleEditItem(row)">
                  <Edit />
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
      class="item-drawer"
      :close-on-click-modal="true"
    >
      <div class="drawer-content" v-if="drawerVisible">
        <el-card shadow="never" class="form-section">
          <template #header>
            <div class="card-header">
              <span>评分项信息</span>
            </div>
          </template>
          <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="评分项名称" prop="itemName" required>
                  <el-input
                    v-model="formData.itemName"
                    placeholder="请输入评分项名称"
                    maxlength="100"
                    show-word-limit
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="所属项目" prop="projectId" required>
                  <el-select
                    v-model="formData.projectId"
                    placeholder="请选择项目"
                    filterable
                    clearable
                    @change="handleProjectChange"
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
                <el-form-item label="评分规则" prop="ruleId" required>
                  <el-select
                    v-model="formData.ruleId"
                    placeholder="请选择评分规则"
                    filterable
                    clearable
                  >
                    <el-option
                      v-for="rule in ruleList"
                      :key="rule.id"
                      :label="rule.ruleName"
                      :value="rule.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="攻击队伍">
                  <el-select
                    v-model="formData.attackTeamId"
                    placeholder="请选择攻击队伍"
                    filterable
                    clearable
                  >
                    <el-option
                      v-for="team in attackTeamList"
                      :key="team.id"
                      :label="team.teamName"
                      :value="team.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="防守队伍">
                  <el-select
                    v-model="formData.defenseTeamId"
                    placeholder="请选择防守队伍"
                    filterable
                    clearable
                  >
                    <el-option
                      v-for="team in defenseTeamList"
                      :key="team.id"
                      :label="team.teamName"
                      :value="team.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="实际得分">
                  <el-input
                    v-model.number="formData.actualScore"
                    placeholder="请输入实际得分"
                    type="number"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="关联成绩">
                  <el-select
                    v-model="formData.resultId"
                    placeholder="请选择成绩"
                    filterable
                    clearable
                    :disabled="!formData.projectId"
                    @change="handleResultChange"
                  >
                    <el-option
                      v-for="result in resultList"
                      :key="result.id"
                      :label="`成绩-${result.id} (${result.attackTeamName || '未知'})`"
                      :value="result.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="关联成果">
                  <el-select
                    v-model="formData.achievementId"
                    placeholder="请选择成果"
                    filterable
                    clearable
                    :disabled="!formData.resultId"
                  >
                    <el-option
                      v-for="achievement in achievementList"
                      :key="achievement.id"
                      :label="achievement.achievementName || achievement.id"
                      :value="achievement.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="最终得分">
                  <el-input
                    v-model.number="formData.finalScore"
                    placeholder="请输入最终得分"
                    type="number"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>
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
      :title="`评分项详情 - ID: ${currentDetail?.id || '未知'}`"
      direction="rtl"
      size="60%"
      class="detail-drawer"
    >
      <div class="detail-content" v-if="currentDetail">
        <div class="detail-header">
          <h2>评分项详情</h2>
        </div>
        <el-card shadow="never" class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="评分项 ID">{{
              currentDetail.id || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="评分项名称">{{
              currentDetail.itemName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="所属项目">{{
              getProjectName(currentDetail.projectId) || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="评分规则">{{
              getRuleName(currentDetail.ruleId) || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="攻击队伍">{{
              getTeamName(currentDetail.attackTeamId) || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="防守队伍">{{
              getTeamName(currentDetail.defenseTeamId) || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="实际得分">
              <span :class="getScoreClass(currentDetail.actualScore)">
                {{ formatScore(currentDetail.actualScore) }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="最终得分">
              <span :class="getScoreClass(currentDetail.finalScore)">
                {{ formatScore(currentDetail.finalScore) }}
              </span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Refresh, Filter, View, Edit } from '@element-plus/icons-vue'
import { scoringItemApi } from '@/api/services/panaltyscore/scoringItem'
import { projectApi } from '@/api/services/project/project'
import { scoringRuleApi } from '@/api/services/panaltyscore/scoringRule'
import teamApi from '@/api/services/team/team'
import { attackScoreApi } from '@/api/services/attack/attackScore'

// 状态
const loading = ref(false)
const saving = ref(false)
const showMoreFilters = ref(false)
const drawerVisible = ref(false)
const detailVisible = ref(false)
const tableData = ref([])
const selectedRows = ref([])
const formRef = ref()

// 数据列表
const projectList = ref([])
const ruleList = ref([])
const teamList = ref([])
const resultList = ref([])
const achievementList = ref([])

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

// 筛选参数
const filterParams = reactive({
  keyword: '',
  projectId: '',
  ruleId: '',
  attackTeamId: '',
  defenseTeamId: '',
})

// 抽屉模式
const drawerMode = ref('add') // 'add' | 'edit'
const drawerTitle = computed(() => (drawerMode.value === 'add' ? '新增评分项' : '编辑评分项'))

// 表单数据
const formData = reactive({
  itemName: '',
  projectId: '',
  ruleId: '',
  attackTeamId: '',
  defenseTeamId: '',
  resultId: '',
  achievementId: '',
  actualScore: null,
  finalScore: null,
})

// 表单验证规则
const formRules = {
  itemName: [{ required: true, message: '请输入评分项名称', trigger: 'blur' }],
  projectId: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  ruleId: [{ required: true, message: '请选择评分规则', trigger: 'change' }],
}

// 当前操作的数据
const currentDetail = ref(null)

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

// 获取评分规则列表
const fetchRuleList = async () => {
  try {
    const result = await scoringRuleApi.getPageList({
      page: 1,
      limit: 1000,
      data: {},
    })
    if (result && result.code === 200) {
      ruleList.value = result.data || []
    }
  } catch (error) {
    console.error('获取评分规则列表失败:', error)
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
    }
  } catch (error) {
    console.error('获取队伍列表失败:', error)
  }
}

// 攻击队伍列表
const attackTeamList = computed(() => {
  return teamList.value.filter((team) => team.teamType === 'attack')
})

// 防守队伍列表
const defenseTeamList = computed(() => {
  return teamList.value.filter((team) => team.teamType === 'defense')
})

// 根据项目ID获取项目名称
const getProjectName = (projectId) => {
  const project = projectList.value.find((item) => item.id === projectId)
  return project ? project.projectName : ''
}

// 根据规则ID获取规则名称
const getRuleName = (ruleId) => {
  const rule = ruleList.value.find((item) => item.id === ruleId)
  return rule ? rule.ruleName : ''
}

// 根据队伍ID获取队伍名称
const getTeamName = (teamId) => {
  const team = teamList.value.find((item) => item.id === teamId)
  return team ? team.teamName : ''
}

// 格式化分数显示
const formatScore = (score) => {
  if (score === null || score === undefined) return '-'
  return Number(score).toFixed(2)
}

// 获取分数样式类
const getScoreClass = (score) => {
  if (score === null || score === undefined) return 'score-normal'
  const numScore = Number(score)
  if (numScore > 0) return 'score-positive'
  if (numScore < 0) return 'score-negative'
  return 'score-normal'
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
    const result = await scoringItemApi.getPageList(params)
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

// 新增评分项
const handleAddItem = () => {
  drawerMode.value = 'add'
  // 重置表单数据
  Object.keys(formData).forEach((key) => {
    formData[key] = ''
  })
  formData.actualScore = null
  formData.finalScore = null
  drawerVisible.value = true
}

// 编辑评分项
const handleEditItem = (row) => {
  drawerMode.value = 'edit'
  currentDetail.value = row
  // 填充表单数据
  Object.keys(formData).forEach((key) => {
    if (row[key] !== undefined && row[key] !== null) {
      formData[key] = row[key]
    }
  })
  drawerVisible.value = true
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    const result = await scoringItemApi.getInfo({ id: row.id })
    currentDetail.value = result.data || result
    detailVisible.value = true
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取详情失败:' + error.message)
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除此评分项吗?', '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await scoringItemApi.batchRemove([row.id])
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
    ElMessage.warning('请先选择要删除的评分项')
    return
  }

  try {
    const ids = selectedRows.value.map((item) => item.id)
    await ElMessageBox.confirm(`确定删除选中的${ids.length}条评分项吗?`, '批量删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await scoringItemApi.batchRemove(ids)
    if (result && result.code === 200) {
      ElMessage.success(`成功删除${ids.length}条评分项`)
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
      itemName: formData.itemName.trim(),
      projectId: Number(formData.projectId),
      ruleId: Number(formData.ruleId),
      attackTeamId: formData.attackTeamId ? Number(formData.attackTeamId) : null,
      defenseTeamId: formData.defenseTeamId ? Number(formData.defenseTeamId) : null,
      resultId: formData.resultId ? Number(formData.resultId) : null,
      achievementId: formData.achievementId ? Number(formData.achievementId) : null,
      actualScore:
        formData.actualScore !== null && formData.actualScore !== ''
          ? Number(formData.actualScore)
          : null,
      finalScore:
        formData.finalScore !== null && formData.finalScore !== ''
          ? Number(formData.finalScore)
          : null,
    }

    // 如果是编辑模式，添加ID
    if (drawerMode.value === 'edit' && currentDetail.value?.id) {
      saveData.id = currentDetail.value.id
    }

    let result
    if (drawerMode.value === 'edit') {
      result = await scoringItemApi.modify(saveData)
    } else {
      result = await scoringItemApi.add(saveData)
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

// 初始化
onMounted(() => {
  fetchProjectList()
  fetchRuleList()
  fetchTeamList()
  fetchData()
})

// 获取成绩列表
const fetchResultList = async (projectId) => {
  if (!projectId) {
    resultList.value = []
    achievementList.value = []
    return
  }
  try {
    const result = await attackScoreApi.getPageList({
      page: 1,
      limit: 100,
      data: { projectId: Number(projectId) },
    })
    if (result && result.code === 200) {
      resultList.value = result.data?.list || []
    }
  } catch (error) {
    console.error('获取成绩列表失败:', error)
  }
}

// 获取成果列表
const fetchAchievementList = async (resultId) => {
  if (!resultId) {
    achievementList.value = []
    return
  }
  const result = resultList.value.find((r) => r.id === Number(resultId))
  if (result && result.resultGraph) {
    try {
      const parsed = JSON.parse(result.resultGraph)
      achievementList.value = parsed.achievements || []
    } catch {
      achievementList.value = []
    }
  } else {
    achievementList.value = []
  }
}

// 项目选择变化
const handleProjectChange = (projectId) => {
  formData.resultId = ''
  formData.achievementId = ''
  resultList.value = []
  achievementList.value = []
  if (projectId) {
    fetchResultList(projectId)
  }
}

// 成绩选择变化
const handleResultChange = (resultId) => {
  formData.achievementId = ''
  achievementList.value = []
  if (resultId) {
    fetchAchievementList(resultId)
  }
}
</script>

<style scoped lang="scss">
.scoring-item-container {
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

.score-positive {
  color: #67c23a;
  font-weight: bold;
}

.score-negative {
  color: #f56c6c;
  font-weight: bold;
}

.score-normal {
  color: #606266;
  font-weight: bold;
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
  .scoring-item-container {
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
