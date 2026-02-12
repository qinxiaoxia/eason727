<template>
  <div class="scoring-rule-container">
    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="main-filters">
        <!-- 关键词搜索 -->
        <el-input
          v-model="filterParams.keyword"
          placeholder="搜索规则名称/规则编码"
          clearable
          @input="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        />

        <!-- 规则类型筛选 -->
        <el-select
          v-model="filterParams.ruleType"
          placeholder="规则类型"
          clearable
          @change="handleSearch"
          class="keyword-input"
        >
          <el-option label="加分规则" value="bonus" />
          <el-option label="扣分规则" value="penalty" />
          <el-option label="通用规则" value="common" />
        </el-select>

        <!-- 计分类型筛选 -->
        <el-select
          v-model="filterParams.scoreType"
          placeholder="计分类型"
          clearable
          @change="handleSearch"
          class="keyword-input"
        >
          <el-option label="固定分值" value="fixed" />
          <el-option label="累计分值" value="accumulative" />
          <el-option label="动态分值" value="dynamic" />
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
                v-model="filterParams.ruleCode"
                placeholder="规则编码"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.accumulativeCode"
                placeholder="累计编码"
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
          <el-button type="primary" @click="handleAddRule">
            <el-icon><Plus /></el-icon>新增规则
          </el-button>
          <el-button :disabled="!selectedRows.length" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>批量删除
          </el-button>
          <el-button @click="handleImport" plain>
            <el-icon><Upload /></el-icon>导入规则
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
        key="scoring-rule-table"
      >
        <!-- 选择列 -->
        <el-table-column type="selection" width="50" align="center" />

        <!-- 规则ID -->
        <el-table-column prop="id" label="序号" width="60"> </el-table-column>

        <!-- 规则名称 -->
        <el-table-column prop="ruleName" label="规则名称" min-width="200" show-overflow-tooltip />

        <!-- 规则编码 -->
        <el-table-column prop="ruleCode" label="规则编码" width="150" align="center" />

        <!-- 规则类型 -->
        <el-table-column prop="ruleType" label="规则类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getRuleTypeTag(row.ruleType)" effect="light">
              {{ getRuleTypeText(row.ruleType) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 计分类型 -->
        <el-table-column prop="scoreType" label="计分类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getScoreTypeTag(row.scoreType)">
              {{ getScoreTypeText(row.scoreType) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 分值 -->
        <el-table-column prop="scoreValue" label="分值" width="100" align="center">
          <template #default="{ row }">
            <span :class="getScoreValueClass(row.ruleType, row.scoreValue)">
              {{ getScoreValueText(row.ruleType, row.scoreValue) }}
            </span>
          </template>
        </el-table-column>

        <!-- 最低分限制 -->
        <el-table-column prop="minScore" label="最低分" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.minScore !== null && row.minScore !== undefined">
              {{ row.minScore }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <!-- 最高分限制 -->
        <el-table-column prop="maxScoreLimit" label="最高分" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.maxScoreLimit !== null && row.maxScoreLimit !== undefined">
              {{ row.maxScoreLimit }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <!-- 累计编码 -->
        <el-table-column prop="accumulativeCode" label="累计编码" width="150" align="center">
          <template #default="{ row }">
            <span v-if="row.accumulativeCode" class="text-ellipsis" :title="row.accumulativeCode">
              {{ row.accumulativeCode }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <!-- 规则描述 -->
        <el-table-column prop="description" label="规则描述" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.description" class="text-ellipsis" :title="row.description">
              {{ row.description }}
            </span>
            <span v-else class="text-muted">暂无描述</span>
          </template>
        </el-table-column>

        <!-- 评分规则 -->
        <el-table-column prop="scoringRule" label="评分规则" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.scoringRule" class="text-ellipsis" :title="row.scoringRule">
              {{ row.scoringRule }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" width="120" fixed="right">
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
                <el-icon class="action-icon edit-icon" @click="handleEditRule(row)">
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
      class="rule-drawer"
      :close-on-click-modal="true"
    >
      <div class="drawer-content" v-if="drawerVisible">
        <el-card shadow="never" class="form-section">
          <template #header>
            <div class="card-header">
              <span>评分规则信息</span>
            </div>
          </template>
          <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="规则名称" prop="ruleName" required>
                  <el-input
                    v-model="formData.ruleName"
                    placeholder="请输入规则名称"
                    maxlength="50"
                    show-word-limit
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="规则编码" prop="ruleCode" required>
                  <el-input
                    v-model="formData.ruleCode"
                    placeholder="请输入规则编码"
                    maxlength="20"
                    show-word-limit
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="规则类型" prop="ruleType" required>
                  <el-select v-model="formData.ruleType" placeholder="请选择规则类型">
                    <el-option label="加分规则" value="bonus" />
                    <el-option label="扣分规则" value="penalty" />
                    <el-option label="通用规则" value="common" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="计分类型" prop="scoreType" required>
                  <el-select v-model="formData.scoreType" placeholder="请选择计分类型">
                    <el-option label="固定分值" value="fixed" />
                    <el-option label="累计分值" value="accumulative" />
                    <el-option label="动态分值" value="dynamic" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="分值" prop="scoreValue" required>
                  <el-input
                    v-model.number="formData.scoreValue"
                    placeholder="请输入分值"
                    type="number"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="累计编码">
                  <el-input
                    v-model="formData.accumulativeCode"
                    placeholder="请输入累计编码"
                    maxlength="20"
                    show-word-limit
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="最低分">
                  <el-input
                    v-model.number="formData.minScore"
                    placeholder="请输入最低分限制"
                    type="number"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最高分">
                  <el-input
                    v-model.number="formData.maxScoreLimit"
                    placeholder="请输入最高分限制"
                    type="number"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="规则描述" prop="description">
              <el-input
                v-model="formData.description"
                type="textarea"
                :rows="3"
                placeholder="请输入规则描述"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="评分规则" prop="scoringRule">
              <el-input
                v-model="formData.scoringRule"
                type="textarea"
                :rows="4"
                placeholder="请输入具体的评分规则说明"
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
      :title="`评分规则详情 - ID: ${currentDetail?.id || '未知'}`"
      direction="rtl"
      size="60%"
      class="detail-drawer"
    >
      <div class="detail-content" v-if="currentDetail">
        <div class="detail-header">
          <h2>评分规则详情</h2>
        </div>
        <el-card shadow="never" class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="规则 ID">{{
              currentDetail.id || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="规则名称">{{
              currentDetail.ruleName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="规则编码">{{
              currentDetail.ruleCode || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="规则类型">
              <el-tag :type="getRuleTypeTag(currentDetail.ruleType)">
                {{ getRuleTypeText(currentDetail.ruleType) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="计分类型">
              <el-tag :type="getScoreTypeTag(currentDetail.scoreType)">
                {{ getScoreTypeText(currentDetail.scoreType) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="分值">
              <span :class="getScoreValueClass(currentDetail.ruleType, currentDetail.scoreValue)">
                {{ getScoreValueText(currentDetail.ruleType, currentDetail.scoreValue) }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="累计编码">{{
              currentDetail.accumulativeCode || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="最低分">{{
              currentDetail.minScore || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="最高分">{{
              currentDetail.maxScoreLimit || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="规则描述" :span="2">{{
              currentDetail.description || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="评分规则" :span="2">{{
              currentDetail.scoringRule || '-'
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </el-drawer>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="importVisible"
      title="导入评分规则"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="import-content">
        <el-upload
          ref="uploadRef"
          class="upload-demo"
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          accept=".xlsx,.xls"
        >
          <template #trigger>
            <el-button type="primary">选择文件</el-button>
          </template>
          <template #tip>
            <div class="el-upload__tip">请上传 .xlsx 或 .xls 格式的文件，文件大小不超过 10MB</div>
          </template>
        </el-upload>

        <div class="template-download" style="margin-top: 16px">
          <el-button type="text" @click="downloadTemplate">
            <el-icon><Download /></el-icon>
            下载导入模板
          </el-button>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="importVisible = false">取消</el-button>
          <el-button type="primary" @click="handleImportSubmit" :loading="importing">
            导入
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Delete,
  Refresh,
  Filter,
  View,
  Edit,
  Upload,
  Download,
} from '@element-plus/icons-vue'
import { scoringRuleApi } from '@/api/services/panaltyScore/scoringRule'

// 状态
const loading = ref(false)
const saving = ref(false)
const importing = ref(false)
const showMoreFilters = ref(false)
const drawerVisible = ref(false)
const detailVisible = ref(false)
const importVisible = ref(false)
const tableData = ref([])
const selectedRows = ref([])
const formRef = ref()
const uploadRef = ref()
const fileList = ref([])

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

// 筛选参数
const filterParams = reactive({
  keyword: '',
  ruleCode: '',
  ruleType: '',
  scoreType: '',
  accumulativeCode: '',
})

// 抽屉模式
const drawerMode = ref('add') // 'add' | 'edit'
const drawerTitle = computed(() => (drawerMode.value === 'add' ? '新增评分规则' : '编辑评分规则'))

// 表单数据
const formData = reactive({
  ruleName: '',
  ruleCode: '',
  ruleType: '',
  scoreType: '',
  scoreValue: 0,
  accumulativeCode: '',
  minScore: null,
  maxScoreLimit: null,
  description: '',
  scoringRule: '',
})

// 表单验证规则
const formRules = {
  ruleName: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  ruleCode: [{ required: true, message: '请输入规则编码', trigger: 'blur' }],
  ruleType: [{ required: true, message: '请选择规则类型', trigger: 'change' }],
  scoreType: [{ required: true, message: '请选择计分类型', trigger: 'change' }],
  scoreValue: [{ required: true, message: '请输入分值', trigger: 'blur' }],
}

// 当前操作的数据
const currentDetail = ref(null)

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      limit: pagination.pageSize,
      data: { ...filterParams },
    }
    const result = await scoringRuleApi.getPageList(params)
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

// 新增规则
const handleAddRule = () => {
  drawerMode.value = 'add'
  // 重置表单数据
  Object.keys(formData).forEach((key) => {
    formData[key] = ''
  })
  formData.scoreValue = 0
  formData.minScore = null
  formData.maxScoreLimit = null
  drawerVisible.value = true
}

// 编辑规则
const handleEditRule = (row) => {
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
    const result = await scoringRuleApi.getInfo({ id: row.id })
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
    await ElMessageBox.confirm('确定删除此评分规则吗?', '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await scoringRuleApi.batchRemove([row.id])
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
    ElMessage.warning('请先选择要删除的评分规则')
    return
  }

  try {
    const ids = selectedRows.value.map((item) => item.id)
    await ElMessageBox.confirm(`确定删除选中的${ids.length}条评分规则吗?`, '批量删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await scoringRuleApi.batchRemove(ids)
    if (result && result.code === 200) {
      ElMessage.success(`成功删除${ids.length}条评分规则`)
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
      ruleName: formData.ruleName.trim(),
      ruleCode: formData.ruleCode.trim(),
      ruleType: formData.ruleType,
      scoreType: formData.scoreType,
      scoreValue: Number(formData.scoreValue),
      accumulativeCode: formData.accumulativeCode?.trim() || '',
      minScore:
        formData.minScore !== null && formData.minScore !== '' ? Number(formData.minScore) : null,
      maxScoreLimit:
        formData.maxScoreLimit !== null && formData.maxScoreLimit !== ''
          ? Number(formData.maxScoreLimit)
          : null,
      description: formData.description?.trim() || '',
      scoringRule: formData.scoringRule?.trim() || '',
    }

    // 如果是编辑模式，添加ID
    if (drawerMode.value === 'edit' && currentDetail.value?.id) {
      saveData.id = currentDetail.value.id
    }

    let result
    if (drawerMode.value === 'edit') {
      result = await scoringRuleApi.modify(saveData)
    } else {
      result = await scoringRuleApi.add(saveData)
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

// 导入相关函数
const handleImport = () => {
  importVisible.value = true
  fileList.value = []
}

const handleFileChange = (file) => {
  // 只保留一个文件
  fileList.value = [file]
}

const handleImportSubmit = async () => {
  if (!fileList.value.length) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }

  try {
    importing.value = true
    const file = fileList.value[0].raw
    const result = await scoringRuleApi.import(file)

    if (result && result.code === 200) {
      ElMessage.success('导入成功')
      importVisible.value = false
      fileList.value = []
      fetchData()
    } else {
      ElMessage.error(result?.message || '导入失败')
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败:' + error.message)
  } finally {
    importing.value = false
  }
}

const downloadTemplate = () => {
  // 这里可以添加下载模板的逻辑
  ElMessage.info('模板下载功能待实现')
}

// 状态处理函数
const getRuleTypeTag = (ruleType) => {
  const typeMap = {
    bonus: 'success',
    penalty: 'danger',
    common: 'primary',
  }
  return typeMap[ruleType] || 'info'
}

const getRuleTypeText = (ruleType) => {
  const textMap = {
    bonus: '加分规则',
    penalty: '扣分规则',
    common: '通用规则',
  }
  return textMap[ruleType] || ruleType
}

const getScoreTypeTag = (scoreType) => {
  const typeMap = {
    fixed: 'success',
    accumulative: 'warning',
    dynamic: 'primary',
  }
  return typeMap[scoreType] || 'info'
}

const getScoreTypeText = (scoreType) => {
  const textMap = {
    fixed: '固定分值',
    accumulative: '累计分值',
    dynamic: '动态分值',
  }
  return textMap[scoreType] || scoreType
}

const getScoreValueClass = (ruleType) => {
  if (ruleType === 'bonus') {
    return 'score-positive'
  } else if (ruleType === 'penalty') {
    return 'score-negative'
  }
  return 'score-normal'
}

const getScoreValueText = (ruleType, scoreValue) => {
  const value = Number(scoreValue)
  if (ruleType === 'bonus') {
    return `+${value}`
  } else if (ruleType === 'penalty') {
    return `-${value}`
  }
  return value
}

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.scoring-rule-container {
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

.import-content {
  padding: 20px;
}

.template-download {
  text-align: center;
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
  .scoring-rule-container {
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

// 上传组件样式优化
:deep(.upload-demo) {
  .el-upload {
    width: 100%;
  }

  .el-upload-dragger {
    width: 100%;
  }
}
</style>
