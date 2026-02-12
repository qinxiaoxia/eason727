<template>
  <div class="personal-center">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">个人中心</h1>
      <p class="page-desc">管理您的个人信息和账户安全</p>
    </div>

    <div class="content-container">
      <!-- 左侧 - 个人信息卡片 -->
      <div class="left-panel">
        <el-card class="info-card" shadow="hover">
          <div class="user-avatar">
            <div class="avatar-circle">
              <el-icon><User /></el-icon>
            </div>
          </div>

          <div class="user-basic-info">
            <h3 class="user-name">{{ userInfo.nickName || userInfo.userName || '用户' }}</h3>
            <p class="user-id">ID: {{ userInfo.id || '-' }}</p>
            <el-tag
              :type="userInfo.enabled === '1' ? 'success' : 'danger'"
              size="small"
              class="status-tag"
            >
              {{ userInfo.enabled === '1' ? '启用' : '禁用' }}
            </el-tag>
          </div>

          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-label">角色</span>
              <span class="stat-value">
                <span v-if="userInfo.roleNames && userInfo.roleNames.length > 0">
                  {{ userInfo.roleNames.join('，') }}
                </span>
                <span v-else class="no-data">-</span>
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">创建时间</span>
              <span class="stat-value">
                {{ userInfo.createTime ? formatDate(userInfo.createTime) : '-' }}
              </span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧 - 功能操作 -->
      <div class="right-panel">
        <!-- 基本信息卡片 -->
        <el-card class="action-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><User /></el-icon>
              <span>基本信息</span>
            </div>
          </template>

          <div class="info-list">
            <div class="info-item">
              <span class="info-label">用户名</span>
              <span class="info-value">{{ userInfo.userName || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">用户昵称</span>
              <div class="info-value-with-action">
                <span>{{ userInfo.nickName || '-' }}</span>
                <el-button type="primary" link size="small" @click="showNicknameDialog = true">
                  修改
                </el-button>
              </div>
            </div>
            <div class="info-item">
              <span class="info-label">备注信息</span>
              <span class="info-value">{{ userInfo.remark || '无' }}</span>
            </div>
          </div>
        </el-card>

        <!-- 安全设置卡片 -->
        <el-card class="action-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
            </div>
          </template>

          <div class="security-actions">
            <div class="security-item">
              <div class="security-info">
                <h4>登录密码</h4>
                <p>定期更换密码保证账户安全</p>
                <span class="password-tip" v-if="userInfo.modifyPassTime">
                  最后修改：{{ formatDate(userInfo.modifyPassTime) }}
                </span>
              </div>
              <el-button type="primary" @click="showPasswordDialog = true"> 修改密码 </el-button>
            </div>
          </div>
        </el-card>

        <!-- 系统信息卡片 -->
        <el-card class="action-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><InfoFilled /></el-icon>
              <span>系统信息</span>
            </div>
          </template>

          <div class="system-info">
            <div class="system-item">
              <span class="system-label">用户状态</span>
              <el-tag :type="userInfo.enabled === '1' ? 'success' : 'error'">
                {{ userInfo.enabled === '1' ? '正常' : '禁用' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 修改昵称对话框 -->
    <el-dialog
      v-model="showNicknameDialog"
      title="修改昵称"
      width="400px"
      :close-on-click-modal="true"
    >
      <el-form
        ref="nicknameFormRef"
        :model="nicknameForm"
        :rules="nicknameRules"
        label-width="80px"
      >
        <el-form-item label="当前昵称">
          <el-input v-model="userInfo.nickName" disabled />
        </el-form-item>
        <el-form-item label="新昵称" prop="nickName">
          <el-input
            v-model="nicknameForm.nickName"
            placeholder="请输入新昵称"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showNicknameDialog = false">取消</el-button>
          <el-button type="primary" @click="handleUpdateNickname" :loading="loading">
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="showPasswordDialog"
      title="修改密码"
      width="600px"
      :close-on-click-modal="true"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="120px"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="password">
          <el-input
            v-model="passwordForm.password"
            type="password"
            placeholder="请输入新密码（6-20位字符）"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showPasswordDialog = false">取消</el-button>
          <el-button type="primary" @click="handleUpdatePassword" :loading="loading">
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock, InfoFilled } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/time'
import userApi from '@/api/services/system/user'

// 响应式数据
const loading = ref(false)
const userInfo = ref({})
const showNicknameDialog = ref(false)
const showPasswordDialog = ref(false)

// 表单引用
const nicknameFormRef = ref()
const passwordFormRef = ref()

// 表单数据
const nicknameForm = reactive({
  nickName: '',
})

const passwordForm = reactive({
  oldPassword: '',
  password: '',
  confirmPassword: '',
})

// 验证规则
const nicknameRules = {
  nickName: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { min: 2, max: 20, message: '昵称长度在 2 到 20 个字符', trigger: 'blur' },
  ],
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.password) {
          callback(Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 获取当前用户信息
const getCurrentUserInfo = async () => {
  loading.value = true
  try {
    const currentUserId = getCurrentUserId()
    if (!currentUserId) {
      ElMessage.error('无法获取当前用户信息')
      return
    }

    // 如果后端只需要sysUser对象包含id
    const response = await userApi.getUserInfo({
      sysUser: { id: currentUserId },
    })

    if (response.code === 200) {
      userInfo.value = response.data || {}
      nicknameForm.nickName = userInfo.value.nickName || ''
    } else {
      ElMessage.error(response.message || '获取用户信息失败')
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  } finally {
    loading.value = false
  }
}

// 获取当前用户ID
const getCurrentUserId = () => {
  // 根据您的认证系统实现
  const userStr = localStorage.getItem('user_info') || sessionStorage.getItem('user_info') // 改为 user_info

  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      console.log('解析后的用户对象:', user)
      return user.id || user.userId
    } catch (e) {
      console.error('解析用户信息失败:', e)
    }
  }
  return null
}

// 修改昵称
const handleUpdateNickname = async () => {
  try {
    await nicknameFormRef.value.validate()
    loading.value = true

    const response = await userApi.editUserInfo({
      id: userInfo.value.id,
      nickName: nicknameForm.nickName,
      userName: userInfo.value.userName,
      enabled: userInfo.value.enabled,
      roleIdList: userInfo.value.roleIdList,
      remark: userInfo.value.remark,
    })

    if (response.code === 200) {
      ElMessage.success('昵称修改成功')
      showNicknameDialog.value = false
      userInfo.value.nickName = nicknameForm.nickName
      updateStoredUserInfo({ nickName: nicknameForm.nickName })
    } else {
      ElMessage.error(response.message || '昵称修改失败')
    }
  } catch (error) {
    if (error.errors) {
      ElMessage.error('请检查表单填写是否正确')
    }
  } finally {
    loading.value = false
  }
}

// 修改密码
const handleUpdatePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    loading.value = true

    const response = await userApi.modifyPassword({
      id: userInfo.value.id,
      oldPassword: passwordForm.oldPassword,
      password: passwordForm.password,
    })

    if (response.code === 200) {
      ElMessage.success('密码修改成功')
      showPasswordDialog.value = false
      // 清空表单
      Object.assign(passwordForm, {
        oldPassword: '',
        password: '',
        confirmPassword: '',
      })
      // 建议重新登录
      setTimeout(() => {
        ElMessage.info('为了安全，建议重新登录')
      }, 1000)
    } else {
      ElMessage.error(response.message || '密码修改失败')
    }
  } catch (error) {
    if (error.errors) {
      ElMessage.error('请检查表单填写是否正确')
    }
  } finally {
    loading.value = false
  }
}

// 更新存储的用户信息
const updateStoredUserInfo = (updates) => {
  try {
    const userStr = localStorage.getItem('user_Info') || sessionStorage.getItem('user_Info')
    if (userStr) {
      const user = JSON.parse(userStr)
      const updatedUser = { ...user, ...updates }
      localStorage.setItem('user_Info', JSON.stringify(updatedUser))
      sessionStorage.setItem('user_Info', JSON.stringify(updatedUser))
    }
  } catch (error) {
    console.error('更新存储的用户信息失败:', error)
  }
}

// 格式化日期（只显示日期）
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return formatDateTime(dateString).split(' ')[0]
}

