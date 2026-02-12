<template>
  <div class="not-found-container">
    <div class="error-content">
      <!-- 错误代码 -->
      <div class="error-code">404</div>

      <!-- 错误标题 -->
      <h1 class="error-title">页面不存在</h1>

      <!-- 错误描述 -->
      <p class="error-message">
        抱歉，您访问的页面不存在或已被移除。
        <br />请检查URL是否正确，或返回首页继续浏览。
      </p>

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

        <el-button class="btn-secondary" @click="refreshPage">
          <i class="fas fa-redo"></i>
          刷新页面
        </el-button>
      </div>

      <!-- 建议操作 -->
      <div class="suggestions">
        <h3>建议操作：</h3>
        <ul>
          <li>检查URL地址是否正确</li>
          <li>返回<a href="javascript:void(0)" @click="goHome">首页</a>浏览其他内容</li>
          <li>联系系统管理员报告此问题</li>
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

// 刷新页面
const refreshPage = () => {
  window.location.reload()
}
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.error-content {
  max-width: 800px;
  width: 100%;
  text-align: center;
  padding: 40px 30px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.error-code {
  font-size: 120px;
  font-weight: 800;
  color: #0f57b3;
  margin-bottom: 10px;
  text-shadow: 3px 3px 0 rgba(53, 71, 111, 0.1);
  line-height: 1;
}

.error-title {
  font-size: 32px;
  color: #0f57b3;
  margin-bottom: 20px;
  font-weight: 600;
}

.error-message {
  font-size: 18px;
  color: #666;
  margin-bottom: 30px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
}

.animation-container {
  margin: 30px 0;
  position: relative;
  height: 200px;
}

.lost-illustration {
  width: 200px;
  height: 200px;
  margin: 0 auto;
  position: relative;
}

.compass {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  border: 8px solid #0f57b3;
  border-radius: 50%;
  animation: rotate 10s linear infinite;
}

.compass::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  background: #0f57b3;
  border-radius: 50%;
}

.compass-n,
.compass-s,
.compass-e,
.compass-w {
  position: absolute;
  color: #0f57b3;
  font-weight: bold;
  font-size: 18px;
}

.compass-n {
  top: 5px;
  left: 50%;
  transform: translateX(-50%);
}
.compass-s {
  bottom: 5px;
  left: 50%;
  transform: translateX(-50%);
}
.compass-e {
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
}
.compass-w {
  left: 5px;
  top: 50%;
  transform: translateY(-50%);
}

.search-icon {
  position: absolute;
  bottom: 30px;
  right: 40px;
  font-size: 40px;
  color: #0f57b3;
  animation: bounce 2s ease-in-out infinite;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
  flex-wrap: wrap;
}

.btn-primary,
.btn-secondary {
  padding: 12px 30px;
  font-size: 16px;
  border-radius: 50px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 180px;
  justify-content: center;
}

.btn-primary {
  background: linear-gradient(135deg, #0f57b3 0%, #5878a1 100%);
  border: none;
  color: white;
}

.btn-primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 7px 20px rgba(165, 197, 228, 0.6);
}

.btn-secondary {
  background: transparent;
  color: #0f57b3;
  border: 2px solid #0f57b3;
}

.btn-secondary:hover {
  background: #0f57b3;
  color: white;
}

.suggestions {
  margin-top: 40px;
  text-align: left;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 10px;
  border-left: 4px solid #0f57b3;
}

.suggestions h3 {
  color: #0f57b3;
  margin-bottom: 15px;
  font-size: 18px;
}

.suggestions ul {
  list-style-type: none;
  padding-left: 0;
}

.suggestions li {
  margin-bottom: 10px;
  color: #666;
  position: relative;
  padding-left: 20px;
}

.suggestions li:before {
  content: '•';
  color: #0f57b3;
  font-weight: bold;
  position: absolute;
  left: 0;
}

.suggestions a {
  color: #264e87;
  text-decoration: none;
  font-weight: 500;
}

.suggestions a:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .error-code {
    font-size: 80px;
  }

  .error-title {
    font-size: 24px;
  }

  .error-message {
    font-size: 16px;
  }

  .action-buttons {
    flex-direction: column;
    align-items: center;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
    max-width: 300px;
  }

  .lost-illustration {
    width: 150px;
    height: 150px;
  }

  .compass {
    width: 100px;
    height: 100px;
  }

  .search-icon {
    font-size: 30px;
    bottom: 20px;
    right: 30px;
  }
}
</style>
