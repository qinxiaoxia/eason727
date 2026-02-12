<template>
  <div class="menu-management-container">
    <!-- 操作区域 -->
    <el-card class="operation-card" shadow="never">
      <div class="operation-container">
        <div class="operation-left">
          <el-button type="primary" @click="handleAdd" class="action-btn">
            <el-icon><Plus /></el-icon>
            新增菜单
          </el-button>
          <el-button
            :disabled="selectedRows.length === 0"
            @click="handleBatchDelete"
            class="action-btn"
          >
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
          <el-button @click="handleExpandAll" class="action-btn">
            <el-icon><Expand /></el-icon>
            展开全部
          </el-button>
          <el-button @click="handleCollapseAll" class="action-btn">
            <el-icon><Fold /></el-icon>
            折叠全部
          </el-button>
        </div>
        <div class="operation-stats">
          <el-tag type="info">共 {{ total }} 个菜单</el-tag>
          <el-tag v-if="selectedRows.length > 0" type="warning">
            已选 {{ selectedRows.length }} 项
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
        ref="menuTableRef"
        v-loading="loading"
        :data="tableData"
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        @selection-change="handleSelectionChange"
        stripe
        style="width: 100%"
        class="menu-table"
        default-expand-all
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="菜单ID" width="100" />
        <el-table-column prop="menuName" label="菜单名称" width="200">
          <template #default="{ row }">
            <div class="menu-name-cell">
              <el-icon v-if="row.icon" class="menu-icon">
                <component :is="row.icon" />
              </el-icon>
              <span>{{ row.menuName }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="menuType" label="菜单类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getMenuTypeTagType(row.menuType)" effect="light">
              {{ getMenuTypeText(row.menuType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="perms" label="权限标识" width="150" show-overflow-tooltip />
        <el-table-column prop="url" label="菜单路径" min-width="200" show-overflow-tooltip />
        <el-table-column prop="orderNum" label="排序" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.orderNum" type="info" effect="plain">
              {{ row.orderNum }}
            </el-tag>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="visible" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.visible === '1' ? 'success' : 'danger'" effect="light">
              {{ row.visible === '1' ? '显示' : '隐藏' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180">
          <template #default="{ row }">
            <div class="time-cell">
              <span v-if="row.createTime" class="time-text">
                {{ formatDateTime(row.createTime) }}
              </span>
              <span v-else class="no-data">-</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-icons">
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
              <el-tooltip content="添加子菜单" placement="top">
                <el-icon class="action-icon" @click="handleAddChild(row)">
                  <Plus />
                </el-icon>
              </el-tooltip>
              <el-tooltip :content="row.visible === '1' ? '隐藏菜单' : '显示菜单'" placement="top">
                <el-icon
                  class="action-icon"
                  :class="row.visible === '1' ? 'hide-icon' : 'show-icon'"
                  @click="handleToggleVisible(row)"
                >
                  <component :is="row.visible === '1' ? 'Hide' : 'View'" />
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
    </el-card>

    <!-- 新增/编辑抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      direction="rtl"
      size="600px"
      class="menu-drawer"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="父级菜单">
          <el-cascader
            v-model="formData.parentId"
            :options="menuTreeOptions"
            :props="cascaderProps"
            placeholder="请选择父级菜单"
            clearable
            style="width: 100%"
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="菜单名称" prop="menuName">
              <el-input
                v-model="formData.menuName"
                placeholder="请输入菜单名称"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="菜单类型" prop="menuType">
              <el-select
                v-model="formData.menuType"
                placeholder="请选择菜单类型"
                style="width: 100%"
                @change="handleMenuTypeChange"
              >
                <el-option label="目录" value="M" />
                <el-option label="菜单" value="C" />
                <el-option label="按钮" value="F" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item v-if="formData.menuType !== 'F'" label="菜单图标">
          <el-input
            v-model="formData.icon"
            placeholder="请输入图标名称"
            maxlength="50"
            show-word-limit
          >
            <template #prefix>
              <el-icon v-if="formData.icon">
                <component :is="formData.icon" />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item v-if="formData.menuType === 'C'" label="菜单路径" prop="url">
          <el-input
            v-model="formData.url"
            placeholder="请输入菜单路径"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item v-if="formData.menuType !== 'M'" label="权限标识" prop="perms">
          <el-input
            v-model="formData.perms"
            placeholder="请输入权限标识"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="显示排序" prop="orderNum">
              <el-input-number
                v-model="formData.orderNum"
                :min="0"
                :max="999"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="显示状态" prop="visible">
              <el-radio-group v-model="formData.visible">
                <el-radio label="1">显示</el-radio>
                <el-radio label="0">隐藏</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input
            v-model="formData.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="loading">保存</el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="菜单详情"
      direction="rtl"
      size="700px"
      class="detail-drawer"
    >
      <el-descriptions :column="2" border v-if="currentMenuDetail">
        <el-descriptions-item label="菜单ID">
          {{ currentMenuDetail.id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="菜单名称">
          <div class="menu-detail-name">
            <el-icon v-if="currentMenuDetail.icon" class="menu-icon">
              <component :is="currentMenuDetail.icon" />
            </el-icon>
            {{ currentMenuDetail.menuName || '-' }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="菜单类型">
          <el-tag :type="getMenuTypeTagType(currentMenuDetail.menuType)" effect="light">
            {{ getMenuTypeText(currentMenuDetail.menuType) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="父级菜单">
          {{ currentMenuDetail.parentName || '根目录' }}
        </el-descriptions-item>
        <el-descriptions-item label="权限标识">
          {{ currentMenuDetail.perms || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="菜单路径">
          {{ currentMenuDetail.url || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="显示排序">
          <el-tag type="info" effect="plain">
            {{ currentMenuDetail.orderNum || '0' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="显示状态">
          <el-tag :type="currentMenuDetail.visible === '1' ? 'success' : 'danger'" effect="light">
            {{ currentMenuDetail.visible === '1' ? '显示' : '隐藏' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ currentMenuDetail.createTime ? formatDateTime(currentMenuDetail.createTime) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间" :span="2">
          {{ currentMenuDetail.updateTime ? formatDateTime(currentMenuDetail.updateTime) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ currentMenuDetail.remark || '-' }}
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
import { Refresh, Plus, Delete, View, Edit, Expand, Fold } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/time'
import menuApi from '@/api/services/system/menu'

// 响应式数据
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const drawerVisible = ref(false)
const drawerTitle = ref('')
const selectedRows = ref([])
const detailDrawerVisible = ref(false)
const currentMenuDetail = ref(null)
const menuTableRef = ref()

// 表单引用
const formRef = ref()

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 1000, // 树形数据需要获取全部
  data: {
    menuName: '',
    menuType: '',
    visible: '',
  },
})

// 表单数据
const formData = reactive({
  id: '',
  parentId: [],
  menuName: '',
  menuType: 'C',
  icon: '',
  perms: '',
  url: '',
  orderNum: 0,
  visible: '1',
  remark: '',
})

// 菜单树选项（用于级联选择器）
const menuTreeOptions = ref([])
const cascaderProps = {
  value: 'id',
  label: 'menuName',
  children: 'children',
  checkStrictly: true,
}

// 表单验证规则
const rules = {
  menuName: [
    { required: true, message: '菜单名称不能为空', trigger: 'blur' },
    { min: 2, max: 50, message: '菜单名称长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  menuType: [{ required: true, message: '请选择菜单类型', trigger: 'change' }],
  url: [
    {
      validator: (rule, value, callback) => {
        if (formData.menuType === 'C' && !value) {
          callback(new Error('菜单路径不能为空'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  perms: [
    {
      validator: (rule, value, callback) => {
        if (formData.menuType !== 'M' && !value) {
          callback(new Error('权限标识不能为空'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 获取菜单列表（树形结构）
const getPageList = async () => {
  loading.value = true
  try {
    const response = await menuApi.getPageList(queryParams)
    // 将扁平数据转换为树形结构
    const flatData = response.data || []
    tableData.value = buildMenuTree(flatData)
    total.value = flatData.length
    // 同时生成菜单树选项
    menuTreeOptions.value = buildMenuTree(flatData.filter((item) => item.menuType === 'M'))
  } catch (error) {
    console.error('获取菜单列表失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 构建菜单树
const buildMenuTree = (data) => {
  const map = {}
  const tree = []

  data.forEach((item) => {
    map[item.id] = { ...item, children: [] }
  })

  data.forEach((item) => {
    if (item.parentId && map[item.parentId]) {
      map[item.parentId].children.push(map[item.id])
    } else {
      tree.push(map[item.id])
    }
  })

  return tree
}

// 获取菜单类型文本
const getMenuTypeText = (type) => {
  const typeMap = {
    M: '目录',
    C: '菜单',
    F: '按钮',
  }
  return typeMap[type] || type
}

// 获取菜单类型标签样式
const getMenuTypeTagType = (type) => {
  const typeMap = {
    M: 'primary',
    C: 'success',
    F: 'warning',
  }
  return typeMap[type] || 'info'
}

// 刷新
const handleRefresh = () => {
  getPageList()
  ElMessage.success('数据已刷新')
}

// 展开全部
const handleExpandAll = () => {
  tableData.value.forEach((row) => {
    menuTableRef.value.toggleRowExpansion(row, true)
  })
}

// 折叠全部
const handleCollapseAll = () => {
  tableData.value.forEach((row) => {
    menuTableRef.value.toggleRowExpansion(row, false)
  })
}

// 新增菜单
const handleAdd = () => {
  drawerTitle.value = '新增菜单'
  Object.assign(formData, {
    id: '',
    parentId: [],
    menuName: '',
    menuType: 'C',
    icon: '',
    perms: '',
    url: '',
    orderNum: 0,
    visible: '1',
    remark: '',
  })
  drawerVisible.value = true
}

// 添加子菜单
const handleAddChild = (row) => {
  drawerTitle.value = '添加子菜单'
  Object.assign(formData, {
    id: '',
    parentId: [row.id],
    menuName: '',
    menuType: row.menuType === 'M' ? 'C' : 'F',
    icon: '',
    perms: '',
    url: '',
    orderNum: 0,
    visible: '1',
    remark: '',
  })
  drawerVisible.value = true
}

// 编辑菜单
const handleEdit = (row) => {
  drawerTitle.value = '编辑菜单'
  Object.assign(formData, {
    id: row.id,
    parentId: row.parentId ? [row.parentId] : [],
    menuName: row.menuName,
    menuType: row.menuType,
    icon: row.icon || '',
    perms: row.perms || '',
    url: row.url || '',
    orderNum: row.orderNum || 0,
    visible: row.visible || '1',
    remark: row.remark || '',
  })
  drawerVisible.value = true
}

// 查看详情
const handleViewDetail = (row) => {
  currentMenuDetail.value = { ...row }
  detailDrawerVisible.value = true
}

// 菜单类型变化处理
const handleMenuTypeChange = (value) => {
  if (value === 'M') {
    formData.url = ''
    formData.perms = ''
  } else if (value === 'C') {
    formData.perms = ''
  }
}

// 保存菜单
const handleSave = async () => {
  try {
    if (!formRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }
    await formRef.value.validate()

    loading.value = true

    const submitData = {
      ...formData,
      parentId: formData.parentId.length > 0 ? formData.parentId[formData.parentId.length - 1] : 0,
    }

    let response
    if (formData.id) {
      response = await menuApi.editMenu(submitData)
    } else {
      response = await menuApi.addMenu(submitData)
    }

    if (response.code === 200) {
      ElMessage.success(formData.id ? '修改成功' : '新增成功')
      drawerVisible.value = false
      getPageList()
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('保存菜单失败:', error)
    if (error.errors) {
      ElMessage.error('请检查表单填写是否正确')
    } else {
      ElMessage.error('保存失败:' + (error.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}

// 删除菜单
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该菜单吗?', '提示', {
      type: 'warning',
    })

    const response = await menuApi.removeMenu(id)
    if (response.code === 200) {
      ElMessage.success('删除成功')
      getPageList()
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要删除的菜单')
    return
  }

  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedRows.value.length} 个菜单吗?`, '提示', {
      type: 'warning',
    })

    const ids = selectedRows.value.map((item) => item.id)
    const response = await menuApi.batchRemoveMenus(ids)
    if (response.code === 200) {
      ElMessage.success(`成功删除 ${selectedRows.value.length} 个菜单`)
      selectedRows.value = []
      getPageList()
    } else {
      ElMessage.error(response.message || '批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 切换显示状态
const handleToggleVisible = async (row) => {
  const newVisible = row.visible === '1' ? '0' : '1'
  const visibleText = newVisible === '1' ? '显示' : '隐藏'

  try {
    await ElMessageBox.confirm(`确定${visibleText}菜单"${row.menuName}"吗?`, '状态确认', {
      type: 'warning',
    })

    loading.value = true

    const response = await menuApi.editMenu({
      ...row,
      visible: newVisible,
    })

    if (response.code === 200) {
      ElMessage.success(`${visibleText}成功`)
      getPageList()
    } else {
      ElMessage.error(response.message || `${visibleText}失败`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('状态切换失败:', error)
      ElMessage.error('状态切换失败')
    }
  } finally {
    loading.value = false
  }
}

// 表格选择变化
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 初始化
onMounted(() => {
  getPageList()
})
</script>

<style scoped lang="scss">
.menu-management-container {
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

.menu-table {
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

  .menu-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .menu-icon {
      color: #64748b;
    }
  }

  .action-icons {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;

    .action-icon {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.3s ease;
      color: #64748b;
      background: transparent;
      border: none;

      &:hover {
        color: #3b82f6;
        background-color: #f1f5f9;
        transform: scale(1.1);
      }

      &.delete-icon:hover {
        color: #ef4444;
        background-color: #fef2f2;
      }

      &.hide-icon:hover {
        color: #f59e0b;
        background-color: #fffbeb;
      }

      &.show-icon:hover {
        color: #10b981;
        background-color: #f0fdf4;
      }
    }
  }
}

.time-cell {
  .time-text {
    font-size: 13px;
    color: #6b7280;
  }
}

.no-data {
  color: #9ca3af;
  font-style: italic;
  font-size: 13px;
}

.pagination-container {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  background: #fff;
}

// 抽屉样式
.menu-drawer,
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

      .el-form-item {
        margin-bottom: 20px;

        &:last-child {
          margin-bottom: 0;
        }
      }
    }

    .el-drawer__footer {
      padding: 20px 24px;
      border-top: 1px solid #e5e7eb;
    }
  }
}

.detail-drawer {
  :deep(.el-drawer__body) {
    .el-descriptions {
      margin-top: 8px;

      .el-descriptions__label {
        font-weight: 500;
        color: #374151;
        background-color: #f8fafc;
      }

      .el-descriptions__content {
        color: #6b7280;
      }

      .menu-detail-name {
        display: flex;
        align-items: center;
        gap: 8px;

        .menu-icon {
          color: #64748b;
        }
      }
    }
  }
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.action-btn {
  border-radius: 6px;
  font-weight: 500;

  &:hover {
    transform: translateY(-1px);
    transition: all 0.2s ease;
  }
}

// 菜单类型标签样式
:deep(.el-tag) {
  &.el-tag--primary {
    background: #eff6ff;
    border-color: #dbeafe;
    color: #1d4ed8;
  }

  &.el-tag--success {
    background: #f0fdf4;
    border-color: #dcfce7;
    color: #166534;
  }

  &.el-tag--warning {
    background: #fffbeb;
    border-color: #fef3c7;
    color: #92400e;
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .menu-management-container {
    padding: 16px;
  }

  .operation-container {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .menu-drawer,
  .detail-drawer {
    :deep(.el-drawer) {
      width: 90% !important;
    }
  }
}

@media (max-width: 768px) {
  .menu-management-container {
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

  .menu-drawer,
  .detail-drawer {
    :deep(.el-drawer) {
      width: 95% !important;

      .el-drawer__header {
        padding: 16px 20px;
      }

      .el-drawer__body {
        padding: 16px 20px;
      }

      .el-drawer__footer {
        padding: 16px 20px;
      }
    }
  }
}

@media (max-width: 480px) {
  .menu-management-container {
    padding: 8px;
  }

  .operation-container .operation-left {
    flex-direction: column;
    align-items: stretch;
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
    .path {
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

  &.hide-icon:hover::before {
    background: rgba(245, 158, 11, 0.1);
  }

  &.show-icon:hover::before {
    background: rgba(16, 185, 129, 0.1);
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

// 级联选择器样式
:deep(.el-cascader) {
  width: 100%;
}

// 输入数字样式
:deep(.el-input-number) {
  width: 100%;
}

// 菜单图标输入框样式
:deep(.el-input-group__prepend) {
  .el-icon {
    color: #64748b;
  }
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

// 表格操作列固定
:deep(.el-table__fixed-right) {
  .action-icons {
    padding: 0 8px;
  }
}

// 时间显示样式
.time-text {
  font-size: 13px;
  color: #6b7280;
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

// 图标大小统一
.action-icon {
  font-size: 16px;
}

// 操作列图标间距优化
.action-icons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;

  @media (max-width: 480px) {
    gap: 4px;
    flex-wrap: wrap;
  }
}

// 树形表格样式
:deep(.el-table__row) {
  .el-table__expand-icon {
    color: #64748b;

    &:hover {
      color: #3b82f6;
    }
  }
}

// 菜单名称样式
.menu-name-cell {
  font-weight: 500;
  color: #374151;
}

// 详情页样式
.menu-detail-name {
  font-weight: 500;
  color: #374151;
}
</style>
