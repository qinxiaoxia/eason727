<template>
  <div class="not-found-container">
    <div class="error-content">
      <!-- 错误代码 -->
      <div class="error-code">403</div>

      <!-- 错误标题 -->
      <h1 class="error-title">访问被拒绝</h1>

      <!-- 错误描述 -->
      <p class="error-message">
        抱歉，您没有权限访问此页面。
        <br />请联系系统管理员获取相应权限。
      </p>

      <!-- 动画效果 -->
      <div class="animation-container">
        <div class="lost-illustration">
          <div class="shield-icon">
            <div class="shield"></div>
            <div class="lock"></div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="primary" class="btn-primary" @click="goHome">
          <i class="fas fa-home"></i>
          返回首页
        </el-button>

        <el-button class="btn-secondary" @click="goBack">
          <i class="fas fa-arrow-left"></i>
          返回上页
        </el-button>

        <el-button class="btn-secondary" @click="contactAdmin">
          <i class="fas fa-envelope"></i>
          联系管理员
        </el-button>
      </div>

      <!-- 建议操作 -->
      <div class="suggestions">
        <h3>可能的原因：</h3>
        <ul>
          <li>当前账号权限不足</li>
          <li>页面需要特定角色才能访问</li>
          <li>资产访问权限已被修改</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

// 返回首页
const goHome = () => {
  router.push('/')
}

// 返回上一页
const goBack = () => {
  router.go(-1)
}

// 联系管理员
const contactAdmin = () => {
  window.location.href = 'mailto:admin@assets.com?subject=权限申请'
}
</script>

<style scoped>
/* 复用404的基础样式，只修改特殊部分 */
.shield-icon {
  position: relative;
  width: 120px;
  height: 140px;
  margin: 0 auto;
}

.shield {
  width: 100%;
  height: 120px;
  background: #48356f;
  border-radius: 60% 60% 50% 50%;
  position: relative;
  animation: bounce 2s ease-in-out infinite;
}

.shield::before {
  content: '';
  position: absolute;
  top: 10px;
  left: 10px;
  right: 10px;
  bottom: 10px;
  border: 3px solid white;
  border-radius: 50% 50% 40% 40%;
}

.lock {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 40px;
  background: #ff6b6b;
  border-radius: 8px;
  animation: shake 1.5s ease-in-out infinite;
}

.lock::before {
  content: '';
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 30px;
  height: 20px;
  background: #ff6b6b;
  border-radius: 15px 15px 0 0;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(-50%) rotate(0deg);
  }
  25% {
    transform: translateX(-50%) rotate(-5deg);
  }
  75% {
    transform: translateX(-50%) rotate(5deg);
  }
}
</style>
