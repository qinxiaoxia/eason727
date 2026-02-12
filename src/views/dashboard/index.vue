<template>
  <div class="dashboard-container">
    <h1>仪表盘</h1>
    <elrow :gutter="20">
      <elcol :span="6">
        <elcard shadow="hover">
          <div class="card-content">
            <div class="card-icon" style="background-color: #409eff">
              <elicon><user /></elicon>
            </div>
            <div class="card-text">
              <div class="card-title">用户数</div>
              <div class="card-value">1,234</div>
            </div>
          </div>
        </elcard>
      </elcol>
      <!-- 其他卡片 -->
    </elrow>
  </div>
</template>

<script setup>
import { User } from '@element-plus/icons-vue'
</script>

<style scoped lang="scss">
.dashboard-container {
  .card-content {
    display: flex;
    align-items: center;

    .card-icon {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-right: 15px;

      .elicon {
        font-size: 24px;
      }
    }

    .card-title {
      font-size: 0.9rem;
      color: #909399;
    }

    .card-value {
      font-size: 1rem;
      margin-top: 0.5rem;
    }
  }
}
</style>