onMounted(() => {
  getCurrentUserInfo()
})
</script>

<style scoped lang="scss">
.personal-center {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;

  .page-title {
    font-size: 28px;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 8px 0;
  }

  .page-desc {
    font-size: 16px;
    color: #6b7280;
    margin: 0;
  }
}

.content-container {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 24px;
  align-items: start;
}

// 左侧信息卡片
.left-panel {
  .info-card {
    border: none;
    border-radius: 12px;
    text-align: center;

    :deep(.el-card__body) {
      padding: 32px 24px;
    }
  }

  .user-avatar {
    margin-bottom: 20px;

    .avatar-circle {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      background: linear-gradient(135deg, #1c318e 0%, #170529 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto;

      .el-icon {
        font-size: 36px;
        color: white;
      }
    }
  }

  .user-basic-info {
    margin-bottom: 24px;

    .user-name {
      font-size: 20px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 8px 0;
    }

    .user-id {
      font-size: 14px;
      color: #6b7280;
      margin: 0 0 12px 0;
    }

    .status-tag {
      border-radius: 12px;
    }
  }

  .user-stats {
    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid #f3f4f6;

      &:last-child {
        border-bottom: none;
      }

      .stat-label {
        font-size: 14px;
        color: #6b7280;
      }

      .stat-value {
        font-size: 14px;
        color: #1f2937;
        font-weight: 500;
        text-align: right;
      }
    }
  }
}

