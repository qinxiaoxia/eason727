<!-- components/UserMenu.vue -->
<template>
  <div class="user-menu">
    <el-dropdown @command="handleCommand" trigger="click">
      <span class="user-info">
        <el-avatar :size="32" class="user-avatar">
          {{ userAvatarText }}
        </el-avatar>
        <span class="user-name">{{ userName }}</span>
        <el-icon class="arrow-down"><ArrowDown /></el-icon>
      </span>

      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="profile">
            <el-icon><User /></el-icon>
            <span>个人中心</span>
          </el-dropdown-item>
          <el-dropdown-item command="logout" divided>
            <el-icon><SwitchButton /></el-icon>
            <span>退出登录</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, SwitchButton, ArrowDown } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import authApi from '@/api/services/auth'

const router = useRouter()

// 计算用户显示名称
const userName = computed(() => {
  try {
    const userInfo = localStorage.getItem('user_info')
    if (!userInfo) return '用户'
    const user = JSON.parse(userInfo)
    return user.nickName || user.userName || '用户'
  } catch {
    return '用户'
  }
})

// 计算用户头像文本
const userAvatarText = computed(() => {
  try {
    const userInfo = localStorage.getItem('user_info')
    if (!userInfo) return 'U'
    const user = JSON.parse(userInfo)
    return (user.nickName?.charAt(0) || user.userName?.charAt(0) || 'U').toUpperCase()
  } catch {
    return 'U'
  }
})

// 获取用户ID
const getCurrentUserId = () => {
  try {
    const userInfo = localStorage.getItem('user_info')
    if (!userInfo) return null
    const user = JSON.parse(userInfo)
    return user.id
  } catch (error) {
    console.error('获取用户ID失败:', error)
    return null
  }
}

// 获取token
const getAuthToken = () => {
  return localStorage.getItem('Authorization')
}

// 处理下拉菜单命令
const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      handleProfile()
      break
    case 'logout':
      await handleLogout()
      break
  }
}

// 个人中心
const handleProfile = () => {
  router.push('/system/PersonalCenter')
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const userId = getCurrentUserId()
    const token = getAuthToken()

    if (!userId || !token) {
      console.warn('用户ID或token不存在，直接清除本地存储')
    } else {
      // 调用退出登录接口
      try {
        await authApi.logout({
          userId: userId,
          token: token,
        })
      } catch (error) {
        console.warn('登出接口调用失败，继续清除本地存储:', error)
      }
    }

    // 清除本地存储
    localStorage.removeItem('Authorization')
    localStorage.removeItem('user_info')
    localStorage.removeItem('user_role')
    localStorage.removeItem('dynamic_route_added')

    ElMessage.success('退出登录成功')

    // 跳转到登录页
    router.push('/login')
  } catch {
    // 用户取消退出
    console.log('用户取消退出登录')
  }
}
</script>

<style scoped>
.user-menu {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.user-avatar {
  background-color: #409eff;
  color: white;
  font-weight: bold;
}

.user-name {
  font-size: 14px;
  color: #d2d2d2;
  max-width: 100px;
  overflow: hidden;
  font-weight: bold;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow-down {
  font-size: 12px;
  color: #666;
  margin-left: 4px;
}
</style>
