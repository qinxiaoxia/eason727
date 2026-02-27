<template>
  <div class="attack-score-container">
    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="main-filters">
        <!-- 关键词搜索 -->
        <el-select
          v-model="filterParams.attackTeamId"
          placeholder="攻击队伍"
          clearable
          filterable
          @change="handleSearch"
          class="keyword-input"
          style="width: 220px"
        >
          <el-option
            v-for="team in attackTeams"
            :key="team.id"
            :label="team.teamName"
            :value="team.id"
          />
        </el-select>
        <el-select
          v-model="filterParams.defenseTeamId"
          placeholder="防守队伍"
          clearable
          filterable
          @change="handleSearch"
          class="keyword-input"
          style="width: 220px"
        >
          <el-option
            v-for="team in defenseTeams"
            :key="team.id"
            :label="team.teamName"
            :value="team.id"
          />
        </el-select>
        <el-select
          v-model="filterParams.projectId"
          placeholder="项目"
          clearable
          filterable
          @change="handleSearch"
          class="keyword-input"
          style="width: 220px"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.projectName"
            :value="project.id"
          />
        </el-select>
        <!-- 操作按钮 -->
        <el-button-group class="action-buttons">
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
        </el-button-group>
      </div>
      <!-- 更多筛选 -->
    </div>

    <!-- 表格区域 -->
    <el-card class="table-card">
      <!-- 表格操作区域 -->
      <div class="table-actions">
        <el-button-group>
          <el-button type="primary" @click="handleAddScore">
            <el-icon><Plus /></el-icon>新增成绩
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
        key="score-table"
      >
        <!-- 选择列 -->
        <el-table-column type="selection" width="50" align="center" />

        <!-- 成绩ID -->
        <el-table-column prop="id" label="成绩ID" width="90"> </el-table-column>

        <el-table-column prop="attackTeamName" label="攻击队伍" width="180" align="center">
          <template #default="{ row }">
            <span>{{ row.attackTeamName || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="defenseTeamName" label="防守队伍" width="180" align="center">
          <template #default="{ row }">
            <span>{{ row.defenseTeamName || '-' }}</span>
          </template>
        </el-table-column>

        <!-- 项目 -->
        <el-table-column prop="projectName" label="项目" width="200" align="center">
          <template #default="{ row }">
            <span>{{ row.projectName || '-' }}</span>
          </template>
        </el-table-column>

        <!-- 攻击描述 -->
        <el-table-column prop="description" label="攻击描述" min-width="200">
          <template #default="{ row }">
            <span>{{ row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="成果数量" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.resultGraph && row.resultGraph !== '{}'" type="success" size="small">
              {{ getAchievementCount(row.resultGraph) }}
            </el-tag>
            <el-tag v-else type="info" size="small">0</el-tag>
          </template>
        </el-table-column>
        <!-- 操作列 -->
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="icon-actions">
              <!-- 查看详情 -->
              <el-tooltip content="查看详情" placement="top">
                <el-icon class="action-icon view-icon" @click="handleViewDetail(row)">
                  <View />
                </el-icon>
              </el-tooltip>

              <!-- 创建/编辑成果 -->
              <el-tooltip :content="hasAchievements(row) ? '编辑成果' : '创建成果'" placement="top">
                <el-icon
                  class="action-icon"
                  :class="hasAchievements(row) ? 'edit-icon' : 'add-icon'"
                  @click="
                    hasAchievements(row) ? handleEditAchievement(row) : handleCreateAchievement(row)
                  "
                >
                  <Collection v-if="hasAchievements(row)" />
                  <Plus v-else />
                </el-icon>
              </el-tooltip>

              <!-- 编辑成绩 -->
              <el-tooltip content="编辑成绩" placement="top">
                <el-icon class="action-icon edit-icon" @click="handleEditScore(row)">
                  <Document />
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

    <!-- 新增/编辑成绩弹窗 -->
    <el-dialog
      v-model="scoreDialogVisible"
      :title="scoreDialogTitle"
      width="95%"
      top="3vh"
      class="score-dialog"
      :close-on-click-modal="false"
      :before-close="handleDialogClose"
    >
      <div class="dialog-content">
        <!-- 基础信息表单 -->
        <el-card shadow="never" class="form-section">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
            </div>
          </template>
          <el-form :model="scoreForm" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="防守单位" required>
                  <el-select
                    v-model="scoreForm.defenseTeamId"
                    placeholder="请选择防守单位"
                    filterable
                    clearable
                    @change="handleDefenseTeamChange"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="team in defenseTeams"
                      :key="team.id"
                      :label="team.teamName"
                      :value="team.id"
                    >
                      <span>{{ team.teamName }}</span>
                      <span v-if="team.teamShortName" class="option-desc"
                        >({{ team.teamShortName }})</span
                      >
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>

              <!-- 项目改为下拉选择 -->
              <el-col :span="8">
                <el-form-item label="项目" required>
                  <el-select
                    v-model="scoreForm.projectId"
                    placeholder="请选择项目"
                    filterable
                    clearable
                    @change="handleProjectChange"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="project in projects"
                      :key="project.id"
                      :label="project.projectName"
                      :value="project.id"
                    >
                      <span>{{ project.projectName }}</span>
                      <span v-if="project.organization" class="option-desc"
                        >({{ project.organization }})</span
                      >
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="攻击描述">
              <el-input
                v-model="scoreForm.description"
                type="textarea"
                :rows="3"
                placeholder="请输入攻击描述"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 攻击成果流程图 -->
        <el-card shadow="never" class="flow-section">
          <template #header>
            <div class="card-header">
              <span>| 攻击成果流程图</span>
            </div>
          </template>

          <AttackAchievementFlow
            ref="flowRef"
            @node-dblclick="handleNodeDoubleClick"
            @save="handleFlowSave"
          />
        </el-card>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="scoreDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveScore">保存成绩</el-button>
          <el-button type="success" @click="handleValidateScore">校验</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 基本信息弹窗（新建/编辑成绩） -->
    <el-dialog
      v-model="basicDialogVisible"
      :title="scoreForm.id ? '编辑成绩' : '新建成绩'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="scoreForm" label-width="100px">
        <el-form-item label="防守单位" required>
          <el-select
            v-model="scoreForm.defenseTeamId"
            placeholder="请选择防守单位"
            filterable
            clearable
            @change="handleDefenseTeamChange"
            style="width: 100%"
          >
            <el-option
              v-for="team in defenseTeams"
              :key="team.id"
              :label="team.teamName"
              :value="team.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" required>
          <el-select
            v-model="scoreForm.projectId"
            placeholder="请选择项目"
            filterable
            clearable
            @change="handleProjectChange"
            style="width: 100%"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.projectName"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="攻击描述">
          <el-input
            v-model="scoreForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入攻击描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="basicDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveBasic">保存</el-button>
      </template>
    </el-dialog>

    <!-- 成果流程图弹窗 -->
    <el-dialog
      v-model="achievementDialogVisible"
      :title="achievementMode === 'create' ? '创建成果' : '编辑成果'"
      width="95%"
      top="3vh"
      :close-on-click-modal="false"
    >
      <AttackAchievementFlow
        ref="flowRef"
        :result-id="scoreForm.id || 0"
        :project-id="Number(scoreForm.projectId) || 0"
        :attack-team-id="Number(scoreForm.attackTeamId) || 0"
        :defense-team-id="Number(scoreForm.defenseTeamId) || 0"
      />
      <template #footer>
        <el-button @click="achievementDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleSaveAchievement">保存成果</el-button>
      </template>
    </el-dialog>

    <!-- 成绩详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      :title="`成绩详情 - ID: ${currentDetail?.id || '未知'}`"
      direction="rtl"
      size="60%"
      class="score-detail-drawer"
      :close-on-click-modal="true"
    >
      <div class="detail-content" v-if="currentDetail">
        <div class="detail-header">
          <h2>成绩详情</h2>
        </div>

        <el-card shadow="never" class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="成绩ID">
              {{ currentDetail.id || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="攻击单位ID">
              {{ currentDetail.attackTeamId || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="防守单位ID">
              {{ currentDetail.defenseTeamId || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="项目ID">
              {{ currentDetail.projectId || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatFullTime(currentDetail.createTime) || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatFullTime(currentDetail.updateTime) || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="攻击描述" :span="2">
              {{ currentDetail.description || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 关联成果列表 -->
        <el-card shadow="never" class="achievements-card" v-if="currentDetail.achievements">
          <template #header>
            <div class="card-header">
              <span>关联成果列表</span>
            </div>
          </template>

          <el-table :data="currentDetail.achievements" border stripe>
            <el-table-column prop="achievementName" label="成果名称" min-width="200" />
            <el-table-column prop="assetName" label="资产名称" width="150" />
            <el-table-column prop="assetIP" label="资产IP" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="actualScore" label="得分" width="80" align="center" />
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleEditAchievementFromDetail(row)">
                  编辑成果
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { Plus, Delete, Refresh, View, Document, Collection } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AttackAchievementFlow from '@/components/attack-flow/AttackAchievementFlow.vue'
import { attackScoreApi } from '@/api/services/attack/attackScore'
import teamApi from '@/api/services/team/team'
import { projectApi } from '@/api/services/project/project.js'

// 状态
const loading = ref(false)
const detailDrawerVisible = ref(false)
const scoreDialogVisible = ref(false)
const basicDialogVisible = ref(false)
const achievementDialogVisible = ref(false)
const achievementMode = ref('create')
const currentDetail = ref(null)
const selectedRows = ref([])
const attackTeams = ref([])
const defenseTeams = ref([])
const projects = ref([])
// 表格数据
const tableData = ref([])

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

// 成绩表单
const scoreForm = ref({
  attackTeamId: '',
  attackTeamName: '',
  defenseTeamId: '',
  defenseTeamName: '',
  projectId: '',
  projectName: '',
  description: '',
  resultGraph: '',
})

// 流程图引用
const flowRef = ref(null)

// 筛选参数
const filterParams = reactive({
  keyword: '',
  attackTeamId: '',
  attackTeamName: '',
  defenseTeamId: '',
  defenseTeamName: '',
  projectId: '',
  projectName: '',
})

const handleDefenseTeamChange = (teamId) => {
  const selectedTeam = defenseTeams.value.find((team) => team.id === teamId)
  if (selectedTeam) {
    scoreForm.value.defenseTeamName = selectedTeam.teamName
  } else {
    scoreForm.value.defenseTeamName = ''
  }
}

const handleProjectChange = (projectId) => {
  const selectedProject = projects.value.find((project) => project.id === projectId)
  if (selectedProject) {
    scoreForm.value.projectName = selectedProject.projectName
  } else {
    scoreForm.value.projectName = ''
  }
}

const getAchievementCount = (resultGraph) => {
  try {
    if (!resultGraph || resultGraph === '{}') return 0
    const data = JSON.parse(resultGraph)
    return data.achievements?.length || 0
  } catch {
    return 0
  }
}

const getStatusTagType = (status) => {
  const statusMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    draft: 'info',
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待审核',
    approved: '已批准',
    rejected: '已拒绝',
    draft: '草稿',
  }
  return statusMap[status] || status
}

// 定义所有在模板中使用的函数
const handleSearch = () => {
  clearTimeout(searchTimer.value)
  searchTimer.value = setTimeout(() => {
    pagination.currentPage = 1
    fetchData()
  }, 500)
}

const searchTimer = ref(null)

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

const hasAchievements = (row) => {
  if (!row.resultGraph || row.resultGraph === '{}') {
    return false
  }
  try {
    const data = JSON.parse(row.resultGraph)
    return data.achievements && data.achievements.length > 0
  } catch {
    return false
  }
}

const handleSaveBasic = async () => {
  if (!scoreForm.value.defenseTeamId) {
    ElMessage.warning('请选择防守单位')
    return
  }
  if (!scoreForm.value.projectId) {
    ElMessage.warning('请选择项目')
    return
  }

  try {
    const saveData = {
      attackTeamId: Number(scoreForm.value.attackTeamId) || 0,
      attackTeamName: scoreForm.value.attackTeamName || '',
      defenseTeamId: Number(scoreForm.value.defenseTeamId),
      defenseTeamName: scoreForm.value.defenseTeamName || '',
      projectId: Number(scoreForm.value.projectId),
      projectName: scoreForm.value.projectName || '',
      description: scoreForm.value.description || '',
    }

    if (scoreForm.value.id) {
      saveData.id = scoreForm.value.id
      await attackScoreApi.modify(saveData)
      ElMessage.success('成绩更新成功')
    } else {
      const result = await attackScoreApi.add(saveData)
      if (result.data && result.data.id) {
        scoreForm.value.id = result.data.id
      }
      ElMessage.success('成绩创建成功')
    }

    fetchData()
    basicDialogVisible.value = false
  } catch (error) {
    console.error('保存成绩失败:', error)
    ElMessage.error('保存失败')
  }
}

const handleCreateAchievement = async (row) => {
  const projectName =
    row.projectName ||
    projects.value.find((project) => project.id === row.projectId)?.projectName ||
    ''

  scoreForm.value = {
    id: row.id,
    attackTeamId: row.attackTeamId || '',
    attackTeamName: row.attackTeamName || '',
    defenseTeamId: row.defenseTeamId,
    defenseTeamName: row.defenseTeamName || '',
    projectId: row.projectId,
    projectName: projectName,
    description: row.description || '',
  }

  achievementMode.value = 'create'
  achievementDialogVisible.value = true
  await nextTick()
  if (flowRef.value) {
    flowRef.value.resetGraph()
  }
}

const handleEditAchievement = async (row) => {
  const projectName =
    row.projectName ||
    projects.value.find((project) => project.id === row.projectId)?.projectName ||
    ''

  const defenseTeamName =
    row.defenseTeamName ||
    defenseTeams.value.find((team) => team.id === row.defenseTeamId)?.teamName ||
    ''

  const attackTeamName =
    row.attackTeamName ||
    attackTeams.value.find((team) => team.id === row.attackTeamId)?.teamName ||
    ''

  scoreForm.value = {
    id: row.id,
    attackTeamId: row.attackTeamId || '',
    attackTeamName: attackTeamName,
    defenseTeamId: row.defenseTeamId,
    defenseTeamName: defenseTeamName,
    projectId: row.projectId,
    projectName: projectName,
    description: row.description || '',
  }
  achievementMode.value = 'edit'
  achievementDialogVisible.value = true
  await nextTick()
  if (flowRef.value && row.resultGraph) {
    try {
      const data = JSON.parse(row.resultGraph)
      if (data.achievements) {
        const x6Data = convertToX6Format(data)
        if (x6Data) {
          flowRef.value.loadGraphData(x6Data)
        }
      } else if (data.cells) {
        flowRef.value.loadGraphData(data)
      }
    } catch (e) {
      console.error('加载流程图失败:', e)
    }
  }
}

const handleSaveAchievement = async () => {
  if (!scoreForm.value.id) {
    ElMessage.warning('请先保存成绩')
    return
  }

  try {
    let resultGraph = '{}'
    if (flowRef.value) {
      const flowData = flowRef.value.getGraphData()
      const simplifiedData = simplifyGraphData(flowData, scoreForm.value.id)
      resultGraph = JSON.stringify(simplifiedData)
    }

    const saveData = {
      id: scoreForm.value.id,
      attackTeamId: Number(scoreForm.value.attackTeamId) || 0,
      attackTeamName: scoreForm.value.attackTeamName || '',
      defenseTeamId: Number(scoreForm.value.defenseTeamId),
      defenseTeamName: scoreForm.value.defenseTeamName || '',
      projectId: Number(scoreForm.value.projectId),
      projectName: scoreForm.value.projectName || '',
      description: scoreForm.value.description || '',
      resultGraph: resultGraph,
    }

    await attackScoreApi.modify(saveData)
    ElMessage.success('成果保存成功')
    achievementDialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error('保存成果失败:', error)
    ElMessage.error('保存失败')
  }
}

const handleEditAchievementFromDetail = async () => {
  const row = tableData.value.find((item) => item.id === currentDetail.value.id)
  if (row) {
    detailDrawerVisible.value = false
    await nextTick()
    handleEditAchievement(row)
  }
}

const handleAddScore = () => {
  scoreForm.value = {
    id: '',
    attackTeamId: '',
    defenseTeamId: '',
    projectId: '',
    description: '',
  }
  basicDialogVisible.value = true
}

const handleBatchDelete = async () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要删除的成绩')
    return
  }

  try {
    const ids = selectedRows.value.map((item) => item.id)
    await ElMessageBox.confirm(`确定删除选中的 ${ids.length} 条成绩吗？`, '批量删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    await attackScoreApi.batchRemove(ids)
    ElMessage.success(`成功删除 ${ids.length} 条成绩`)
    selectedRows.value = []
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const handleViewDetail = async (row) => {
  const detailData = {
    id: row.id,
    projectId: row.projectId,
    attackTeamId: row.attackTeamId,
    defenseTeamId: row.defenseTeamId,
    description: row.description || '',
    createTime: row.createTime,
    updateTime: row.updateTime,
    resultGraph: row.resultGraph,
  }

  if (detailData.resultGraph && detailData.resultGraph !== '{}') {
    try {
      const parsed = JSON.parse(detailData.resultGraph)
      if (parsed.achievements) {
        detailData.achievements = parsed.achievements
      }
    } catch (e) {
      console.error('解析resultGraph失败:', e)
    }
  }

  currentDetail.value = detailData
  detailDrawerVisible.value = true
}

const handleEditScore = async (row) => {
  const defenseTeamName =
    row.defenseTeamName ||
    defenseTeams.value.find((team) => team.id === row.defenseTeamId)?.teamName ||
    ''
  const projectName =
    row.projectName ||
    projects.value.find((project) => project.id === row.projectId)?.projectName ||
    ''

  scoreForm.value = {
    id: row.id,
    attackTeamId: row.attackTeamId || '',
    defenseTeamId: row.defenseTeamId,
    defenseTeamName: defenseTeamName,
    projectId: row.projectId,
    projectName: projectName,
    description: row.description || '',
  }

  basicDialogVisible.value = true
}

// 后端格式转 X6 格式
const convertToX6Format = (backendData) => {
  if (!backendData || !backendData.achievements) {
    return null
  }

  const cells = []

  // 添加起点节点
  const startNode = {
    id: 'start',
    shape: 'circle',
    position: { x: 100, y: 200 },
    size: { width: 60, height: 60 },
    attrs: {
      label: { text: '起点', fill: '#fff' },
      body: { fill: '#409eff', stroke: '#409eff', strokeWidth: 2 },
    },
    data: {
      type: 'start',
      achievementName: '渗透路径起点',
      status: 'pending',
    },
    ports: {
      groups: {
        out: { position: 'right' },
      },
      items: [{ id: 'out-1', group: 'out' }],
    },
  }
  cells.push(startNode)

  // 添加成果节点
  backendData.achievements.forEach((achievement, index) => {
    const nodeId = `achievement-${index}`
    const statusColor =
      achievement.status === 'approved'
        ? '#67c23a'
        : achievement.status === 'rejected'
          ? '#f56c6c'
          : achievement.status === 'pending'
            ? '#e6a23c'
            : '#909399'
    const node = {
      id: nodeId,
      shape: 'polygon',
      points: '50,0 100,30 50,60 0,30',
      position: achievement.position || { x: 300 + index * 200, y: 200 },
      size: { width: 100, height: 60 },
      attrs: {
        label: { text: achievement.achievementName, fill: '#fff' },
        body: {
          fill: statusColor,
          stroke: statusColor,
          strokeWidth: 2,
        },
      },
      data: {
        type: 'achievement',
        achievementName: achievement.achievementName,
        assetName: achievement.assetName,
        assetIP: achievement.assetIP,
        networkLevel: achievement.networkLevel,
        status: achievement.status,
        predictedScore: achievement.predictedScore,
        actualScore: achievement.actualScore,
        description: achievement.description,
        attachmentName: achievement.attachmentName || '',
        attachmentUrl: achievement.attachmentUrl || '',
      },
      ports: {
        groups: {
          left: { position: 'left' },
          right: { position: 'right' },
          top: { position: 'top' },
          bottom: { position: 'bottom' },
        },
        items: [
          { id: 'left', group: 'left' },
          { id: 'right', group: 'right' },
          { id: 'top', group: 'top' },
          { id: 'bottom', group: 'bottom' },
        ],
      },
    }
    cells.push(node)

    // 添加边（简化版，只连接起点和第一个节点）
    if (index === 0) {
      const edgeId = `edge-${index}`
      const edge = {
        id: edgeId,
        shape: 'edge',
        source: { cell: 'start', port: 'out-1' },
        target: { cell: nodeId, port: 'left' },
        attrs: {
          line: {
            stroke: '#409eff',
            strokeWidth: 2,
          },
        },
        zIndex: 0,
      }
      cells.push(edge)
    }

    // 添加后续节点之间的边
    if (index > 0) {
      const prevNodeId = `achievement-${index - 1}`
      const edgeId = `edge-${index}`
      const edge = {
        id: edgeId,
        shape: 'edge',
        source: { cell: prevNodeId, port: 'right' },
        target: { cell: nodeId, port: 'left' },
        attrs: {
          line: {
            stroke: '#409eff',
            strokeWidth: 2,
          },
        },
        zIndex: 0,
      }
      cells.push(edge)
    }
  })

  // 添加结束节点
  const endNode = {
    id: 'end',
    shape: 'rect',
    position: { x: 800, y: 200 },
    size: { width: 120, height: 40 },
    attrs: {
      label: { text: '结束节点', fill: '#fff' },
      body: { fill: '#f56c6c', stroke: '#f56c6c', strokeWidth: 2 },
    },
    data: {
      type: 'end',
      achievementName: '结束节点',
      status: 'pending',
    },
    ports: {
      groups: {
        in: { position: 'left' },
      },
      items: [{ id: 'in-1', group: 'in' }],
    },
  }
  cells.push(endNode)

  console.log('转换后的 X6 数据:', { cells })
  return { cells }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除成绩 ID: ${row.id} 吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    // 调用删除接口
    const result = await attackScoreApi.batchRemove([row.id])
    console.log('删除响应:', result)

    // 判断删除是否成功
    if (result && result.code === 200) {
      ElMessage.success('删除成功')

      // 强制刷新分页数据
      pagination.currentPage = 1 // 重置到第一页
      await fetchData()
      console.log('🔄 删除后数据已刷新')
    } else {
      ElMessage.error(result?.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 新增：处理流程图保存
const handleFlowSave = () => {
  ElMessage.success('流程图已保存')
}

const handleSaveScore = async () => {
  try {
    // 验证必填项
    if (!scoreForm.value.defenseTeamId) {
      ElMessage.warning('请选择防守单位')
      return
    }
    if (!scoreForm.value.projectId) {
      ElMessage.warning('请选择项目')
      return
    }

    // 获取流程图数据
    let resultGraph = '{}'
    if (flowRef.value) {
      const flowData = flowRef.value.getGraphData()
      const simplifiedData = simplifyGraphData(flowData)
      resultGraph = JSON.stringify(simplifiedData)
    }

    // 准备保存数据
    const saveData = {
      attackTeamId: Number(scoreForm.value.attackTeamId),
      attackTeamName: scoreForm.value.attackTeamName,
      defenseTeamId: Number(scoreForm.value.defenseTeamId),
      defenseTeamName: scoreForm.value.defenseTeamName,
      projectId: Number(scoreForm.value.projectId),
      projectName: scoreForm.value.projectName,
      description: scoreForm.value.description || '',
      resultGraph: resultGraph,
    }

    console.log('保存数据:', saveData)

    let result
    if (scoreForm.value.id) {
      saveData.id = scoreForm.value.id
      result = await attackScoreApi.modify(saveData)
    } else {
      result = await attackScoreApi.add(saveData)
    }

    console.log('保存响应:', result)

    // 更健壮的判断逻辑
    if (result) {
      const action = scoreForm.value.id ? '更新' : '创建'
      ElMessage.success(`成绩${action}成功`)

      // 先刷新数据，再关闭弹窗
      await fetchData()
      scoreDialogVisible.value = false
      console.log('✅ 数据刷新完成')
    } else {
      ElMessage.error('保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + error.message)
  }
}
const simplifyGraphData = (flowData) => {
  if (!flowData || !flowData.cells) {
    return {} // 返回空对象，不是数组
  }

  const achievements = []
  const edges = []

  // 提取成果节点
  flowData.cells.forEach((cell) => {
    if (cell.shape === 'polygon' && cell.data && cell.data.type === 'achievement') {
      const achievement = {
        id: cell.id,
        achievementName: cell.data.achievementName || '未命名成果',
        assetName: cell.data.assetName || '',
        assetIP: cell.data.assetIP || '',
        networkLevel: cell.data.networkLevel || '',
        status: cell.data.status || 'pending',
        predictedScore: cell.data.predictedScore || 0,
        actualScore: cell.data.actualScore || 0,
        description: cell.data.description || '',
        attachmentName: cell.data.attachmentName || '',
        attachmentUrl: cell.data.attachmentUrl || '',
        position: {
          x: cell.position?.x || 0,
          y: cell.position?.y || 0,
        },
      }
      achievements.push(achievement)
    }
  })

  // 提取边的关系
  flowData.cells.forEach((cell) => {
    if (cell.shape === 'edge') {
      edges.push({
        id: cell.id,
        source: cell.source?.cell,
        target: cell.target?.cell,
      })
    }
  })

  console.log('提取的边数据:', edges)
  return {
    achievements,
    edges,
    metadata: {
      nodeCount: achievements.length,
      edgeCount: edges.length,
      createdAt: new Date().toISOString(),
    },
  }
}
const handleValidateScore = async () => {
  try {
    if (!scoreForm.value.defenseTeamId) {
      ElMessage.warning('请输入防守单位ID')
      return
    }
    if (!scoreForm.value.projectId) {
      ElMessage.warning('请输入项目ID')
      return
    }

    const flowData = flowRef.value ? flowRef.value.getGraphData() : null
    if (
      !flowData ||
      !flowData.cells ||
      !flowData.cells.some((cell) => cell.data?.type === 'achievement')
    ) {
      ElMessage.warning('请至少添加一个成果节点')
      return
    }

    ElMessage.success('校验通过')
  } catch (error) {
    console.error('校验失败:', error)
    ElMessage.error('校验失败')
  }
}

const handleNodeDoubleClick = (nodeData) => {
  console.log('节点双击:', nodeData)
}

// 处理弹窗关闭前的逻辑
const handleDialogClose = (done) => {
  // 检查流程图中是否有节点
  if (flowRef.value) {
    try {
      const flowData = flowRef.value.getGraphData()
      if (flowData && flowData.cells && flowData.cells.length > 0) {
        // 过滤掉起点节点，只检查成果节点
        const achievementNodes = flowData.cells.filter((cell) => {
          return cell.shape === 'polygon' && cell.data && cell.data.type === 'achievement'
        })

        if (achievementNodes.length > 0) {
          // 弹出提示对话框
          ElMessageBox.confirm('您的画布上有未保存的内容，是否保存后关闭？', '确认关闭', {
            confirmButtonText: '保存',
            cancelButtonText: '不保存',
            type: 'warning',
            distinguishCancelAndClose: true,
            closeOnClickModal: false,
          })
            .then(async () => {
              // 用户选择保存
              try {
                await handleSaveScore()
              } catch (error) {
                console.error('保存失败:', error)
              } finally {
                done()
              }
            })
            .catch(() => {
              // 用户选择不保存，直接关闭
              done()
            })
          return
        }
      }
    } catch (error) {
      console.error('检查画布节点失败:', error)
    }
  }
  // 没有节点或出错，直接关闭
  done()
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

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      limit: pagination.pageSize,
      data: { ...filterParams },
    }
    console.log('请求参数:', params)
    const result = await attackScoreApi.getPageList(params)
    console.log('原始接口响应:', result)

    // 调试：打印基础数据状态
    console.log('当前基础数据状态:', {
      defenseTeams: defenseTeams.value.length,
      projects: projects.value.length,
      defenseTeamsSample: defenseTeams.value.slice(0, 3),
      projectsSample: projects.value.slice(0, 3),
    })

    let processedData = []

    if (Array.isArray(result)) {
      processedData = result
    } else if (result && result.code === 200 && Array.isArray(result.data)) {
      processedData = result.data
      pagination.total = result.count || result.total || 0
    } else {
      processedData = []
      pagination.total = 0
    }

    // 详细的数据映射逻辑
    tableData.value = processedData.map((item) => {
      console.log('处理单条数据:', item)

      // 查找防守队伍名称
      const defenseTeam = defenseTeams.value.find((team) => team.id === item.defenseTeamId)
      console.log('防守队伍查找:', {
        defenseTeamId: item.defenseTeamId,
        defenseTeams: defenseTeams.value.map((t) => ({ id: t.id, name: t.teamName })),
        found: defenseTeam,
      })

      // 查找项目名称
      const project = projects.value.find(
        (proj) => String(proj.id) === String(item.projectId), // 关键修复：统一类型
      )
      console.log('项目查找:', {
        projectId: item.projectId,
        projects: projects.value.map((p) => ({ id: p.id, name: p.projectName })),
        found: project,
      })

      return {
        ...item,
        // 保持原始字段
        defenseTeamld: item.defenseTeamId,
        projectld: item.projectId,
        // 映射名称字段
        defenseTeamName: defenseTeam ? defenseTeam.teamName : '-',
        projectName: project?.projectName || '未知项目', // 更明确的占位符
        attackTeamName: item.attackTeamId
          ? attackTeams.value.find((team) => team.id === item.attackTeamId)?.teamName || '-'
          : '-',
      }
    })

    console.log('最终表格数据:', tableData.value)
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败:' + error.message)
  } finally {
    loading.value = false
  }
}

// 弹窗标题
const scoreDialogTitle = computed(() => {
  return scoreForm.value.id ? '编辑攻击成绩' : '新增攻击成绩'
})

onMounted(async () => {
  console.log('开始加载基础数据...')
  await loadTeamsAndProjects() // 等待基础数据加载完成
  console.log('基础数据加载完成，开始加载表格数据...')
  await fetchData() // 再加载表格数据
  console.log('所有数据加载完成')
})

// 确保 loadTeamsAndProjects 返回 Promise
const loadTeamsAndProjects = async () => {
  try {
    console.log('正在加载攻击队伍...')
    const attackTeamParams = {
      page: 1,
      limit: 1000,
      data: { teamType: 'attack' },
    }
    const attackResult = await teamApi.getPageList(attackTeamParams)
    attackTeams.value = attackResult.data || []
    console.log('攻击队伍加载完成:', attackTeams.value.length)

    console.log('正在加载防守队伍...')
    const defenseTeamParams = {
      page: 1,
      limit: 1000,
      data: { teamType: 'defense' },
    }
    const defenseResult = await teamApi.getPageList(defenseTeamParams)
    defenseTeams.value = defenseResult.data || []
    console.log('防守队伍加载完成:', defenseTeams.value.length)

    console.log('正在加载项目...')
    const projectParams = {
      page: 1,
      limit: 1000,
      data: {},
    }
    const projectResult = await projectApi.getPageList(projectParams)
    projects.value = projectResult.data || []
    console.log('项目加载完成:', projects.value.length)

    return true // 明确返回完成状态
  } catch (error) {
    console.error('加载基础数据失败:', error)
    ElMessage.error('加载基础数据失败')
    return false
  }
}
</script>

<style scoped lang="scss">
.attack-score-container {
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

.advanced-filters {
  padding: 12px 0;

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
  margin-bottom: 50px;
  margin-top: 30px;
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

.detail-content {
  padding: 20px;

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
  }

  .action-buttons {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
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

// 弹窗样式
.score-dialog {
  .dialog-content {
    max-height: 80vh;
    overflow-y: auto;
  }

  .form-section {
    margin-bottom: 20px;
  }

  .flow-section {
    min-height: 600px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
    color: #303133;
  }

  .detail-tabs {
    margin-bottom: -20px;
  }
}

// 抽屉样式
.score-detail-drawer {
  .detail-content {
    padding: 20px;
  }
}

// 状态标签样式
:deep(.el-tag) {
  border: none;
  font-weight: 500;

  &.el-tag--success {
    background-color: #f0f9ff;
    color: #67c23a;
  }

  &.el-tag--info {
    background-color: #f4f4f5;
    color: #909399;
  }

  &.el-tag--danger {
    background-color: #fef0f0;
    color: #f56c6c;
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

// 下拉菜单样式优化
:deep(.el-dropdown-menu) {
  .el-dropdown-menu__item {
    &:hover {
      background-color: #f5f7fa;
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

// 工具提示样式优化
:deep(.el-tooltip__popper) {
  max-width: 300px;
  word-break: break-all;
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
.dialog-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
.option-desc {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}

/* 下拉选择器样式优化 */
:deep(.el-select) {
  width: 100%;
}

:deep(.el-select .el-input__inner) {
  border-radius: 6px;
}
</style>