// 右侧功能区域
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-card {
  border: none;
  border-radius: 12px;

  :deep(.el-card__header) {
    border-bottom: 1px solid #f3f4f6;
    padding: 20px 24px;

    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #1f2937;
      font-size: 16px;

      .el-icon {
        color: #667eea;
      }
    }
  }

  :deep(.el-card__body) {
    padding: 24px;
  }
}

// 基本信息列表
.info-list {
  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid #f8fafc;

    &:last-child {
      border-bottom: none;
    }

    .info-label {
      font-size: 14px;
      color: #6b7280;
      min-width: 80px;
    }

    .info-value {
      font-size: 14px;
      color: #1f2937;
    }

    .info-value-with-action {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
}

// 安全设置
.security-actions {
  .security-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;

    .security-info {
      h4 {
        margin: 0 0 4px 0;
        font-size: 14px;
        font-weight: 600;
        color: #1f2937;
      }

      p {
        margin: 0 0 4px 0;
        font-size: 13px;
        color: #6b7280;
      }

      .password-tip {
        font-size: 12px;
        color: #9ca3af;
      }
    }
  }
}

// 系统信息
.system-info {
  .system-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f8fafc;

    &:last-child {
      border-bottom: none;
    }

    .system-label {
      font-size: 14px;
      color: #6b7280;
    }

    .system-value {
      font-size: 14px;
      color: #1f2937;
      font-weight: 500;
    }
  }
}

// 对话框样式
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

// 响应式设计
@media (max-width: 968px) {
  .content-container {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .left-panel {
    max-width: 400px;
    margin: 0 auto;
  }
}

@media (max-width: 768px) {
  .personal-center {
    padding: 16px;
  }

  .page-header {
    .page-title {
      font-size: 24px;
    }

    .page-desc {
      font-size: 14px;
    }
  }
}

@media (max-width: 480px) {
  .personal-center {
    padding: 12px;
  }

  .action-card {
    :deep(.el-card__body) {
      padding: 20px;
    }
  }

  .security-item {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    text-align: center;
  }
}

.no-data {
  color: #9ca3af;
  font-style: italic;
}
</style>
