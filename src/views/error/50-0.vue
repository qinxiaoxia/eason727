<template>
  <div class="not-found-container">
    <div class="error-content">
      <!-- 错误代码 -->
      <div class="error-code">500</div>

      <!-- 错误标题 -->
      <h1 class="error-title">服务器内部错误</h1>

      <!-- 错误描述 -->
      <p class="error-message">
        抱歉，服务器暂时无法处理您的请求。
        <br />请稍后重试或联系技术支持。
      </p>

      <!-- 动画效果 -->
      <div class="animation-container">
        <div class="lost-illustration">
          <div class="server-icon">
            <div class="server-rack">
              <div class="server-light"></div>
              <div class="server-light"></div>
              <div class="server-light"></div>
            </div>
            <div class="warning-sign">!</div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="primary" class="btn-primary" @click="refreshPage">
          <i class="fas fa-redo"></i>
          刷新重试
        </el-button>

        <el-button class="btn-secondary" @click="goHome">
          <i class="fas fa-home"></i>
          返回首页
        </el-button>

        <el-button class="btn-secondary" @click="contactSupport">
          <i class="fas fa-headset"></i>
          技术支持
        </el-button>
      </div>

      <!-- 建议操作 -->
      <div class="suggestions">
        <h3>建议操作：</h3>
        <ul>
          <li>等待几分钟后刷新页面重试</li>
          <li>检查网络连接是否正常</li>
          <li>联系技术支持团队报告问题</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

// 刷新页面
const refreshPage = () => {
  window.location.reload()
}

// 返回首页
const goHome = () => {
  router.push('/')
}

// 联系技术支持
const contactSupport = () => {
  window.location.href = 'mailto:support@assets.com?subject=服务器错误报告'
}
</script>

<style scoped>
.server-icon {
  position: relative;
  width: 120px;
  height: 140px;
  margin: 0 auto;
}

.server-rack {
  width: 100px;
  height: 100px;
  background: #48356f;
  border-radius: 10px;
  position: relative;
  animation: pulse 2s ease-in-out infinite;
}

.server-light {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ff6b6b;
  animation: blink 1.5s ease-in-out infinite;
}

.server-light:nth-child(1) {
  top: 20px;
  left: 20px;
  animation-delay: 0s;
}

.server-light:nth-child(2) {
  top: 20px;
  left: 50px;
  animation-delay: 0.5s;
}

.server-light:nth-child(3) {
  top: 20px;
  left: 80px;
  animation-delay: 1s;
}

.warning-sign {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 40px;
  background: #ff6b6b;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 20px;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
</style>
