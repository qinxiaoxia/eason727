<template>
  <div class="assign-columns-container">
    <!--搜索区域-->
    <el-card class="search-card" shadow="never">
      <el-form :model="queryParams" inline>
        <el-form-item label="资源列">
          <el-select
            v-model="queryParams.data.columnName"
            placeholder="请选择资源列"
            clearable
            filterable
            style="width: 300px"
            @change="handleSearch"
          >
            <el-option
              v-for="column in allAssetColumns"
              :key="column.value"
              :label="column.label"
              :value="column.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="loading">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
          <el-button @click="loadAssetColumns" :loading="loadingColumns">
            <el-icon><Refresh /></el-icon>刷新资源列
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
            添加资源列
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
          <el-tag type="info">已配置: {{ total }}个列</el-tag>
          <el-tag type="success">总资源列: {{ allAssetColumns.length }}个</el-tag>
          <el-tag type="warning">未配置: {{ unconfiguredColumns.length }}个</el-tag>
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
        class="assign-columns-table"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="配置ID" width="100" />

        <!--资源列-->
        <el-table-column prop="columnName" label="资源列" min-width="300">
          <template #default="{ row }">
            <el-tag type="primary" effect="plain" class="column-tag">
              {{ getAssetColumnLabel(row.columnName) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right" align="left">
          <template #default="{ row }">
            <div class="icon-actions">
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

    <!--新增抽屉-->
    <el-drawer
      v-model="drawerVisible"
      title="添加资源列"
      direction="rtl"
      size="600px"
      class="assign-columns-drawer"
    >
      <div class="add-columns-content">
        <!--未配置的资源列列表-->
        <div class="unconfigured-section">
          <h4>可添加的资源列 ({{ unconfiguredColumns.length }}个)</h4>
          <div class="columns-grid">
            <el-card
              v-for="column in unconfiguredColumns"
              :key="column.value"
              class="column-card"
              shadow="hover"
              @click="handleSelectColumn(column)"
            >
              <div class="column-content">
                <el-icon class="column-icon"><Grid /></el-icon>
                <div class="column-info">
                  <div class="column-label">{{ column.label }}</div>
                  <div class="column-value">{{ column.value }}</div>
                </div>
                <el-button type="primary" text @click="handleSelectColumn(column)">
                  添加
                </el-button>
              </div>
            </el-card>
          </div>

          <div v-if="unconfiguredColumns.length === 0" class="empty-tips">
            <el-empty description="所有资源列都已配置" :image-size="100" />
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Delete, Grid } from '@element-plus/icons-vue'

// 导入API - 修正导入路径
import assignColumnsApi from '@/api/services/system/assignColumns'
import assetApi from '@/api/services/asset/asset' // 导入资产管理API来获取资源列

// 响应式数据
const loading = ref(false)
const loadingColumns = ref(false)
const drawerVisible = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedRows = ref([])
const selectedColumn = ref(null)
const allAssetColumns = ref([]) // 动态获取的资源列

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  data: {
    columnName: '',
  },
})

// 计算属性：未配置的资源列
const unconfiguredColumns = computed(() => {
  const configuredColumnNames = tableData.value.map((item) => item.columnName)
  return allAssetColumns.value.filter((column) => !configuredColumnNames.includes(column.value))
})

// 动态加载资源列
const loadAssetColumns = async () => {
  loadingColumns.value = true
  try {
    // 调用资产管理接口获取资源列
    const response = await assetApi.getPageList({
      page: 1,
      limit: 1, // 只需要获取字段结构
      data: {},
    })

    console.log('资源列接口响应:', response)

    if (response && response.code === 200) {
      // 从接口响应中提取字段信息
      const fields = extractFieldsFromResponse(response)
      allAssetColumns.value = fields
      ElMessage.success(`成功加载 ${fields.length} 个资源列`)
    } else {
      ElMessage.error('获取资源列失败，使用默认配置')
      // 如果接口失败，使用默认字段
      loadDefaultAssetColumns()
    }
  } catch (error) {
    console.error('加载资源列失败:', error)
    ElMessage.error('加载资源列失败，使用默认配置')
    // 如果接口失败，使用默认字段
    loadDefaultAssetColumns()
  } finally {
    loadingColumns.value = false
  }
}

// 从接口响应中提取字段信息
const extractFieldsFromResponse = (response) => {
  try {
    const fields = []

    // 尝试从data数组的第一个对象提取字段
    if (response && response.data && Array.isArray(response.data) && response.data.length > 0) {
      const sampleData = response.data[0]

      if (sampleData && typeof sampleData === 'object') {
        Object.keys(sampleData).forEach((key) => {
          // 过滤掉一些系统字段
          const excludeFields = ['createTime', 'updateTime', 'creator', 'updater', 'deleted']
          if (!excludeFields.includes(key)) {
            fields.push({
              value: key,
              label: formatFieldLabel(key),
            })
          }
        })
      }
    }

    // 如果提取到字段，返回提取的结果
    if (fields.length > 0) {
      return fields
    }

    // 否则返回默认字段
    return getDefaultAssetColumns()
  } catch (error) {
    console.error('提取字段时出错:', error)
    return getDefaultAssetColumns()
  }
}

