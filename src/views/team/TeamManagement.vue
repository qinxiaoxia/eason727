<template>
  <div class="team-management-container">
    <!-- 搜索区域（保持不变） -->
    <el-card class="search-card" shadow="never">
      <el-form :model="queryParams" inline>
        <el-form-item label="队伍名称">
          <el-input
            v-model="queryParams.data.teamName"
            placeholder="请输入队伍名称"
            clearable
            style="width: 220px"
            @input="handleSearch"
            @keyup.enter="handleImmediateSearch"
            @clear="handleReset"
          />
        </el-form-item>
        <el-form-item label="队伍类型">
          <el-select
            v-model="queryParams.data.teamType"
            placeholder="请选择队伍类型"
            clearable
            style="width: 220px"
            @change="handleSearch"
          >
            <el-option label="攻击队伍" value="attack" />
            <el-option label="防守队伍" value="defense" />
            <el-option label="裁判队伍" value="judge" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作区域（保持不变） -->
    <el-card class="operation-card" shadow="never">
      <div class="operation-container">
        <div class="operation-left">
          <el-button type="primary" @click="handleAdd" class="action-btn">
            <el-icon><Plus /></el-icon>
            新增队伍
          </el-button>
          <el-button
            :disabled="selectedRows.length === 0"
            @click="handleBatchDelete"
            class="action-btn"
          >
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
        </div>
        <div class="operation-stats">
          <el-tag type="info">共{{ total }}个队伍</el-tag>
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

    <!-- 表格区域 -->
    <el-card shadow="never" class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        @selection-change="handleSelectionChange"
        stripe
        style="width: 100%"
        class="team-table"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="teamName" label="队伍名称" width="180" />
        <el-table-column prop="teamShortName" label="队伍简称" width="180" />
        <el-table-column prop="teamType" label="队伍类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getTeamTypeTag(row.teamType)" effect="light">
              {{ getTeamTypeText(row.teamType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="teamNature" label="队伍性质" min-width="100" />
        <el-table-column prop="industry" label="所属行业" width="180" show-overflow-tooltip />
        <el-table-column prop="province" label="省份" width="120" />
        <el-table-column prop="city" label="城市" width="120" />

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
                <el-icon class="action-icon" @click="handleDelete(row.id)">
                  <Delete />
                </el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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

    <!-- 新增/编辑抽屉（保持不变） -->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      direction="rtl"
      size="800px"
      class="team-drawer wide-drawer"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="队伍名称" prop="teamName">
              <el-input
                v-model="formData.teamName"
                placeholder="请输入队伍名称"
                maxlength="50"
                show-word-limit
                class="custom-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="队伍简称" prop="teamShortName">
              <el-input
                v-model="formData.teamShortName"
                placeholder="请输入队伍简称"
                maxlength="20"
                show-word-limit
                class="custom-input"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="队伍类型" prop="teamType">
              <el-select
                v-model="formData.teamType"
                placeholder="请选择队伍类型"
                class="custom-input"
              >
                <el-option label="攻击队伍" value="attack" />
                <el-option label="防守队伍" value="defense" />
                <el-option label="裁判队伍" value="judge" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="队伍性质" prop="teamNature">
              <el-input
                v-model="formData.teamNature"
                placeholder="请输入队伍性质"
                maxlength="50"
                show-word-limit
                class="custom-input"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所属行业" prop="industry">
              <el-input
                v-model="formData.industry"
                placeholder="请输入所属行业"
                maxlength="50"
                show-word-limit
                class="custom-input"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="省份" prop="province">
              <el-input
                v-model="formData.province"
                placeholder="请输入省份"
                maxlength="20"
                class="custom-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="城市" prop="city">
              <el-input
                v-model="formData.city"
                placeholder="请输入城市"
                maxlength="20"
                class="custom-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="区县" prop="district">
              <el-input
                v-model="formData.district"
                placeholder="请输入区县"
                maxlength="20"
                class="custom-input"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="详细地址" prop="address">
          <el-input
            v-model="formData.address"
            type="textarea"
            rows="3"
            placeholder="请输入详细地址"
            maxlength="200"
            show-word-limit
            resize="none"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <div class="footer-left">
            <el-tag v-if="drawerMode === 'edit'" type="info" size="large">
              队伍ID: {{ formData.id }}
            </el-tag>
          </div>
          <div class="footer-right">
            <el-button @click="drawerVisible = false" class="cancel-btn">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving" class="save-btn">
              <el-icon><Check /></el-icon>
              保存
            </el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <!-- 详情抽屉（保持不变） -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="队伍详情"
      direction="rtl"
      size="1000px"
      class="detail-drawer"
    >
      <el-descriptions :column="2" border v-if="currentTeamDetail">
        <el-descriptions-item label="队伍ID">
          {{ currentTeamDetail.id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="队伍名称">
          {{ currentTeamDetail.teamName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="队伍简称">
          {{ currentTeamDetail.teamShortName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="队伍类型">
          <el-tag :type="getTeamTypeTag(currentTeamDetail.teamType)" effect="light">
            {{ getTeamTypeText(currentTeamDetail.teamType) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="队伍性质">
          {{ currentTeamDetail.teamNature || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="所属行业">
          {{ currentTeamDetail.industry || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="省份">
          {{ currentTeamDetail.province || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="城市">
          {{ currentTeamDetail.city || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="区县">
          {{ currentTeamDetail.district || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="详细地址" :span="2">
          {{ currentTeamDetail.address || '-' }}
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
import { onMounted, ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, Delete, View, Edit, Check } from '@element-plus/icons-vue'
import teamApi from '@/api/services/team/team'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const total = ref(0)
const drawerVisible = ref(false)
const drawerTitle = ref('')
const drawerMode = ref('add') // 'add' | 'edit'
const selectedRows = ref([])
const detailDrawerVisible = ref(false)
const currentTeamDetail = ref(null)

// 表单引用
const formRef = ref()

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  data: {
    teamName: '',
    teamType: '',
    teamShortName: '',
    industry: '',
    province: '',
    city: '',
  },
  hasTimeRange: 0,
  timeField: 'createTime',
})

// 表单数据
const formData = reactive({
  id: '',
  teamName: '',
  teamShortName: '',
  teamType: '',
  teamNature: '',
  industry: '',
  province: '',
  city: '',
  district: '',
  address: '',
})

// 表单验证规则
const rules = {
  teamName: [
    { required: true, message: '队伍名称不能为空', trigger: 'blur' },
    { min: 2, max: 50, message: '队伍名称长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  teamShortName: [
    { required: true, message: '队伍简称不能为空', trigger: 'blur' },
    { min: 2, max: 20, message: '队伍简称长度在 2 到 20 个字符', trigger: 'blur' },
  ],
  teamType: [{ required: true, message: '请选择队伍类型', trigger: 'change' }],
}

// 队伍类型标签映射
const getTeamTypeTag = (type) => {
  const typeMap = {
    attack: 'danger',
    defense: 'success',
    judge: 'warning',
  }
  return typeMap[type] || 'info'
}

const getTeamTypeText = (type) => {
  const textMap = {
    attack: '攻击队伍',
    defense: '防守队伍',
    judge: '裁判队伍',
  }
  return textMap[type] || type
}

// 获取队伍列表
const getPageList = async () => {
  loading.value = true
  try {
    const response = await teamApi.getPageList(queryParams)
    console.log('队伍列表接口返回数据:', response)
    if (response && response.code === 200) {
      // 修复：适配后端返回格式
      tableData.value = response.data || []
      total.value = response.count || 0
      // 同步分页参数
      queryParams.page = response.page || 1
      queryParams.limit = response.limit || 20
    } else {
      tableData.value = []
      total.value = 0
      ElMessage.error(response?.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取队伍列表失败:', error)
    ElMessage.error('获取数据失败')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 搜索防抖
let searchTimer = null
const handleSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    queryParams.page = 1
    getPageList()
  }, 500)
}

// 立即搜索
const handleImmediateSearch = () => {
  queryParams.page = 1
  getPageList()
}

// 重置搜索
const handleReset = () => {
  Object.assign(queryParams, {
    page: 1,
    limit: 20,
    data: {
      teamName: '',
      teamType: '',
      teamShortName: '',
      industry: '',
      province: '',
      city: '',
    },
    hasTimeRange: 0,
  })
  getPageList()
}

// 刷新
const handleRefresh = () => {
  getPageList()
  ElMessage.success('数据已刷新')
}

// 新增队伍
const handleAdd = () => {
  drawerMode.value = 'add'
  drawerTitle.value = '新增队伍'
  // 重置表单数据
  Object.keys(formData).forEach((key) => {
    formData[key] = ''
  })
  drawerVisible.value = true
}

// 编辑队伍 - 修复：正确赋值表单数据
const handleEdit = async (row) => {
  drawerMode.value = 'edit'
  drawerTitle.value = '编辑队伍'

  // 修复：正确设置表单数据
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
  currentTeamDetail.value = { ...row }
  detailDrawerVisible.value = true
}

// 保存队伍
const handleSave = async () => {
  try {
    if (!formRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }

    // 表单验证
    await formRef.value.validate()
    saving.value = true

    // 准备提交数据
    const submitData = { ...formData }
    let response

    if (drawerMode.value === 'edit') {
      response = await teamApi.modify(submitData)
    } else {
      response = await teamApi.add(submitData)
    }

    if (response && response.code === 200) {
      ElMessage.success(drawerMode.value === 'add' ? '新增成功' : '修改成功')
      drawerVisible.value = false
      getPageList()
    } else {
      ElMessage.error(response?.message || '操作失败')
    }
  } catch (error) {
    console.error('保存队伍失败:', error)
    if (error.errors) {
      ElMessage.error('请检查表单填写是否正确')
    } else {
      ElMessage.error('保存失败: ' + (error.message || '未知错误'))
    }
  } finally {
    saving.value = false
  }
}

// 删除队伍 - 修复：接口路径问题
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该队伍吗?', '提示', {
      type: 'warning',
    })

    console.log('🗑️ 准备删除队伍ID:', id)

    // 复用批量删除接口，但只传一个ID
    const response = await teamApi.batchRemove([id])

    console.log('✅ 删除接口返回:', response)

    if (response && response.code === 200) {
      ElMessage.success('删除成功')
      getPageList()
    } else {
      ElMessage.error(response?.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('❌ 删除失败:', error)
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要删除的队伍')
    return
  }

  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedRows.value.length} 个队伍吗?`, '提示', {
      type: 'warning',
    })

    const ids = selectedRows.value.map((item) => item.id)
    const response = await teamApi.batchRemove(ids)

    if (response && response.code === 200) {
      ElMessage.success(`成功删除 ${selectedRows.value.length} 个队伍`)
      selectedRows.value = []
      getPageList()
    } else {
      ElMessage.error(response?.message || '批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 表格选择变化
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 分页变化
const handleSizeChange = (newSize) => {
  queryParams.limit = newSize
  queryParams.page = 1
  getPageList()
}

const handleCurrentChange = (newPage) => {
  queryParams.page = newPage
  getPageList()
}

// 初始化
onMounted(() => {
  getPageList()
})
</script>

<style scoped lang="scss">
.team-management-container {
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

.team-table {
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

.action-icons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.time-cell {
  .time-text {
    font-size: 13px;
    color: #6b7280;
  }

  .no-data {
    color: #9ca3af;
    font-style: italic;
    font-size: 13px;
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

.team-drawer {
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

.custom-textarea {
  :deep(.el-textarea__inner) {
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    transition: all 0.3s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

    &:hover {
      border-color: #cbd5e0;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }

    &:focus {
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

    .no-selection {
      color: #9ca3af;
      font-size: 14px;
      font-style: italic;
    }
  }

  .footer-right {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

// 响应式适配
@media (max-width: 768px) {
  .drawer-footer {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;

    .footer-left {
      justify-content: center;
      order: 2;
    }

    .footer-right {
      justify-content: center;
      order: 1;
    }
  }
}

@media (max-width: 480px) {
  .drawer-footer {
    .footer-right {
      flex-direction: column;
      width: 100%;

      .cancel-btn,
      .save-btn {
        width: 100%;
        justify-content: center;
      }
    }
  }
}

.detail-drawer {
  :deep(.el-drawer) {
    box-shadow: -4px 0 16px rgba(0, 0, 0, 0.1);

    .el-drawer__header {
      padding: 20px 24px;
      margin-bottom: 0;
      border-bottom: 1px solid #e5e7eb;

      .el-drawer__title {
        font-weight: 600;
        color: #1f2937;
        font-size: 18px;
      }
    }

    .el-drawer__body {
      padding: 20px 24px;
      height: calc(100% - 80px);
      overflow-y: auto;
    }
  }

  :deep(.el-descriptions) {
    margin-top: 8px;

    .el-descriptions__label {
      font-weight: 500;
      color: #374151;
      background-color: #f8fafc;
    }

    .el-descriptions__content {
      color: #6b7280;
    }
  }
}
.icon-actions {
  display: flex;
  gap: 12px;
  justify-content: left;
  align-items: center;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.action-btn {
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .team-management-container {
    padding: 16px;
  }

  .operation-container {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
}

@media (max-width: 768px) {
  .team-management-container {
    padding: 12px;
  }

  .search-card,
  .operation-card {
    margin-bottom: 16px;

    :deep(.el-card__body) {
      padding: 16px;
    }
  }

  .action-icons {
    gap: 4px;

    .action-icon {
      width: 28px;
      height: 28px;
    }
  }

  .team-drawer,
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
  .team-management-container {
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

  .action-icons {
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px;

    .action-icon {
      width: 24px;
      height: 24px;
    }
  }
}

// 动画效果
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// 滚动条样式优化
:deep(.el-table__body-wrapper)::-webkit-scrollbar,
:deep(.el-drawer__body)::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-track,
:deep(.el-drawer__body)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb,
:deep(.el-drawer__body)::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover,
:deep(.el-drawer__body)::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
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

// 抽屉动画
.drawer-enter-active,
.drawer-leave-active {
  transition: all 0.3s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(100%);
  opacity: 0;
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

:deep(.el-input__wrapper) {
  border-radius: 6px;
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

.no-data {
  color: #9ca3af;
  font-style: italic;
  font-size: 13px;
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

// 抽屉底部按钮组
.drawer-footer {
  .el-button {
    min-width: 80px;
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

.icon-actions {
  display: flex;
  gap: 12px;
  justify-content: left;
  align-items: center;
}
</style>
