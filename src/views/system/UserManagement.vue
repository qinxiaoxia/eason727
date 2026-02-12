<template>
  <div class="user-management-container">
    <!-- 搜索区域 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="queryParams" inline>
        <el-form-item label="用户昵称">
          <el-input
            v-model="queryParams.data.nickName"
            placeholder="请输入用户昵称"
            clearable
            style="width: 220px"
            @input="handleSearchDebounce"
            @keyup.enter="handleImmediateSearch"
            @clear="handleReset"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleImmediateSearch" :loading="loading">
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
            新增用户
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
          <el-tag type="info">共{{ total }}个用户</el-tag>
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
        class="user-table"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="用户 ID" width="120" />
        <el-table-column prop="userName" label="用户名" width="120" />
        <el-table-column prop="nickName" label="用户昵称" width="120" />
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-tag :type="row.enabled === '1' ? 'success' : 'danger'" effect="light">
              {{ row.enabled === '1' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="260">
          <template #default="{ row }">
            <div v-if="row.roleNames" class="role-tags">
              <el-tag size="small" type="info">
                {{ row.roleNames }}
              </el-tag>
            </div>
            <span v-else class="no-data">-</span>
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
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
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
              <el-tooltip content="重置密码" placement="top">
                <el-icon class="action-icon" @click="handleResetPassword(row)">
                  <Refresh />
                </el-icon>
              </el-tooltip>
              <el-tooltip :content="row.enabled === '1' ? '禁用用户' : '启用用户'" placement="top">
                <el-icon
                  class="action-icon"
                  :class="row.enabled === '1' ? 'disable-icon' : 'enable-icon'"
                  @click="handleToggleStatus(row)"
                >
                  <component :is="row.enabled === '1' ? 'Close' : 'Check'" />
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

    <!-- 新增/编辑抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      direction="rtl"
      size="600px"
      class="user-drawer"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="userName">
              <el-input
                v-model="formData.userName"
                placeholder="请输入用户名"
                :disabled="!!formData.id"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="用户昵称" prop="nickName">
              <el-input
                v-model="formData.nickName"
                placeholder="请输入用户昵称"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="状态" prop="enabled">
          <el-radio-group v-model="formData.enabled">
            <el-radio :value="'1'">启用</el-radio>
            <el-radio :value="'0'">禁用</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 角色分配 -->
        <el-form-item label="角色分配" prop="roleIdList">
          <el-select
            v-model="formData.roleIdList"
            multiple
            placeholder="请选择角色"
            style="width: 100%"
            clearable
            filterable
            :loading="roleLoading"
            value-key="id"
          >
            <el-option
              v-for="role in roleOptions"
              :key="role.id"
              :label="role.roleName"
              :value="{ id: role.id }"
            />
          </el-select>
          <div class="role-select-tips">
            <span class="tip-text">可多选，最多可选择 10 个角色</span>
            <span class="selected-count"
              >已选 {{ formData.roleIdList ? formData.roleIdList.length : 0 }} 个角色</span
            >
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

    <!-- 重置密码抽屉 -->
    <el-drawer
      v-model="resetPasswordDrawerVisible"
      title="重置密码"
      direction="rtl"
      size="500px"
      class="reset-password-drawer"
    >
      <el-form
        ref="resetPasswordFormRef"
        :model="resetPasswordForm"
        :rules="resetPasswordRules"
        label-width="100px"
      >
        <el-form-item label="用户名">
          <el-input v-model="resetPasswordForm.userName" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="password">
          <el-input
            v-model="resetPasswordForm.password"
            type="password"
            placeholder="请输入新密码"
            show-password
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="resetPasswordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="resetPasswordDrawerVisible = false">取消</el-button>
          <el-button type="primary" @click="handleConfirmResetPassword" :loading="loading">
            确认重置
          </el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 用户详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="用户详情"
      direction="rtl"
      size="700px"
      class="detail-drawer"
    >
      <el-descriptions :column="2" border v-if="currentUserDetail">
        <el-descriptions-item label="用户ID">
          {{ currentUserDetail.id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="用户名">
          {{ currentUserDetail.userName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="用户昵称">
          {{ currentUserDetail.nickName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentUserDetail.enabled === '1' ? 'success' : 'danger'" effect="light">
            {{ currentUserDetail.enabled === '1' ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="角色" :span="2">
          <div
            v-if="currentUserDetail.roleNames && currentUserDetail.roleNames.length > 0"
            class="role-tags"
          >
            <el-tag
              v-for="roleName in currentUserDetail.roleNames"
              :key="roleName"
              type="info"
              class="role-tag"
            >
              {{ roleName }}
            </el-tag>
          </div>
          <span v-else class="no-data">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ currentUserDetail.createTime ? formatDateTime(currentUserDetail.createTime) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间" :span="2">
          {{ currentUserDetail.updateTime ? formatDateTime(currentUserDetail.updateTime) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="最后修改密码时间" :span="2">
          {{
            currentUserDetail.modifyPassTime
              ? formatDateTime(currentUserDetail.modifyPassTime)
              : '-'
          }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ currentUserDetail.remark || '-' }}
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
import { Search, Refresh, Plus, Delete, View, Edit } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/time'
import userApi from '@/api/services/system/user'
import roleApi from '@/api/services/system/role'

// 响应式数据
const loading = ref(false)
const roleLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const drawerVisible = ref(false)
const drawerTitle = ref('')
const selectedRows = ref([])
const detailDrawerVisible = ref(false)
const resetPasswordDrawerVisible = ref(false)
const currentUserDetail = ref(null)
const roleOptions = ref([])

// 表单引用
const formRef = ref()
const resetPasswordFormRef = ref()

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  data: {
    nickName: '',
    userName: '',
    enabled: '',
    deptIds: [],
  },
})

// 表单数据 - 正确使用 roleIdList 字段
const formData = reactive({
  id: '',
  userName: '',
  nickName: '',
  password: '',
  enabled: '1',
  roleIdList: [], // 角色ID数组
  remark: '',
})

// 重置密码表单
const resetPasswordForm = reactive({
  id: '',
  userName: '',
  password: '',
  confirmPassword: '',
})

// 表单验证规则
const rules = {
  userName: [
    { required: true, message: '用户名不能为空', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  nickName: [
    { required: true, message: '用户昵称不能为空', trigger: 'blur' },
    { min: 2, max: 50, message: '用户昵称长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  enabled: [{ required: true, message: '请选择状态', trigger: 'change' }],
  roleIdList: [
    {
      validator: (rule, value, callback) => {
        if (!value || value.length === 0) {
          callback(new Error('请至少选择一个角色'))
        } else if (value.length > 10) {
          callback(new Error('最多只能选择 10 个角色'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

// 重置密码验证规则
const resetPasswordRules = {
  password: [
    { required: true, message: '新密码不能为空', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== resetPasswordForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 获取用户列表
const getPageList = async () => {
  loading.value = true
  try {
    const response = await userApi.getPageList(queryParams)
    tableData.value = response.data || []
    total.value = response.count || 0
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 获取角色列表
const getRoleList = async () => {
  roleLoading.value = true
  try {
    const params = {
      page: 1,
      limit: 1000,
      data: {},
    }

    const response = await roleApi.getPageList(params)

    if (response.code === 200) {
      roleOptions.value = response.data || []
      console.log('获取到的角色列表:', roleOptions.value)
    } else {
      console.error('角色接口返回错误:', response)
      ElMessage.error(response.message || '获取角色列表失败')
      roleOptions.value = getDefaultRoles()
    }
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.warning('获取角色列表失败，使用默认角色')
    roleOptions.value = getDefaultRoles()
  } finally {
    roleLoading.value = false
  }
}

// 默认角色列表（降级方案）
const getDefaultRoles = () => {
  return [
    { id: 1, roleName: '管理员', roleKey: 'admin' },
    { id: 2, roleName: '普通用户', roleKey: 'user' },
    { id: 3, roleName: '审核员', roleKey: 'audit' },
    { id: 4, roleName: '操作员', roleKey: 'operator' },
    { id: 5, roleName: '查看员', roleKey: 'viewer' },
  ]
}

// 搜索防抖
let searchTimer = null

// 搜索处理（防抖版本）
const handleSearchDebounce = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    queryParams.page = 1
    getPageList()
  }, 500)
}

const handleImmediateSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer) // 清除防抖定时器
  }
  queryParams.page = 1
  getPageList()
}
// 重置搜索
const handleReset = () => {
  Object.assign(queryParams, {
    page: 1,
    limit: 20,
    data: {
      nickName: '',
      userName: '',
      enabled: '',
      deptIds: [],
    },
  })
  getPageList()
}

// 刷新
const handleRefresh = () => {
  getPageList()
  ElMessage.success('数据已刷新')
}

// 新增用户
const handleAdd = () => {
  drawerTitle.value = '新增用户'
  Object.assign(formData, {
    id: '',
    userName: '',
    nickName: '',
    password: '',
    enabled: '1',
    roleIdList: [], // 清空角色列表
    remark: '',
  })
  drawerVisible.value = true
  if (roleOptions.value.length === 0) {
    getRoleList()
  }
}

// 编辑用户 - 正确调用编辑接口
const handleEdit = async (row) => {
  drawerTitle.value = '编辑用户'
  try {
    // 直接从行数据获取基本信息
    Object.assign(formData, {
      id: row.id,
      userName: row.userName,
      nickName: row.nickName,
      enabled: row.enabled || '1',
      roleIdList: (row.roleIds || []).map((id) => ({ id })), // 转换为 [{id: 1}, {id: 2}] 格式
      remark: row.remark || '',
    })

    // 如果需要更详细的角色信息，可以调用详情接口
    const response = await userApi.getUserInfo({ id: row.id })
    const userInfo = response.data || {}

    // 更新角色信息
    if (userInfo.roleIds) {
      formData.roleIdList = userInfo.roleIds.map((id) => ({ id }))
    }

    drawerVisible.value = true
    if (roleOptions.value.length === 0) {
      getRoleList()
    }
  } catch (error) {
    console.error('获取用户详情失败:', error)
    ElMessage.warning('获取详情失败，使用基础信息')
    drawerVisible.value = true
    if (roleOptions.value.length === 0) {
      getRoleList()
    }
  }
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    const response = await userApi.getUserInfo({ id: row.id })
    currentUserDetail.value = response.data || {}
    detailDrawerVisible.value = true
  } catch (error) {
    console.error('获取用户详情失败:', error)
    ElMessage.error('获取用户详情失败')
  }
}

// 保存用户
const handleSave = async () => {
  try {
    if (!formRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }

    await formRef.value.validate()
    loading.value = true

    // 准备提交数据 - 直接提交对象数组格式
    const submitData = {
      id: formData.id,
      userName: formData.userName,
      nickName: formData.nickName,
      password: formData.password,
      enabled: formData.enabled,
      roleIdList: formData.roleIdList, // 直接提交 [{id: 1}, {id: 2}] 格式
      remark: formData.remark,
    }

    console.log('提交的用户数据:', submitData)

    let response
    if (formData.id) {
      response = await userApi.editUserInfo(submitData)
    } else {
      response = await userApi.addUser(submitData)
    }

    if (response.code === 200) {
      ElMessage.success(formData.id ? '修改成功' : '新增成功')
      drawerVisible.value = false
      getPageList()
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('保存用户失败:', error)
    if (error.errors) {
      ElMessage.error('请检查表单填写是否正确')
    } else {
      ElMessage.error('保存失败:' + (error.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}

// 删除用户
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该用户吗?', '提示', {
      type: 'warning',
    })

    const response = await userApi.batchRemoveUsers([id])
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
    ElMessage.warning('请选择要删除的用户')
    return
  }

  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedRows.value.length} 个用户吗?`, '提示', {
      type: 'warning',
    })

    const ids = selectedRows.value.map((item) => item.id)
    const response = await userApi.batchRemoveUsers(ids)
    if (response.code === 200) {
      ElMessage.success(`成功删除 ${selectedRows.value.length} 个用户`)
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

// 重置密码
const handleResetPassword = (row) => {
  Object.assign(resetPasswordForm, {
    id: row.id,
    userName: row.userName,
    password: '',
    confirmPassword: '',
  })
  resetPasswordDrawerVisible.value = true
}

// 确认重置密码
const handleConfirmResetPassword = async () => {
  try {
    if (!resetPasswordFormRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }

    await resetPasswordFormRef.value.validate()
    loading.value = true

    const response = await userApi.resetPassword({
      id: resetPasswordForm.id,
      password: resetPasswordForm.password,
    })

    if (response.code === 200) {
      ElMessage.success('密码重置成功')
      resetPasswordDrawerVisible.value = false
      getPageList()
    } else {
      ElMessage.error(response.message || '密码重置失败')
    }
  } catch (error) {
    console.error('重置密码失败:', error)
    if (error.errors) {
      ElMessage.error('请检查表单填写是否正确')
    } else {
      ElMessage.error('重置密码失败')
    }
  } finally {
    loading.value = false
  }
}

// 切换用户状态
const handleToggleStatus = async (row) => {
  const newStatus = row.enabled === '1' ? '0' : '1'
  const statusText = newStatus === '1' ? '启用' : '禁用'

  try {
    await ElMessageBox.confirm(`确定${statusText}用户 "${row.userName}" 吗?`, '状态确认', {
      type: 'warning',
    })

    loading.value = true
    const response = await userApi.editUserInfo({
      ...row,
      enabled: newStatus,
    })

    if (response.code === 200) {
      ElMessage.success(`${statusText}成功`)
      getPageList()
    } else {
      ElMessage.error(response.message || `${statusText}失败`)
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
  getRoleList()
})
</script>

<style scoped lang="scss">
.user-management-container {
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

.user-table {
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

    &.disable-icon:hover {
      color: #ef4444;
      background-color: #fef2f2;
    }

    &.enable-icon:hover {
      color: #10b981;
      background-color: #f0fdf4;
    }
  }
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

.user-drawer,
.reset-password-drawer,
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
  }

  .el-drawer__footer {
    padding: 20px 24px;
    border-top: 1px solid #e5e7eb;
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

.role-select-tips {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;

  .tip-text {
    color: #9ca3af;
  }

  .selected-count {
    font-weight: 500;
    color: #3b82f6;
  }
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

// 响应式设计
@media (max-width: 1200px) {
  .user-management-container {
    padding: 16px;
  }

  .operation-container {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .user-drawer,
  .detail-drawer,
  .reset-password-drawer {
    :deep(.el-drawer) {
      width: 90% !important;
    }
  }
}

@media (max-width: 768px) {
  .user-management-container {
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

  .user-drawer,
  .detail-drawer,
  .reset-password-drawer {
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
  .user-management-container {
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

  &.disable-icon:hover::before {
    background: rgba(239, 68, 68, 0.1);
  }

  &.enable-icon:hover::before {
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

// 抽屉内容区域优化
:deep(.el-drawer__body) {
  .el-row {
    margin: 0 -10px;

    .el-col {
      padding: 0 10px;
    }
  }
}

.action-btn {
  border-radius: 6px;
  font-weight: 500;

  &:hover {
    transform: translateY(-1px);
    transition: all 0.2s ease;
  }
}
</style>