// 格式化字段标签
const formatFieldLabel = (fieldName) => {
  const labelMap = {
    id: '资产ID',
    systemName: '系统名称',
    assetType: '资产类型',
    ipAddress: 'IP地址',
    domainName: '域名',
    networkLevel: '网络层级',
    organization: '所属组织',
    teamName: '分配队伍',
    isTarget: '是否靶标',
    isMonitored: '是否监控',
    province: '省份',
    city: '城市',
    ports: '端口',
    internalIpRange: '内部IP范围',
    url: 'URL地址',
    os: '操作系统',
    serviceType: '服务类型',
  }

  return labelMap[fieldName] || fieldName
}

// 加载默认资源列（备用）
const loadDefaultAssetColumns = () => {
  allAssetColumns.value = getDefaultAssetColumns()
}

// 获取默认资源列
const getDefaultAssetColumns = () => {
  return [
    { value: 'id', label: '资产ID' },
    { value: 'systemName', label: '系统名称' },
    { value: 'assetType', label: '资产类型' },
    { value: 'ipAddress', label: 'IP地址' },
    { value: 'domainName', label: '域名' },
    { value: 'networkLevel', label: '网络层级' },
    { value: 'organization', label: '所属组织' },
    { value: 'teamName', label: '分配队伍' },
    { value: 'isTarget', label: '是否靶标' },
    { value: 'isMonitored', label: '是否监控' },
    { value: 'province', label: '省份' },
    { value: 'city', label: '城市' },
    { value: 'ports', label: '端口' },
    { value: 'internalIpRange', label: '内部IP范围' },
    { value: 'url', label: 'URL地址' },
    { value: 'os', label: '操作系统' },
    { value: 'serviceType', label: '服务类型' },
  ]
}

// 根据列值获取列标签
const getAssetColumnLabel = (columnValue) => {
  const column = allAssetColumns.value.find((col) => col.value === columnValue)
  return column ? column.label : columnValue
}

// 获取已配置的列列表
const getPageList = async () => {
  loading.value = true
  try {
    const response = await assignColumnsApi.getPageList(queryParams)
    console.log('配置列表接口响应:', response)

    if (response && response.code === 200) {
      tableData.value = response.data || []
      total.value = response.count || 0
    } else {
      tableData.value = []
      total.value = 0
      ElMessage.error(response?.message || '获取配置列表失败')
    }
  } catch (error) {
    console.error('获取配置列表失败:', error)
    ElMessage.error('获取配置列表失败')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 打开添加抽屉
const handleAdd = () => {
  if (unconfiguredColumns.value.length === 0) {
    ElMessage.warning('所有资源列都已配置')
    return
  }
  drawerVisible.value = true
}

// 选择资源列
const handleSelectColumn = async (column) => {
  try {
    selectedColumn.value = column
    await ElMessageBox.confirm(`确定要添加资源列"${column.label}"吗？`, '添加确认', {
      type: 'info',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })

    // 调用新增接口
    const response = await assignColumnsApi.add({
      columnName: column.value,
    })

    if (response && response.code === 200) {
      ElMessage.success(`成功添加资源列"${column.label}"`)
      drawerVisible.value = false
      getPageList()
    } else {
      ElMessage.error(response?.message || '添加失败')
    }
  } catch {
    // 用户取消
    console.log('用户取消添加')
  }
}

// 删除配置
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个资源列配置吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })

    const response = await assignColumnsApi.batchRemove([id])
    if (response && response.code === 200) {
      ElMessage.success('删除成功')
      getPageList()
    } else {
      ElMessage.error(response?.message || '删除失败')
    }
  } catch {
    // 用户点击取消
    console.log('用户取消删除')
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要删除的配置')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个配置吗？`,
      '批量删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      },
    )

    const ids = selectedRows.value.map((item) => item.id)
    const response = await assignColumnsApi.batchRemove(ids)
    if (response && response.code === 200) {
      ElMessage.success(`成功删除 ${selectedRows.value.length} 个配置`)
      selectedRows.value = []
      getPageList()
    } else {
      ElMessage.error(response?.message || '删除失败')
    }
  } catch {
    // 用户点击取消
    console.log('用户取消批量删除')
  }
}

// 搜索处理
const handleSearch = () => {
  queryParams.page = 1
  getPageList()
}

const handleReset = () => {
  Object.assign(queryParams, {
    page: 1,
    limit: 20,
    data: {
      columnName: '',
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

// 初始化
onMounted(() => {
  loadAssetColumns() // 动态加载资源列
  getPageList() // 加载配置列表
})
</script>

<style scoped lang="scss">
/* 样式保持不变，与之前相同 */
.assign-columns-container {
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

.column-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
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

.add-columns-content {
  padding: 0 20px;

  .unconfigured-section {
    h4 {
      margin: 0 0 16px 0;
      color: #1f2937;
    }

    .columns-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 16px;
      max-height: 500px;
      overflow-y: auto;

      .column-card {
        cursor: pointer;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .column-content {
          display: flex;
          align-items: center;
          gap: 12px;

          .column-icon {
            font-size: 24px;
            color: #3b82f6;
          }

          .column-info {
            flex: 1;

            .column-label {
              font-weight: 500;
              color: #1f2937;
            }

            .column-value {
              font-size: 12px;
              color: #6b7280;
            }
          }
        }
      }
    }

    .empty-tips {
      text-align: center;
      padding: 40px 0;
    }
  }
}

.action-btn {
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-1px);
  }
}

// 响应式适配
@media (max-width: 768px) {
  .assign-columns-container {
    padding: 16px;
  }

  .operation-container {
    flex-direction: column;
    gap: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr !important;
  }

  .columns-grid {
    grid-template-columns: 1fr !important;
  }
}
</style>
