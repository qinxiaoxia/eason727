<template>
  <div class="role-management-container">
    <!-- 搜索区域 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="queryParams" inline>
        <el-form-item label="角色名称">
          <el-input
            v-model="queryParams.data.roleName"
            placeholder="请输入角色名称"
            clearable
            style="width: 220px"
            @input="handleSearch"
            @keyup.enter="handleImmediateSearch"
            @clear="handleReset"
          />
        </el-form-item>
        <el-form-item label="角色标识">
          <el-input
            v-model="queryParams.data.roleKey"
            placeholder="请输入角色标识"
            clearable
            style="width: 220px"
            @input="handleSearch"
            @keyup.enter="handleImmediateSearch"
            @clear="handleReset"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="loading">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作区域 -->
    <el-card class="operation-card" shadow="never">
      <div class="operation-container">
        <div class="operation-left">
          <el-button type="primary" @click="handleAdd" class="action-btn">
            <el-icon><Plus /></el-icon>
            新增角色
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
          <el-tag type="info">共 {{ total }} 个角色</el-tag>
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
        v-loading="loading"
        :data="tableData"
        @selection-change="handleSelectionChange"
        stripe
        style="width: 100%"
        class="role-table"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="角色ID" width="100" />
        <el-table-column prop="roleName" label="角色名称" width="150" />
        <el-table-column prop="roleKey" label="角色标识" width="150" />
        <el-table-column prop="userCount" label="用户数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.userCount > 0" type="info" effect="light">
              {{ row.userCount }}人
            </el-tag>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
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
        <el-table-column prop="updateTime" label="更新时间" width="180">
          <template #default="{ row }">
            <div class="time-cell">
              <span v-if="row.updateTime" class="time-text">
                {{ formatDateTime(row.updateTime) }}
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
              <el-tooltip content="删除" placement="top">
                <el-icon class="action-icon delete-icon" @click="handleDelete(row.id)">
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

    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      direction="rtl"
      size="800px"
      class="role-drawer wide-drawer"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色名称" prop="roleName">
              <el-input
                v-model="formData.roleName"
                placeholder="请输入角色名称"
                maxlength="50"
                show-word-limit
                class="custom-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色标识" prop="roleKey">
              <el-input
                v-model="formData.roleKey"
                placeholder="请输入角色标识"
                maxlength="50"
                show-word-limit
                class="custom-input"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 菜单权限选择区域 - 修复 undefined 问题 -->
        <el-form-item label="菜单权限" class="menu-permission-item">
          <div class="menu-select-area">
            <div class="menu-header">
              <div class="menu-title"></div>
              <div class="menu-actions">
                <el-button size="small" @click="handleExpandAll" text class="action-btn">
                  <el-icon><Expand /></el-icon>
                  展开
                </el-button>
                <el-button size="small" @click="handleCollapseAll" text class="action-btn">
                  <el-icon><Fold /></el-icon>
                  折叠
                </el-button>
                <el-button size="small" @click="handleSelectAll" text class="action-btn">
                  <el-icon><Select /></el-icon>
                  全选
                </el-button>
                <el-button size="small" @click="handleClearAll" text class="action-btn">
                  <el-icon><Close /></el-icon>
                  清空
                </el-button>
              </div>
            </div>

            <div class="menu-search">
              <el-input
                v-model="menuFilterText"
                placeholder="输入关键字过滤菜单..."
                clearable
                prefix-icon="Search"
                size="small"
                class="search-input"
              />
            </div>

            <div class="menu-tree-container">
              <div class="tree-stats">
                <span class="tree-info">共 {{ getTotalMenuCount() }} 个菜单</span>
                <!-- 修复：使用安全访问 -->
                <span class="tree-selected" v-if="getMenuIdList().length > 0">
                  已选 {{ getMenuIdList().length }} 个
                </span>
              </div>

              <div class="tree-wrapper">
                <el-tree
                  ref="menuTreeRef"
                  :data="menuTreeData"
                  show-checkbox
                  node-key="id"
                  :props="treeProps"
                  :default-checked-keys="getMenuIdList()"
                  :filter-node-method="filterNode"
                  :expand-on-click-node="false"
                  :check-strictly="false"
                  :height="400"
                  :default-expand-all="false"
                  @check="handleMenuCheck"
                  class="beautified-tree"
                >
                  <template #default="{ node, data }">
                    <div class="tree-node">
                      <el-icon class="node-icon">
                        <component
                          :is="data.children && data.children.length > 0 ? 'Folder' : 'Document'"
                        />
                      </el-icon>
                      <span class="node-label" :title="node.label">{{ node.label }}</span>
                      <div class="node-actions">
                        <el-tag
                          v-if="data.children && data.children.length > 0"
                          size="small"
                          effect="plain"
                          class="children-count"
                        >
                          {{ data.children.length }}
                        </el-tag>
                        <el-tag
                          v-if="isMenuSelected(data)"
                          size="small"
                          type="success"
                          class="selected-badge"
                        >
                          已选
                        </el-tag>
                      </div>
                    </div>
                  </template>
                </el-tree>
              </div>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="formData.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
            maxlength="500"
            show-word-limit
            resize="none"
            class="custom-textarea"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <div class="footer-left">
            <!-- 修复：使用安全访问 -->
            <el-tag v-if="getMenuIdList().length > 0" type="info" size="large">
              已选择 {{ getMenuIdList().length }} 个菜单权限
            </el-tag>
            <span v-else class="no-selection">未选择任何菜单权限</span>
          </div>
          <div class="footer-right">
            <el-button @click="drawerVisible = false" class="cancel-btn">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="loading" class="save-btn">
              <el-icon><Check /></el-icon>
              保存
            </el-button>
          </div>
        </div>
      </template>
    </el-drawer>
    <el-drawer
      v-model="detailDrawerVisible"
      title="角色详情"
      direction="rtl"
      size="1000px"
      class="detail-drawer"
    >
      <el-descriptions :column="2" border v-if="currentRoleDetail">
        <el-descriptions-item label="角色ID">
          {{ currentRoleDetail.id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="角色名称">
          {{ currentRoleDetail.roleName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="角色标识">
          {{ currentRoleDetail.roleKey || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="菜单权限" :span="2">
          <div
            v-if="currentRoleDetail.menuIdList && currentRoleDetail.menuIdList.length > 0"
            class="menu-list"
          >
            <el-tag
              v-for="menuId in currentRoleDetail.menuIdList"
              :key="menuId"
              type="info"
              size="small"
              class="menu-tag"
            >
              {{ getMenuNameById(menuId) }}
            </el-tag>
          </div>
          <span v-else class="no-data">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ currentRoleDetail.remark || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ currentRoleDetail.createTime ? formatDateTime(currentRoleDetail.createTime) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间" :span="2">
          {{ currentRoleDetail.updateTime ? formatDateTime(currentRoleDetail.updateTime) : '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="detailDrawerVisible = false">关闭</el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 分配用户抽屉 -->
    <el-drawer
      v-model="assignUserDrawerVisible"
      title="分配用户"
      direction="rtl"
      size="800px"
      class="assign-user-drawer"
    >
      <div class="user-assign-container">
        <div class="user-select-area">
          <el-transfer
            v-model="assignedUserIds"
            :data="userOptions"
            :titles="['未分配用户', '已分配用户']"
            :props="{ key: 'id', label: 'userName' }"
            filterable
          />
        </div>
      </div>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="assignUserDrawerVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveUser" :loading="loading">保存</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Expand, Fold, Select, Close, Check } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/time'
import roleApi from '@/api/services/system/role'
import menuApi from '@/api/services/system/menu'

// 响应式数据
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const drawerVisible = ref(false)
const drawerTitle = ref('')
const selectedRows = ref([])
const detailDrawerVisible = ref(false)
const currentRoleDetail = ref(null)
const assignUserDrawerVisible = ref(false)
const currentRoleIdForUser = ref(null) // 专门用于用户分配的角色ID

// 表单引用
const formRef = ref()
const menuTreeRef = ref()

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  data: {
    roleName: '',
    roleKey: '',
  },
})

// 表单数据
const formData = reactive({
  id: '',
  roleName: '',
  roleKey: '',
  remark: '',
  menuIdList: [],
})

// 菜单树相关数据
const menuTreeData = ref([])
const menuFilterText = ref('')
const treeProps = {
  children: 'children',
  label: 'menuName',
}

// 用户分配相关数据
const userOptions = ref([])
const assignedUserIds = ref([])

// 表单验证规则
const rules = {
  roleName: [
    { required: true, message: '角色名称不能为空', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  roleKey: [
    { required: true, message: '角色标识不能为空', trigger: 'blur' },
    { min: 2, max: 50, message: '角色标识长度在 2 到 50 个字符', trigger: 'blur' },
  ],
}
const getTotalMenuCount = () => {
  let count = 0
  const countMenus = (menus) => {
    menus.forEach((menu) => {
      count++
      if (menu.children && menu.children.length > 0) {
        countMenus(menu.children)
      }
    })
  }
  if (menuTreeData.value && menuTreeData.value.length > 0) {
    countMenus(menuTreeData.value)
  }
  return count
}
// 检查菜单是否被选中
const isMenuSelected = (menuData) => {
  return getMenuIdList().includes(menuData.id)
}
// 菜单过滤方法
const filterNode = (value, data) => {
  if (!value) return true
  return data.menuName.includes(value)
}

// 菜单选择处理
const handleMenuCheck = (checkedNodes, checkedKeys) => {
  formData.menuIdList = checkedKeys.checkedKeys || []
}
const getMenuIdList = () => {
  return formData.menuIdList || []
}
// 监听菜单过滤
watch(menuFilterText, (val) => {
  if (menuTreeRef.value) {
    menuTreeRef.value.filter(val)
  }
})
// 添加树形操作的方法
const handleExpandAll = () => {
  if (menuTreeRef.value) {
    const nodes = menuTreeRef.value.store.nodesMap
    Object.keys(nodes).forEach((key) => {
      nodes[key].expanded = true
    })
  }
}

const handleCollapseAll = () => {
  if (menuTreeRef.value) {
    const nodes = menuTreeRef.value.store.nodesMap
    Object.keys(nodes).forEach((key) => {
      nodes[key].expanded = false
    })
  }
}

const handleSelectAll = () => {
  if (menuTreeRef.value && menuTreeData.value.length > 0) {
    const allKeys = getAllMenuKeys(menuTreeData.value)
    menuTreeRef.value.setCheckedKeys(allKeys)
    formData.menuIdList = allKeys
  }
}

const handleClearAll = () => {
  if (menuTreeRef.value) {
    menuTreeRef.value.setCheckedKeys([])
    formData.menuIdList = []
  }
}

// 获取所有菜单键的方法
const getAllMenuKeys = (treeData) => {
  const keys = []
  const traverse = (nodes) => {
    nodes.forEach((node) => {
      keys.push(node.id)
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    })
  }
  traverse(treeData)
  return keys
}
const getMenuNameById = (menuId) => {
  // 这里应该从菜单树数据中查找菜单名称
  // 简化处理，直接返回ID
  return `菜单 ${menuId}`
}

const getPageList = async () => {
  loading.value = true
  try {
    const response = await roleApi.getPageList(queryParams)
    console.log('角色列表接口返回数据结构:', response)

    tableData.value = response.data || []
    total.value = response.count || 0

    // 检查第一个角色是否包含菜单信息
    if (tableData.value.length > 0) {
      const firstRole = tableData.value[0]
      console.log('第一个角色的数据结构:', firstRole)

      // 检查可能的菜单字段名
      if (firstRole.menuIdList !== undefined) {
        console.log('角色数据包含 menuIdList 字段')
      } else if (firstRole.menuIds !== undefined) {
        console.log('角色数据包含 menuIds 字段')
        // 如果是字符串格式，转换为数组
        tableData.value.forEach((role) => {
          if (role.menuIds && typeof role.menuIds === 'string') {
            role.menuIdList = role.menuIds.split(',').map((id) => parseInt(id))
          }
        })
      } else {
        console.log('角色数据不包含菜单字段，需要初始化')
        tableData.value.forEach((role) => {
          role.menuIdList = [] // 初始化空数组
        })
      }
    }
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const getMenuTreeData = async () => {
  try {
    console.log('开始获取菜单树数据')

    // 直接使用分页接口获取菜单数据
    const response = await menuApi.getPageList({ page: 1, limit: 1000 })
    console.log('菜单接口返回数据:', response)

    let flatMenus = []

    // 处理不同的返回数据结构
    if (Array.isArray(response)) {
      flatMenus = response
    } else if (response.data && Array.isArray(response.data)) {
      flatMenus = response.data
    } else if (response.code === 200 && response.data) {
      flatMenus = response.data
    } else {
      console.warn('菜单接口返回数据格式异常，使用模拟数据')
      flatMenus = getMockMenuData()
    }

    // 构建树形结构
    menuTreeData.value = buildMenuTree(flatMenus)
    console.log('构建的菜单树数据:', menuTreeData.value)
  } catch (error) {
    console.error('获取菜单树失败:', error)
    // 出错时使用模拟数据
    menuTreeData.value = getMockMenuTreeData()
    ElMessage.warning('获取菜单数据失败，使用模拟数据')
  }
}

const buildMenuTree = (flatMenus) => {
  if (!flatMenus || flatMenus.length === 0) {
    return getMockMenuTreeData()
  }

  const menuMap = {}
  const tree = []

  // 创建映射
  flatMenus.forEach((menu) => {
    menuMap[menu.id] = { ...menu, children: [] }
  })

  // 构建树形结构
  flatMenus.forEach((menu) => {
    if (menu.parentId && menuMap[menu.parentId]) {
      menuMap[menu.parentId].children.push(menuMap[menu.id])
    } else {
      tree.push(menuMap[menu.id])
    }
  })

  return tree.length > 0 ? tree : getMockMenuTreeData()
}

const getMockMenuData = () => {
  return [
    { id: 1, menuName: '系统管理', parentId: null },
    { id: 2, menuName: '用户管理', parentId: 1 },
    { id: 3, menuName: '角色管理', parentId: 1 },
    { id: 4, menuName: '菜单管理', parentId: 1 },
    { id: 5, menuName: '部门管理', parentId: 1 },
    { id: 6, menuName: '系统监控', parentId: null },
    { id: 7, menuName: '操作日志', parentId: 6 },
    { id: 8, menuName: '登录日志', parentId: 6 },
    { id: 9, menuName: '业务管理', parentId: null },
    { id: 10, menuName: '订单管理', parentId: 9 },
    { id: 11, menuName: '商品管理', parentId: 9 },
  ]
}
const getMockMenuTreeData = () => {
  return [
    {
      id: 1,
      menuName: '系统管理',
      children: [
        { id: 2, menuName: '用户管理' },
        { id: 3, menuName: '角色管理' },
        { id: 4, menuName: '菜单管理' },
        { id: 5, menuName: '部门管理' },
      ],
    },
    {
      id: 6,
      menuName: '系统监控',
      children: [
        { id: 7, menuName: '操作日志' },
        { id: 8, menuName: '登录日志' },
      ],
    },
    {
      id: 9,
      menuName: '业务管理',
      children: [
        { id: 10, menuName: '订单管理' },
        { id: 11, menuName: '商品管理' },
      ],
    },
  ]
}

// 搜索防抖
let searchTimer = null

// 搜索处理（防抖版本）
const handleSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    queryParams.page = 1
    getPageList()
  }, 500)
}

// 立即搜索（用于手动搜索按钮）
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
      roleName: '',
      roleKey: '',
    },
  })
  getPageList()
}

// 刷新
const handleRefresh = () => {
  getPageList()
  ElMessage.success('数据已刷新')
}

// 新增角色 - 确保 menuIdList 有默认值
const handleAdd = () => {
  drawerTitle.value = '新增角色'
  Object.assign(formData, {
    id: '',
    roleName: '',
    roleKey: '',
    remark: '',
    menuIdList: [], // 确保有默认值
  })

  // 获取菜单树数据
  getMenuTreeData()
    .then(() => {
      drawerVisible.value = true
    })
    .catch((error) => {
      console.error('获取菜单数据失败:', error)
      drawerVisible.value = true
    })
}

const handleEdit = async (row) => {
  drawerTitle.value = '编辑角色'
  loading.value = true

  try {
    console.log('开始编辑角色，角色ID:', row.id)

    // 修复：确保 menuIdList 有默认值
    const selectedMenuIds = row.menuIdList || []
    console.log('角色已选中的菜单ID:', selectedMenuIds)

    // 设置表单数据 - 确保 menuIdList 有默认值
    Object.assign(formData, {
      id: row.id,
      roleName: row.roleName,
      roleKey: row.roleKey,
      remark: row.remark || '',
      menuIdList: selectedMenuIds, // 确保有默认值
    })

    console.log('设置的表单数据:', formData)

    // 获取菜单树数据
    await getMenuTreeData()

    // 打开抽屉
    drawerVisible.value = true
    console.log('编辑抽屉打开成功')
  } catch (error) {
    console.error('编辑角色失败:', error)
    // 出错时使用基础数据 - 确保 menuIdList 有默认值
    Object.assign(formData, {
      id: row.id,
      roleName: row.roleName,
      roleKey: row.roleKey,
      remark: row.remark || '',
      menuIdList: [], // 确保有默认值
    })
    drawerVisible.value = true
    ElMessage.warning('编辑角色数据异常，使用基础数据')
  } finally {
    loading.value = false
  }
}

// 查看详情
const handleViewDetail = (row) => {
  currentRoleDetail.value = { ...row }
  detailDrawerVisible.value = true
}

// 保存角色
const handleSave = async () => {
  try {
    if (!formRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }

    // 表单验证
    await formRef.value.validate()
    loading.value = true

    // 准备提交数据 - 使用安全的 menuIdList
    const submitData = {
      id: formData.id,
      roleName: formData.roleName,
      roleKey: formData.roleKey,
      remark: formData.remark,
      menuIdList: getMenuIdList(), // 使用安全访问
    }

    console.log('提交的角色数据:', submitData)

    let response
    if (formData.id) {
      response = await roleApi.editRole(submitData)
    } else {
      response = await roleApi.addRole(submitData)
    }

    if (response.code === 200) {
      ElMessage.success(formData.id ? '修改成功' : '新增成功')
      drawerVisible.value = false
      // 刷新列表
      // getPageList()
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('保存角色失败:', error)
    if (error.errors) {
      ElMessage.error('请检查表单填写是否正确')
    } else {
      ElMessage.error('保存失败:' + (error.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}

// 删除角色
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该角色吗?', '提示', {
      type: 'warning',
    })

    const response = await roleApi.removeRole(id)
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
    ElMessage.warning('请选择要删除的角色')
    return
  }

  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedRows.value.length} 个角色吗?`, '提示', {
      type: 'warning',
    })

    const ids = selectedRows.value.map((item) => item.id)
    const response = await roleApi.batchRemoveRoles(ids)
    if (response.code === 200) {
      ElMessage.success(`成功删除 ${selectedRows.value.length} 个角色`)
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

// 保存用户分配
const handleSaveUser = async () => {
  try {
    loading.value = true
    const response = await roleApi.assignUser({
      roleId: currentRoleIdForUser.value,
      userIds: assignedUserIds.value,
    })

    if (response.code === 200) {
      ElMessage.success('用户分配成功')
      assignUserDrawerVisible.value = false
      getPageList()
    } else {
      ElMessage.error(response.message || '分配用户失败')
    }
  } catch (error) {
    console.error('分配用户失败:', error)
    ElMessage.error('分配用户失败')
  } finally {
    loading.value = false
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
defineExpose({
  handleEdit,
  handleAdd,
})
// 初始化
onMounted(() => {
  getPageList()
})
</script>

<style scoped lang="scss">
.role-management-container {
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
.role-drawer {
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
// 美化表单输入框
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
// 美化菜单选择区域
.menu-select-area {
  width: 750px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: white;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #f1f5f9;

  .menu-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #374151;

    .menu-icon {
      color: #3b82f6;
      font-size: 18px;
    }
  }

  .menu-stats {
    .el-tag {
      border-radius: 12px;
      font-weight: 500;
    }
  }
}

.menu-search {
  padding: 16px 20px 0;

  .search-input {
    :deep(.el-input__wrapper) {
      border-radius: 20px;
      border: 1px solid #e2e8f0;
      transition: all 0.3s ease;

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
}

.menu-tree-container {
  height: 320px;
  padding: 16px 20px;
  overflow-y: auto;
}

// 美化树形控件
.beautified-menu-tree {
  :deep(.el-tree) {
    background: transparent;

    .el-tree-node {
      margin: 2px 0;

      .el-tree-node__content {
        height: 40px;
        border-radius: 8px;
        transition: all 0.3s ease;
        margin: 2px 0;

        &:hover {
          background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
          transform: translateX(4px);

          .tree-node {
            .node-icon {
              color: #3b82f6;
            }
            .node-label {
              color: #1e40af;
              font-weight: 500;
            }
          }
        }

        .el-checkbox {
          margin-right: 8px;

          :deep(.el-checkbox__inner) {
            border-radius: 4px;
            border: 2px solid #d1d5db;

            &:hover {
              border-color: #3b82f6;
            }
          }
        }

        .tree-node {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 4px 0;
          width: 100%;

          .node-icon {
            color: #6b7280;
            font-size: 16px;
            transition: color 0.3s ease;
          }

          .node-label {
            flex: 1;
            color: #374151;
            font-size: 14px;
            transition: all 0.3s ease;
          }

          .el-tag {
            height: 20px;
            line-height: 18px;
            border-radius: 10px;
            background: rgba(59, 130, 246, 0.1);
            border-color: rgba(59, 130, 246, 0.2);
            color: #1d4ed8;
            font-size: 11px;
          }
        }
      }

      &.is-current {
        > .el-tree-node__content {
          background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
          border-left: 3px solid #3b82f6;

          .tree-node {
            .node-icon {
              color: #3b82f6;
            }
            .node-label {
              color: #1e40af;
              font-weight: 600;
            }
          }
        }
      }

      .el-tree-node__children {
        padding-left: 24px;
        border-left: 1px dashed #e5e7eb;
        margin-left: 12px;
      }
    }
  }
}
.role-drawer.wide-drawer {
  .el-drawer__body {
    padding: 20px 30px;
    overflow-y: auto;
  }

  .el-drawer__header {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--el-border-color-light);
  }

  .custom-input,
  .custom-textarea {
    width: 100%;
  }

  .menu-permission-item {
    margin-top: 20px;

    .menu-select-area {
      border: 1px solid var(--el-border-color-light);
      border-radius: 8px;
      padding: 20px;
      background-color: var(--el-fill-color-light);
    }

    .menu-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;

      .menu-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 16px;
        font-weight: 500;

        .menu-icon {
          color: var(--el-color-primary);
        }
      }

      .menu-actions {
        display: flex;
        gap: 8px;

        .action-btn {
          padding: 6px 12px;
          background-color: var(--el-color-primary-light-9);

          &:hover {
            background-color: var(--el-color-primary-light-8);
          }
        }
      }
    }

    .menu-search {
      margin-bottom: 20px;

      .search-input {
        width: 100%;
      }
    }

    .menu-tree-container {
      border: 1px solid var(--el-border-color);
      border-radius: 6px;
      overflow: hidden;
      background-color: white;

      .tree-stats {
        padding: 10px 15px;
        background-color: var(--el-fill-color-lighter);
        border-bottom: 1px solid var(--el-border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 13px;

        .tree-info {
          color: var(--el-text-color-regular);
        }

        .tree-selected {
          color: var(--el-color-success);
          font-weight: 500;
        }
      }

      .tree-wrapper {
        max-height: 400px;
        overflow-y: auto;
        padding: 10px;

        .beautified-tree {
          .tree-node {
            display: flex;
            align-items: center;
            padding: 6px 0;
            width: 100%;

            .node-icon {
              margin-right: 8px;
              color: var(--el-text-color-secondary);
            }

            .node-label {
              flex: 1;
              font-size: 14px;
              color: var(--el-text-color-primary);
            }

            .node-actions {
              display: flex;
              align-items: center;
              gap: 8px;
              margin-left: 10px;

              .children-count {
                font-size: 12px;
                padding: 2px 6px;
                background-color: var(--el-color-primary-light-9);
                border-color: var(--el-color-primary-light-5);
                color: var(--el-color-primary);
              }

              .selected-badge {
                font-size: 12px;
                padding: 2px 6px;
              }
            }
          }
        }
      }
    }

    .menu-footer {
      margin-top: 20px;

      .quick-actions {
        display: flex;
        gap: 10px;

        .quick-btn {
          padding: 6px 12px;
          background-color: var(--el-color-info-light-9);

          &:hover {
            background-color: var(--el-color-info-light-8);
          }
        }
      }
    }
  }

  .drawer-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 20px;
    border-top: 1px solid var(--el-border-color-light);

    .footer-left {
      .no-selection {
        color: var(--el-text-color-secondary);
        font-size: 14px;
      }
    }

    .footer-right {
      display: flex;
      gap: 10px;

      .cancel-btn {
        &:hover {
          border-color: var(--el-color-primary);
          color: var(--el-color-primary);
        }
      }

      .save-btn {
        padding: 0 24px;
      }
    }
  }
}

.menu-actions {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid #f1f5f9;
  background: #f8fafc;

  .el-button {
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    color: #6b7280;

    &:hover {
      color: #3b82f6;
      background: white;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }

    .el-icon {
      margin-right: 4px;
    }
  }
}

// 美化抽屉底部
.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 0 0;

  .cancel-btn {
    border-radius: 8px;
    padding: 10px 24px;
    border: 1px solid #d1d5db;
    color: #6b7280;

    &:hover {
      border-color: #9ca3af;
      color: #374151;
      transform: translateY(-1px);
    }
  }

  .save-btn {
    border-radius: 8px;
    padding: 10px 24px;
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    border: none;
    font-weight: 500;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    &:active {
      transform: translateY(0);
    }
  }
}

// 美化滚动条
.menu-tree-container::-webkit-scrollbar {
  width: 6px;
}

.menu-tree-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.menu-tree-container::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;

  &:hover {
    background: #94a3b8;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .role-drawer {
    :deep(.el-drawer) {
      width: 90% !important;

      .el-drawer__body {
        padding: 16px;
      }
    }
  }

  .menu-header {
    padding: 12px 16px;
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }

  .menu-search {
    padding: 12px 16px 0;
  }

  .menu-tree-container {
    padding: 12px 16px;
    height: 280px;
  }

  .menu-actions {
    padding: 8px 16px;
    flex-wrap: wrap;
  }
}

// 动画效果
.tree-node {
  transition: all 0.3s ease;
}

.beautified-menu-tree {
  :deep(.el-tree-node__expand-icon) {
    transition: transform 0.3s ease;
  }

  :deep(.el-tree-node__expand-icon.expanded) {
    transform: rotate(90deg);
  }
}

// 加载状态
:deep(.el-tree__empty-block) {
  padding: 40px 0;

  .el-tree__empty-text {
    color: #9ca3af;
    font-style: italic;
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

.role-table {
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
.role-drawer,
.detail-drawer,
.assign-menu-drawer,
.assign-user-drawer {
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

.menu-tree-container {
  height: 100%;
  display: flex;
  flex-direction: column;

  .tree-search {
    margin-bottom: 16px;
  }

  .menu-tree {
    flex: 1;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 12px;
  }
}

.user-assign-container {
  height: 100%;

  .user-select-area {
    height: 100%;

    :deep(.el-transfer) {
      height: 100%;
      display: flex;
      flex-direction: column;

      .el-transfer-panel {
        flex: 1;

        .el-transfer-panel__body {
          height: 400px;
        }
      }
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

// 响应式设计
@media (max-width: 1200px) {
  .role-management-container {
    padding: 16px;
  }

  .operation-container {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .role-drawer,
  .detail-drawer,
  .assign-menu-drawer,
  .assign-user-drawer {
    :deep(.el-drawer) {
      width: 90% !important;
    }
  }
}

@media (max-width: 768px) {
  .role-management-container {
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

  .role-drawer,
  .detail-drawer,
  .assign-menu-drawer,
  .assign-user-drawer {
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

  .user-assign-container {
    .user-select-area {
      :deep(.el-transfer) {
        flex-direction: column;

        .el-transfer-panel {
          width: 100% !important;
          margin-bottom: 16px;
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .role-management-container {
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
:deep(.el-drawer__body)::-webkit-scrollbar,
:deep(.el-tree)::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-track,
:deep(.el-drawer__body)::-webkit-scrollbar-track,
:deep(.el-tree)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb,
:deep(.el-drawer__body)::-webkit-scrollbar-thumb,
:deep(.el-tree)::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover,
:deep(.el-drawer__body)::-webkit-scrollbar-thumb:hover,
:deep(.el-tree)::-webkit-scrollbar-thumb:hover {
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

// 树形控件样式优化
:deep(.el-tree) {
  .el-tree-node {
    margin: 4px 0;

    .el-tree-node__content {
      height: 36px;
      border-radius: 4px;

      &:hover {
        background-color: #f3f4f6;
      }
    }

    &.is-current > .el-tree-node__content {
      background-color: #eff6ff;
      color: #3b82f6;
    }
  }
}

// 穿梭框样式优化
:deep(.el-transfer) {
  .el-transfer-panel {
    border: 1px solid #e5e7eb;
    border-radius: 6px;

    .el-transfer-panel__header {
      background-color: #f8fafc;
      border-bottom: 1px solid #e5e7eb;
    }

    .el-checkbox__input.is-checked + .el-checkbox__label {
      color: #3b82f6;
    }
  }
}

// 抽屉内容区域优化
:deep(.el-drawer__body) {
  .el-row {
    margin: 0 -10px;

    .el-col {
      padding: 0 10px;
    }
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

// 树形搜索框样式
.tree-search {
  :deep(.el-input) {
    .el-input__wrapper {
      border-radius: 20px;
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
</style>
