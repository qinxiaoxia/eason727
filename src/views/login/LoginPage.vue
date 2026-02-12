<template>
  <div class="login-container">
    <!-- 左侧图片区域 -->
    <div class="login-left">
      <div class="platform-info">
        <div class="platform-logo">
          <i class="el-icon-data-analysis"></i>
          <span>攻防演练平台</span>
        </div>
      </div>
      <div class="world-map-bg">
        <div class="circuit-board"></div>
      </div>
    </div>

    <!-- 右侧登录表单区域 -->
    <div class="login-right">
      <div class="login-form-container">
        <div class="form-header">
          <p>欢迎使用攻防演练平台</p>
        </div>

        <el-form
          :model="loginForm"
          :rules="loginRules"
          ref="loginFormRef"
          class="login-form"
          size="large"
        >
          <el-form-item prop="userName">
            <el-input
              v-model="loginForm.userName"
              placeholder="请输入用户名"
              prefix-icon="user"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              show-password
              prefix-icon="Lock"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <!-- 验证码区域 -->
          <el-form-item prop="code" class="captcha-item">
            <div class="captcha-container">
              <el-input
                v-model="loginForm.code"
                placeholder="请输入验证码"
                @keyup.enter="handleLogin"
                class="captcha-input"
              />
              <div class="captcha-image-wrapper" @click="refreshCaptcha">
                <img
                  :src="captchaImage"
                  alt="验证码"
                  class="captcha-image"
                  v-if="captchaImage && !isLoadingCaptcha"
                />
                <div v-if="isLoadingCaptcha" class="captcha-loading">
                  <i class="el-icon-loading"></i>
                  加载中...
                </div>
                <div
                  v-if="!isLoadingCaptcha && !captchaImage"
                  class="captcha-error"
                  @click.stop="refreshCaptcha"
                >
                  <i class="el-icon-warning"></i>
                  加载失败，点击重试
                </div>
              </div>
            </div>
          </el-form-item>

          <!-- 登录按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              class="login-button"
              :loading="loading"
              @click="handleLogin"
              style="width: 100%"
              :disabled="!captchaImage"
            >
              {{ loading ? '登录中...' : '登录' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import userApi from '@/api/services/auth'

const router = useRouter()
const route = useRoute()

const isLoadingCaptcha = ref(false)
const loginLoading = ref(false)
const loginFormRef = ref(null)

// 登录表单
const loginForm = reactive({
  userName: '',
  password: '',
  code: '',
  codeKey: '',
})

// 验证码图片
const captchaImage = ref('')
const captchaKey = ref('')

// 移除前端验证规则，完全依赖后端验证
const loginRules = {
  // 保留基本格式验证，移除业务逻辑验证
  userName: [
    {
      required: true,
      message: '请输入用户名',
      trigger: 'blur',
    },
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: 'blur',
    },
  ],
  code: [
    {
      required: true,
      message: '请输入验证码',
      trigger: 'blur',
    },
  ],
}

// 获取验证码
const fetchCaptcha = async () => {
  try {
    isLoadingCaptcha.value = true
    console.log('开始获取验证码...')
    const res = await userApi.getCaptcha()
    console.log('验证码响应:', res)
    if (res.code === 200 && res.data) {
      const { codeKey, imageData } = res.data
      captchaImage.value = imageData
      captchaKey.value = codeKey
      loginForm.codeKey = codeKey
      console.log('验证码获取成功, key:', codeKey)
    } else {
      console.error('获取验证码失败:', res)
      captchaImage.value = ''
      // 移除前端错误提示，让用户点击重试
    }
  } catch (error) {
    console.error('获取验证码异常:', error)
    captchaImage.value = ''
    // 移除前端错误提示，让用户点击重试
  } finally {
    isLoadingCaptcha.value = false
  }
}

// 刷新验证码
const refreshCaptcha = () => {
  console.log('点击刷新验证码')
  loginForm.code = '' // 清空验证码输入框
  fetchCaptcha()
}

// 修改后的登录函数 - 完全依赖后端验证
const handleLogin = async () => {
  // 只进行基本表单验证
  try {
    await loginFormRef.value.validate()
  } catch {
    // 表单验证失败，不进行登录操作
    return
  }

  loginLoading.value = true

  try {
    const loginData = {
      userName: loginForm.userName,
      password: loginForm.password,
      code: loginForm.code,
      codeKey: captchaKey.value || loginForm.codeKey,
    }

    const res = await userApi.login(loginData)
    console.log('登录响应:', res)

    if (res.code === 200 && res.data) {
      const { token, userId } = res.data
      localStorage.setItem('Authorization', token)

      if (!token) {
        // 移除前端错误提示，完全依赖后端
        loginLoading.value = false
        return
      }

      console.log('~原始用户信息:', userId)

      // 获取用户信息
      let finalUserInfo = userId
      try {
        const userInfoRes = await userApi.getUserInfo({})
        if (userInfoRes.code === 200 && userInfoRes.data) {
          finalUserInfo = userInfoRes.data
          console.log('~从API获取的用户信息:', finalUserInfo)
          localStorage.setItem('user_info', JSON.stringify(finalUserInfo))
        } else {
          console.warn('获取用户信息失败，使用默认信息')
          finalUserInfo = {
            userName: loginForm.userName,
            permits: ['admin'],
            id: 0,
          }
        }
      } catch (error) {
        console.error('获取用户信息异常:', error)
        finalUserInfo = {
          userName: loginForm.userName,
          permits: ['admin'],
          id: 0,
        }
      }

      // 处理用户权限
      let userPermits = finalUserInfo.permits || ['user']
      if (!Array.isArray(userPermits)) {
        userPermits = [userPermits]
      }
      console.log('~最终用户权限:', userPermits)

      // 保存用户权限到本地存储
      localStorage.setItem('user_permits', JSON.stringify(userPermits))

      // 清除之前的路由状态
      localStorage.removeItem('dynamic_route_added')
      localStorage.removeItem('user_top_menus')

      ElMessage.success('登录成功')

      // 跳转到首页
      const redirect = route.query.redirect || '/overview'
      console.log('准备跳转到:', redirect)
      router.push(redirect)
    } else {
      // 完全使用后端返回的错误信息
      console.error('登录失败:', res)
      ElMessage.error(res.message || '登录失败')

      // 登录失败后刷新验证码
      await fetchCaptcha()
    }
  } catch (error) {
    // 网络异常等错误，使用通用提示
    console.error('登录异常:', error)
    ElMessage.error('网络异常，请稍后重试')

    // 异常情况下也刷新验证码
    await fetchCaptcha()
  } finally {
    loginLoading.value = false
  }
}

// 初始化
onMounted(() => {
  console.log('登录页面加载完成')
  fetchCaptcha()
})
</script>

<style scoped>
.login-container {
  display: flex;
  height: 98.2vh;
  width: auto;
  overflow: hidden;
  background: #dde7f7;
  position: relative;
}

.login-left {
  flex: 1.2;
  border-radius: 8px 0px 0px 8px;
  background: #19222f;
  position: relative;
  display: flex;
  height: 65vh;
  width: 65vw;
  margin-top: 16vh;
  margin-left: 10vw;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  overflow: hidden;
}

.platform-info {
  position: absolute;
  top: 40px;
  left: 40px;
  z-index: 2;
}

.platform-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.platform-logo i {
  font-size: 24px;
  color: #19222f;
}

.world-map-bg {
  position: absolute;
  top: 40;
  left: 5;
  width: 85%;
  height: 85%;
  background-image: url('@/assets/images/登录页.png'); /* 替换为你的图片路径 */
  background-size: cover;
  background-position: center;
  opacity: 1;
  z-index: 1;
}

.login-right {
  border-radius: 0px 8px 8px 0px;
  flex: 1;
  height: 65vh;
  width: 65vw;
  margin-top: 16vh;
  margin-right: 10vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #ffffff;
  position: relative;
  z-index: 1;
}

.login-form-container {
  width: 100%;
  max-width: 400px;
  padding: 0 20px;
  box-sizing: border-box;
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.form-header p {
  font-size: 20px;
  color: #73757a;
}

.login-form {
  width: 100%;
}

.captcha-item {
  margin-bottom: 20px;
}

.captcha-container {
  display: flex;
  gap: 10px;
  align-items: center;
}

.captcha-input {
  flex: 1;
}

.captcha-image-wrapper {
  position: relative;
  width: 130px;
  height: 40px;
  cursor: pointer;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  min-height: 40px;
}

.captcha-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.captcha-loading,
.captcha-error {
  color: #909399;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0 5px;
}

.captcha-loading i {
  font-size: 16px;
  margin-bottom: 2px;
  animation: rotate 2s linear infinite;
}

.captcha-error i {
  font-size: 16px;
  margin-bottom: 2px;
  color: #f56c6c;
}

.captcha-error {
  color: #f56c6c;
  cursor: pointer;
}

.captcha-error:hover {
  color: #f78989;
}

.captcha-refresh {
  position: absolute;
  top: 0;
  right: 0;
  width: 20px;
  height: 20px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  border-bottom-left-radius: 4px;
  opacity: 0;
  transition: opacity 0.3s;
}

.captcha-image-wrapper:hover .captcha-refresh {
  opacity: 1;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  margin-top: 10px;
}

.login-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }

  .login-left {
    flex: 0.4;
    min-height: 200px;
    width: 90vw;
    margin: 5vh auto;
  }

  .login-right {
    flex: 0.6;
    width: 90vw;
    margin: 0 auto 5vh;
  }

  .captcha-container {
    flex-direction: column;
  }

  .captcha-image-wrapper {
    width: 100%;
    height: 80px;
  }
}
</style>
