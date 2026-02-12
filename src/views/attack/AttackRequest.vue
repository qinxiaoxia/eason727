<template>
  <div class="attack-request-container">
    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="main-filters">
        <!-- 关键词搜索 -->
        <el-input
          v-model="filterParams.keyword"
          placeholder="搜索攻击/防守单位"
          clearable
          @input="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        />

        <!-- 时间筛选 -->
        <div class="time-filter-group">
          <el-select
            v-model="selectedTimeField"
            placeholder="更新时间"
            class="time-field-select"
            style="width: 120px"
            @change="handleTimeFieldChange"
          >
            <el-option label="更新时间" value="updateTime" />
            <el-option label="创建时间" value="createTime" />
          </el-select>
          <TimeRangePicker
            v-model:time-field="selectedTimeField"
            :immediate="true"
            show-time-field="false"
            class="time-range-picker"
            @change="handleTimeRangeChange"
            @confirm="handleTimeConfirm"
            @clear="handleTimeClear"
          />
        </div>

        <!-- 操作按钮 -->
        <el-button-group class="action-buttons">
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
          <el-button @click="showMoreFilters = !showMoreFilters">
            <el-icon><Filter /></el-icon>{{ showMoreFilters ? '收起' : '更多' }}
          </el-button>
        </el-button-group>
      </div>

      <!-- 更多筛选 -->
      <el-collapse-transition>
        <div v-show="showMoreFilters" class="advanced-filters">
          <el-row :gutter="16">
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.attackTeamId"
                placeholder="攻击单位ID"
                type="number"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.defenseTeamId"
                placeholder="防守单位ID"
                type="number"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.projectId"
                placeholder="项目ID"
                type="number"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
          </el-row>
        </div>
      </el-collapse-transition>
    </div>

    <!-- 表格区域 -->
    <el-card class="table-card">
      <!-- 表格操作区域 -->
      <div class="table-actions">
        <el-button-group>
          <el-button type="primary" @click="handleAddRequest">
            <el-icon><Plus /></el-icon>新增申请
          </el-button>
          <el-button :disabled="!selectedRows.length" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>批量删除
          </el-button>
        </el-button-group>
        <div class="table-right-actions">
          <el-button @click="handleRefresh" plain>
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>

      <!-- 数据表格 -->
      <el-table
        :data="tableData"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        border
        stripe
        style="width: 100%; margin-top: 16px"
        key="request-table"
      >
        <!-- 选择列 -->
        <el-table-column type="selection" width="50" align="center" />

        <!-- 申请ID -->
        <el-table-column prop="id" label="申请ID" min-width="180">
          <template #default="{ row }">
            <div class="id-cell">
              <el-tooltip :content="String(row.id)" placement="top">
                <span class="id-text">{{ row.id }}</span>
              </el-tooltip>
              <el-icon class="copy-icon" @click="copyToClipboard(row.id)">
                <DocumentCopy />
              </el-icon>
            </div>
          </template>
        </el-table-column>

        <!-- 攻击队伍ID -->
        <el-table-column prop="attackTeamId" label="攻击单位ID" width="120" align="center" />

        <!-- 攻击队伍名称 -->
        <el-table-column
          prop="attackTeamName"
          label="攻击队伍"
          width="150"
          align="center"
          show-overflow-tooltip
        />

        <!-- 防守单位ID -->
        <el-table-column prop="defenseTeamId" label="防守单位ID" width="120" align="center" />

        <!-- 防守单位名称 -->
        <el-table-column
          prop="defenseOrganization"
          label="防守单位"
          width="150"
          align="center"
          show-overflow-tooltip
        />

        <!-- 系统名称 -->
        <el-table-column prop="systemName" label="系统名称" width="150" show-overflow-tooltip />

        <!-- 目标IP -->
        <el-table-column prop="targetIp" label="目标IP" width="120" align="center" />

        <!-- 目标端口 -->
        <el-table-column prop="targetPort" label="目标端口" width="100" align="center" />

        <!-- 目标URL -->
        <el-table-column prop="targetUrl" label="目标URL" min-width="200" show-overflow-tooltip />

        <!-- 攻击方案 -->
        <el-table-column prop="attackPlan" label="攻击方案" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.attackPlan" class="text-ellipsis" :title="row.attackPlan">
              {{ row.attackPlan }}
            </span>
            <span v-else class="text-muted">暂无方案</span>
          </template>
        </el-table-column>

        <!-- 状态 -->
        <el-table-column prop="status" label="状态" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="light">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 审核时间 -->
        <el-table-column prop="reviewTime" label="审核时间" width="160" align="center" sortable>
          <template #default="{ row }">
            <el-tooltip :content="formatFullTime(row.reviewTime)" placement="top">
              <span>{{ formatTimeAgo(row.reviewTime) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <!-- 审核人 -->
        <el-table-column prop="reviewerName" label="审核人" width="120" align="center" />

        <!-- 操作列 -->
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <div class="icon-actions">
              <!-- 查看详情 -->
              <el-tooltip content="查看详情" placement="top">
                <el-icon class="action-icon view-icon" @click="handleViewDetail(row)">
                  <View />
                </el-icon>
              </el-tooltip>

              <!-- 编辑 -->
              <el-tooltip content="编辑" placement="top">
                <el-icon
                  v-if="row.status === 'draft' || row.status === 'rejected'"
                  class="action-icon edit-icon"
                  @click="handleEditRequest(row)"
                  :disabled="!hasPermission('attackRequest:edit')"
                >
                  <Edit />
                </el-icon>
              </el-tooltip>

              <!-- 提交 -->
              <el-tooltip content="提交" placement="top">
                <el-icon
                  v-if="row.status === 'draft'"
                  class="action-icon submit-icon"
                  @click="handleSubmitRequest(row)"
                >
                  <Check />
                </el-icon>
              </el-tooltip>

              <!-- 审核 -->
              <el-tooltip content="审核" placement="top">
                <el-icon
                  v-if="row.status === 'pending'"
                  class="action-icon review-icon"
                  @click="handleReviewRequest(row)"
                  :disabled="!hasPermission('attackRequest:audit')"
                >
                  <DocumentChecked />
                </el-icon>
              </el-tooltip>

              <!-- 删除 -->
              <el-tooltip content="删除" placement="top">
                <el-icon class="action-icon delete-icon" @click="handleDelete(row)">
                  <Delete />
                </el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
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
      size="60%"
      class="request-drawer"
      :close-on-click-modal="true"
    >
      <div class="drawer-content" v-if="drawerVisible">
        <!-- 基础信息 -->
        <el-card shadow="never" class="form-section">
          <template #header>
            <div class="card-header">
              <span>| 基础信息</span>
            </div>
          </template>

          <el-form :model="formData" label-width="120px" ref="formRef">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="防守单位名称" required>
                  <el-input
                    v-model="formData.defenseOrganization"
                    placeholder="请输入防守单位名称"
                    clearable
                  />
                </el-form-item>
              </el-col>

              <el-col :span="8">
                <el-form-item label="系统名称" required>
                  <el-input v-model="formData.systemName" placeholder="请输入系统名称" clearable />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="目标IP" required>
                  <el-input v-model="formData.targetIp" placeholder="请输入目标IP地址" clearable />
                </el-form-item>
              </el-col>

              <el-col :span="8">
                <el-form-item label="目标端口">
                  <el-input
                    v-model.number="formData.targetPort"
                    placeholder="请输入目标端口"
                    type="number"
                    clearable
                  />
                </el-form-item>
              </el-col>

              <el-col :span="8">
                <el-form-item label="目标URL">
                  <el-input v-model="formData.targetUrl" placeholder="请输入目标URL" clearable />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="攻击方案">
              <el-input
                v-model="formData.attackPlan"
                type="textarea"
                :rows="4"
                placeholder="请输入攻击方案描述"
                maxlength="1000"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </el-card>
        <!-- 附件上传区域 - 新增 -->
        <el-card shadow="never" class="attachment-section">
          <template #header>
            <div class="card-header">
              <span>| 附件上传（必须上传至少一张截图）</span>
            </div>
          </template>

          <el-upload
            ref="uploadRef"
            action="#"
            :before-upload="beforeUpload"
            :on-remove="handleRemove"
            :on-change="handleFileChange"
            :auto-upload="false"
            :file-list="fileList"
            :limit="5"
            list-type="picture-card"
            accept=".jpg,.jpeg,.png,.gif,.bmp"
            multiple
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip">
                必须上传至少一张截图，支持 JPG/PNG/GIF/BMP 格式，单个文件不超过10MB
              </div>
            </template>
          </el-upload>

          <!-- 文件预览区域 -->
          <div v-if="selectedFiles.length > 0" class="file-preview">
            <h4>已选择文件 ({{ selectedFiles.length }}/5):</h4>
            <div class="file-list">
              <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
                <el-icon><Document /></el-icon>
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">({{ formatFileSize(file.size) }})</span>
                <el-icon class="remove-icon" @click="removeFile(index)">
                  <Close />
                </el-icon>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="saving">
            {{ drawerMode === 'add' ? '创建' : '更新' }}
          </el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="detailVisible"
      :title="`申请详情 - ID: ${currentDetail?.id || '未知'}`"
      direction="rtl"
      size="70%"
      class="detail-drawer"
    >
      <div class="detail-content" v-if="currentDetail">
        <div class="detail-header">
          <h2>申请详情</h2>
        </div>

        <el-card shadow="never" class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="申请ID">{{
              currentDetail.id || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="攻击单位ID">{{
              currentDetail.attackTeamId || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="攻击队伍">{{
              currentDetail.attackTeamName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="防守单位ID">{{
              currentDetail.defenseTeamId || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="防守单位">{{
              currentDetail.defenseOrganization || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="系统名称">{{
              currentDetail.systemName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="项目ID">{{
              currentDetail.projectId || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="目标IP">{{
              currentDetail.targetIp || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="目标端口">{{
              currentDetail.targetPort || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="目标URL">{{
              currentDetail.targetUrl || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(currentDetail.status)">
                {{ getStatusText(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="审核人">{{
              currentDetail.reviewerName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="审核时间">{{
              formatFullTime(currentDetail.reviewTime)
            }}</el-descriptions-item>
            <el-descriptions-item label="审核意见" :span="2">
              {{ currentDetail.reviewNotes || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="攻击方案" :span="2">
              {{ currentDetail.attackPlan || '暂无方案' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-card
          shadow="never"
          class="attachments-card"
          v-if="currentDetail && currentDetail.screenshotName"
        >
          <template #header>
            <div class="card-header">
              <span>| 附件列表</span>
            </div>
          </template>

          <div class="attachment-detail-list">
            <div class="attachment-detail-item">
              <div class="attachment-info">
                <el-icon class="file-icon"><Document /></el-icon>
                <div class="file-details">
                  <span class="file-name">{{ currentDetail.screenshotName }}</span>
                  <span class="file-type">截图文件</span>
                </div>
              </div>

              <div class="attachment-actions">
                <el-button
                  v-if="isImageFile(currentDetail.screenshotName)"
                  type="primary"
                  link
                  @click="handlePreviewScreenshot(currentDetail)"
                >
                  预览
                </el-button>

                <el-button type="primary" link @click="handleDownloadScreenshot(currentDetail)">
                  下载
                </el-button>
              </div>
            </div>
          </div>

          <!-- 图片预览区域 -->
          <!-- 图片预览区域 -->
          <div v-if="isImageFile(currentDetail.screenshotName)" class="image-preview-section">
            <h4>截图预览</h4>
            <div class="image-grid">
              <el-image
                :src="getAttachmentUrl(currentDetail.id)"
                :preview-src-list="[getAttachmentUrl(currentDetail.id)]"
                fit="cover"
                class="detail-image"
                :alt="currentDetail.screenshotName"
                loading="lazy"
                @error="handleImageError"
                @load="handleImageLoad"
              >
                <template #error>
                  <div class="image-error" @click="handlePreviewScreenshot(currentDetail)">
                    <el-icon><Picture /></el-icon>
                    <span>点击预览</span>
                  </div>
                </template>

                <template #placeholder>
                  <div class="image-loading">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>加载中...</span>
                  </div>
                </template>
              </el-image>
            </div>
          </div>
        </el-card>

        <!-- 关联成果列表 -->
        <el-card
          shadow="never"
          class="achievements-card"
          v-if="currentDetail.attackAchievementList && currentDetail.attackAchievementList.length"
        >
          <template #header>
            <div class="card-header">
              <span>| 关联成果列表 ({{ currentDetail.attackAchievementList.length }})</span>
            </div>
          </template>

          <el-table :data="currentDetail.attackAchievementList" border stripe>
            <el-table-column prop="achievementName" label="成果名称" min-width="200" />
            <el-table-column prop="assetName" label="资产名称" width="150" />
            <el-table-column prop="assetIP" label="资产IP" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="actualScore" label="得分" width="80" align="center" />
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleViewAchievement(row)">
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-drawer>

    <!-- 审核抽屉 -->
    <el-drawer
      v-model="reviewVisible"
      title="申请审核"
      direction="rtl"
      size="50%"
      class="review-drawer"
    >
      <div class="review-content" v-if="currentReview">
        <el-form :model="reviewForm" label-width="100px">
          <el-form-item label="申请ID">
            <span>{{ currentReview.id }}</span>
          </el-form-item>
          <el-form-item label="攻击队伍">
            <span>{{ currentReview.attackTeamName }}</span>
          </el-form-item>
          <el-form-item label="防守单位">
            <span>{{ currentReview.defenseOrganization }}</span>
          </el-form-item>
          <el-form-item label="审核意见" required>
            <el-input
              v-model="reviewForm.reviewNotes"
              type="textarea"
              :rows="4"
              placeholder="请输入审核意见"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="审核结果" required>
            <el-radio-group v-model="reviewForm.status">
              <el-radio label="approved">通过</el-radio>
              <el-radio label="rejected">拒绝</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="review-footer">
          <el-button @click="reviewVisible = false">取消</el-button>
          <el-button type="primary" @click="handleReviewSubmit">提交审核</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Delete,
  Refresh,
  Filter,
  DocumentCopy,
  View,
  Edit,
  Check,
  DocumentChecked,
  Document,
  Close,
} from '@element-plus/icons-vue'
import TimeRangePicker from '@/components/TimeRangePicker.vue'
import { attackRequestApi } from '@/api/services/attack/attackRequest.js'
import { useUserStore } from '@/stores/user'
const userStore = useUserStore()
const hasPermission = (permission) => {
  return userStore.permissions?.includes(permission)
}
// 状态
const loading = ref(false)
const saving = ref(false)
const showMoreFilters = ref(false)
const drawerVisible = ref(false)
const detailVisible = ref(false)
const reviewVisible = ref(false)
const tableData = ref([])
const selectedRows = ref([])
// 文件上传相关
const uploadRef = ref(null)
const fileList = ref([])
const selectedFiles = ref([]) // 存储实际文件对象
// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

// 筛选参数
const filterParams = reactive({
  keyword: '',
  attackTeamId: '',
  defenseTeamId: '',
  projectId: '',
  status: '',
})

// 时间筛选
const selectedTimeField = ref('updateTime')
const searchTimeRange = reactive({
  hasTimeRange: 0,
  timeField: 'updateTime',
  minTime: '',
  maxTime: '',
})

// 抽屉模式
const drawerMode = ref('add') // 'add' | 'edit'
const drawerTitle = computed(() => (drawerMode.value === 'add' ? '新增攻击申请' : '编辑攻击申请'))

// 表单数据 - 根据接口结构调整
const formData = reactive({
  attackTeamId: '',
  attackTeamName: '',
  defenseTeamId: '',
  defenseOrganization: '',
  systemName: '',
  targetIp: '',
  targetPort: '',
  targetUrl: '',
  projectId: '',
  attackPlan: '',
})

// 当前操作的数据
const currentDetail = ref(null)
const currentReview = ref(null)
const reviewForm = reactive({
  reviewNotes: '',
  status: 'approved',
})
// ========== 文件上传相关函数 ==========
// 文件上传前验证
const beforeUpload = (file) => {
  const isImage = /\.(jpg|jpeg|png|gif|bmp)$/i.test(file.name)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isImage) {
    ElMessage.error('只能上传图片格式文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过10MB!')
    return false
  }
  return true
}

// 修改图片加载错误处理
const handleImageError = (event) => {
  console.error('❌ 图片加载失败:', event)
  // 可以考虑显示一个占位符或错误消息
  ElMessage.error('图片加载失败')
}
const handleImageLoad = (event) => {
  console.log('✅ 图片加载成功:', event)
}

// 文件选择变化
const handleFileChange = (file, fileList) => {
  console.log('文件变化:', file, fileList)

  // 只保留状态为 ready 或 success 的文件
  const validFiles = fileList.filter((item) => item.status === 'ready' || item.status === 'success')

  fileList.value = validFiles

  // 存储原始文件对象 - 确保获取到 raw 文件
  selectedFiles.value = validFiles
    .map((item) => {
      return item.raw || item // 优先使用 raw 属性
    })
    .filter(Boolean)

  console.log('选中的文件对象:', selectedFiles.value)
}

// 文件移除
const handleRemove = (file, fileList) => {
  console.log('文件移除:', file, fileList)
  fileList.value = fileList
  selectedFiles.value = fileList.map((item) => item.raw || item).filter(Boolean)
}

// 手动移除文件
const removeFile = (index) => {
  if (uploadRef.value && fileList.value[index]) {
    uploadRef.value.handleRemove(fileList.value[index])
  }
}
// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 清空文件列表
const clearFiles = () => {
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  fileList.value = []
  selectedFiles.value = []
}
// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      limit: pagination.pageSize,
      data: { ...filterParams },
    }

    console.log('请求参数:', params)
    const result = await attackRequestApi.getPageList(params)
    console.log('接口处理后的响应:', result)

    // 修复响应判断逻辑
    if (result && result.code === 200) {
      tableData.value = result.data || []
      // 正确处理总数
      pagination.total = result.total || result.data?.length || 0

      console.log('表格数据数量:', tableData.value.length)
      console.log('分页总数:', pagination.total)

      if (tableData.value.length === 0) {
        ElMessage.info('没有查询到数据')
      }
    } else {
      console.warn('接口返回异常:', result)
      tableData.value = []
      pagination.total = 0
      ElMessage.warning('获取数据失败')
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 搜索相关函数
const handleSearch = () => {
  pagination.currentPage = 1
  fetchData()
}

const handleReset = () => {
  Object.keys(filterParams).forEach((key) => {
    filterParams[key] = ''
  })
  pagination.currentPage = 1
  fetchData()
}

const handleRefresh = () => {
  fetchData()
  ElMessage.success('数据已刷新')
}

// 时间筛选
const handleTimeFieldChange = (value) => {
  selectedTimeField.value = value
  handleSearch()
}

const handleTimeRangeChange = (timeData) => {
  if (timeData && timeData.startTime && timeData.endTime) {
    searchTimeRange.hasTimeRange = 1
    searchTimeRange.minTime = timeData.startStr
    searchTimeRange.maxTime = timeData.endStr
    handleSearch()
  } else {
    searchTimeRange.hasTimeRange = 0
    handleSearch()
  }
}

const handleTimeConfirm = (timeData) => {
  console.log('时间确认:', timeData)
}

const handleTimeClear = () => {
  searchTimeRange.hasTimeRange = 0
  handleSearch()
}

// 表格操作
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  fetchData()
}

const handleCurrentChange = (page) => {
  pagination.currentPage = page
  fetchData()
}

const handleAddRequest = () => {
  drawerMode.value = 'add'
  // 重置表单数据
  Object.keys(formData).forEach((key) => {
    formData[key] = ''
  })
  // 清空文件列表
  clearFiles()
  drawerVisible.value = true
}

const handleEditRequest = (row) => {
  drawerMode.value = 'edit'
  currentDetail.value = row
  // 填充表单
  Object.keys(formData).forEach((key) => {
    formData[key] = row[key] || ''
  })
  // 清空文件列表（编辑时可能需要重新上传）
  clearFiles()
  drawerVisible.value = true
}

const handleViewDetail = async (row) => {
  try {
    const result = await attackRequestApi.getInfo({ id: row.id })
    console.log('详情数据:', result)
    currentDetail.value = result.data || result
    detailVisible.value = true
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取详情失败: ' + error.message)
  }
}

const handleSubmitRequest = async (row) => {
  try {
    await ElMessageBox.confirm('确定提交此申请吗？提交后将进入审核流程', '提交确认', {
      type: 'warning',
      confirmButtonText: '确定提交',
      cancelButtonText: '取消',
    })

    // 准备提交数据
    const submitData = {
      id: row.id,
      attackTeamId: row.attackTeamId,
      attackTeamName: row.attackTeamName,
      defenseTeamId: row.defenseTeamId,
      defenseOrganization: row.defenseOrganization,
      systemName: row.systemName,
      targetIp: row.targetIp,
      targetPort: row.targetPort,
      targetUrl: row.targetUrl,
      projectId: row.projectId,
      attackPlan: row.attackPlan,
    }

    console.log('提交数据:', submitData)

    // 提交申请（如果需要重新上传文件，这里需要处理）
    const result = await attackRequestApi.submit(submitData, [])

    if (result && result.code === 200) {
      ElMessage.success('申请提交成功')
      fetchData()
    } else {
      const errorMsg = result?.message || '提交失败'
      ElMessage.error(`提交失败: ${errorMsg}`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('提交失败: ' + error.message)
    }
  }
}

// 审核请求
const handleReviewRequest = (row) => {
  currentReview.value = row
  reviewForm.reviewNotes = ''
  reviewForm.status = 'approved'
  reviewVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除申请 ID:${row.id} 吗?`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await attackRequestApi.batchRemove([row.id])
    console.log('删除响应:', result) // 添加调试日志

    // 修复判断逻辑
    if (result && (result.code === 200 || result.success)) {
      ElMessage.success('删除成功')
      // 强制刷新数据
      await fetchData()
    } else {
      // 更详细的错误信息
      const errorMsg = result?.message || result?.data?.message || '删除失败'
      console.error('删除失败详情:', result)
      ElMessage.error(`删除失败: ${errorMsg}`)
    }
  } catch (error) {
    console.error('删除异常:', error)
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

const handleBatchDelete = async () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要删除的申请')
    return
  }

  try {
    const ids = selectedRows.value.map((item) => item.id)
    await ElMessageBox.confirm(`确定删除选中的 ${ids.length} 条申请吗?`, '批量删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await attackRequestApi.batchRemove(ids)
    console.log('批量删除响应:', result) // 添加调试日志

    // 修复判断逻辑
    if (result && (result.code === 200 || result.success)) {
      ElMessage.success(`成功删除 ${ids.length} 条申请`)
      selectedRows.value = []
      // 强制刷新数据
      await fetchData()
    } else {
      const errorMsg = result?.message || result?.data?.message || '批量删除失败'
      console.error('批量删除失败详情:', result)
      ElMessage.error(`批量删除失败: ${errorMsg}`)
    }
  } catch (error) {
    console.error('批量删除异常:', error)
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败: ' + error.message)
    }
  }
}

const handleSave = async () => {
  try {
    saving.value = true

    // 验证必填字段
    const requiredFields = [
      { field: 'defenseOrganization', name: '防守单位名称' },
      { field: 'systemName', name: '系统名称' },
      { field: 'targetIp', name: '目标IP地址' },
    ]

    for (const { field, name } of requiredFields) {
      if (!formData[field]?.trim()) {
        ElMessage.warning(`请输入${name}`)
        return
      }
    }

    // 验证附件
    if (selectedFiles.value.length === 0) {
      ElMessage.warning('必须上传至少一张截图')
      return
    }

    // 准备保存数据
    const saveData = {
      attackTeamId: formData.attackTeamId || 0,
      attackTeamName: formData.attackTeamName.trim(),
      defenseTeamId: formData.defenseTeamId || 0,
      defenseOrganization: formData.defenseOrganization.trim(),
      systemName: formData.systemName.trim(),
      targetIp: formData.targetIp.trim(),
      targetPort: Number(formData.targetPort) || 0,
      targetUrl: formData.targetUrl?.trim() || '',
      projectId: formData.projectId || 0,
      attackPlan: formData.attackPlan?.trim() || '',
    }

    console.log('=== 调试信息开始 ===')
    console.log('保存数据:', saveData)
    console.log('JSON字符串:', JSON.stringify(saveData))
    console.log('文件信息:', selectedFiles.value)
    console.log('文件数量:', selectedFiles.value.length)

    // 处理文件对象 - 确保获取实际文件
    const filesToUpload = selectedFiles.value.map((file) => file.raw || file)
    console.log('实际文件对象:', filesToUpload)
    console.log('=== 调试信息结束 ===')

    let result
    if (drawerMode.value === 'edit' && currentDetail.value?.id) {
      result = await attackRequestApi.modify(saveData, selectedFiles.value)
    } else {
      result = await attackRequestApi.add(saveData, selectedFiles.value)
    }

    console.log('保存响应:', result)

    if (result && result.code === 200) {
      ElMessage.success(drawerMode.value === 'add' ? '创建成功' : '更新成功')
      drawerVisible.value = false
      // 保存成功后立即刷新数据
      await fetchData()
    } else {
      const errorMsg = result?.message || '保存失败'
      ElMessage.error(`保存失败: ${errorMsg}`)
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}
// 替换 getAttachmentUrl 方法
const getAttachmentUrl = async (requestId) => {
  if (!requestId) return ''

  try {
    console.log('🔄 获取文件URL (通过ID):', requestId)

    const fileUrl = await attackRequestApi.getFileUrlById(requestId)

    if (fileUrl) {
      console.log('✅ 通过ID获取URL成功')
      return fileUrl
    } else {
      console.warn('⚠️ 文件数据异常，返回空URL')
      return ''
    }
  } catch (error) {
    console.error('❌ 获取文件URL失败:', error)
    return ''
  }
}
// 判断是否为图片文件
const isImageFile = (fileName) => {
  if (!fileName) return false
  const lowerFileName = fileName.toLowerCase()
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
  return imageExtensions.some((ext) => lowerFileName.endsWith(ext))
}

// 判断是否为PDF文件
const isPdfFile = (fileName) => {
  if (!fileName) return false
  return fileName.toLowerCase().endsWith('.pdf')
}
// 判断文件类型
const getFileType = (fileName) => {
  if (isImageFile(fileName)) return 'image'
  if (isPdfFile(fileName)) return 'pdf'
  return 'other'
}
const handlePreviewScreenshot = async (row) => {
  try {
    if (!row.id) {
      ElMessage.warning('没有有效的记录ID')
      return
    }

    // 获取文件类型
    const fileType = getFileType(row.screenshotName)

    if (fileType === 'image') {
      // 图片文件，使用图片预览
      await previewImageById(row.id)
    } else if (fileType === 'pdf') {
      // PDF文件，在新窗口打开
      await previewPdfById(row.id)
    } else {
      ElMessage.warning('不支持的文件类型预览')
    }
  } catch (error) {
    console.error('❌ 预览异常:', error)
    ElMessage.error('预览失败: ' + (error.message || '未知错误'))
  }
}
// 预览图片
const previewImageById = async (requestId) => {
  try {
    console.log('🖼️ 开始预览图片 (通过ID):', requestId)

    const fileUrl = await attackRequestApi.getFileUrlById(requestId)

    if (fileUrl) {
      console.log('✅ 通过ID获取图片URL成功')
      window.open(fileUrl, '_blank')
      // 延迟释放URL，让用户有足够时间查看
      setTimeout(() => {
        window.URL.revokeObjectURL(fileUrl)
      }, 10000) // 延迟到10秒后释放
    } else {
      ElMessage.error('无法获取图片预览链接')
    }
  } catch (error) {
    console.error('❌ 图片预览失败:', error)
    ElMessage.error('图片预览失败: ' + error.message)
  }
}
// 预览PDF
const previewPdfById = async (requestId) => {
  try {
    console.log('📄 开始预览PDF (通过ID):', requestId)

    // 下载PDF文件
    const blobData = await attackRequestApi.downloadFileById(requestId)

    if (blobData instanceof Blob) {
      // 创建PDF的blob URL
      const pdfBlob = new Blob([blobData], { type: 'application/pdf' })
      const pdfUrl = window.URL.createObjectURL(pdfBlob)

      // 在新窗口打开PDF
      window.open(pdfUrl, '_blank')

      // 延迟释放URL
      setTimeout(() => {
        window.URL.revokeObjectURL(pdfUrl)
      }, 10000)
    } else {
      throw new Error('返回的不是有效的PDF文件')
    }
  } catch (error) {
    console.error('❌ PDF预览失败:', error)
    ElMessage.error('PDF预览失败: ' + error.message)
  }
}

// 修改下载函数以支持多种文件类型
const handleDownloadScreenshot = async (row) => {
  try {
    if (!row.id) {
      ElMessage.warning('没有有效的记录ID')
      return
    }

    console.log('💾 开始下载文件 (通过ID):', row.id)

    // 使用ID下载文件
    const blobData = await attackRequestApi.downloadFileById(row.id)

    if (blobData instanceof Blob) {
      // 检查文件大小和类型
      if (blobData.size < 1024) {
        const text = await blobData.text()
        try {
          const errorData = JSON.parse(text)
          throw new Error(errorData.message || '文件可能不存在')
        } catch {
          throw new Error('文件大小异常，下载失败')
        }
      }

      // 创建下载链接
      const url = window.URL.createObjectURL(blobData)
      const link = document.createElement('a')
      link.href = url

      // 使用原始文件名或基于类型生成默认文件名
      let fileName = row.screenshotName
      if (!fileName) {
        // 根据响应头推断文件类型
        const contentType = blobData.type
        if (contentType.includes('image')) {
          fileName = `attachment_${row.id}.jpg`
        } else if (contentType.includes('pdf')) {
          fileName = `attachment_${row.id}.pdf`
        } else {
          fileName = `attachment_${row.id}.dat`
        }
      }

      link.download = fileName

      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      // 释放URL
      setTimeout(() => {
        window.URL.revokeObjectURL(url)
      }, 1000)

      ElMessage.success('下载成功')
    } else {
      throw new Error('返回数据格式错误')
    }
  } catch (error) {
    console.error('❌ 下载失败:', error)
    ElMessage.error(`下载失败: ${error.message}`)
  }
}

// 审核相关
const handleReviewSubmit = async () => {
  try {
    if (!reviewForm.reviewNotes?.trim()) {
      ElMessage.warning('请输入审核意见')
      return
    }

    const reviewData = {
      id: currentReview.value.id,
      reviewNotes: reviewForm.reviewNotes.trim(),
      status: reviewForm.status,
    }

    console.log('审核数据:', reviewData)

    const result = await attackRequestApi.approve(reviewData)
    console.log('审核响应:', result)

    if (result && result.code === 200) {
      ElMessage.success('审核提交成功')
      reviewVisible.value = false
      fetchData()
    } else {
      const errorMsg = result?.message || result?.data?.message || '审核失败'
      ElMessage.error(`审核失败: ${errorMsg}`)
    }
  } catch (error) {
    console.error('审核失败:', error)
    ElMessage.error('审核失败: ' + error.message)
  }
}

// 状态处理函数
const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    in_progress: 'primary',
    completed: 'success',
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    draft: '待提交',
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    in_progress: '进行中',
    completed: '已完成',
  }
  return textMap[status] || status
}

const getStatusTagType = (status) => {
  const typeMap = {
    verified: 'success',
    pending: 'warning',
    failed: 'danger',
    in_progress: 'primary',
  }
  return typeMap[status] || 'info'
}

// 工具函数
const copyToClipboard = (text) => {
  navigator.clipboard
    .writeText(String(text))
    .then(() => ElMessage.success('复制成功'))
    .catch(() => ElMessage.error('复制失败'))
}

const formatTimeAgo = (timeStr) => {
  if (!timeStr) return '-'
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    if (diffDays < 30) return `${diffDays}天前`
    return date.toLocaleDateString('zh-CN')
  } catch {
    return timeStr
  }
}

const formatFullTime = (timeStr) => {
  if (!timeStr) return '-'
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return timeStr
  }
}

// 查看成果详情
const handleViewAchievement = (achievement) => {
  console.log('查看成果详情:', achievement)
  ElMessage.info(`查看成果: ${achievement.achievementName}`)
}

// 调试函数 - 查看数据结构
const debugDataStructure = () => {
  console.group('🔍 数据结构调试')
  console.log('表格数据:', tableData.value)
  console.log('表单数据:', formData)
  console.log('当前详情:', currentDetail.value)
  console.log('筛选参数:', filterParams)
  console.groupEnd()
}

// 初始化
onMounted(() => {
  fetchData()
  // 添加调试函数到全局，方便在控制台调用
  window.debugAttackRequest = debugDataStructure
})
</script>

<style scoped lang="scss">
.attack-request-container {
  padding: 16px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.filter-section {
  background-color: #fff;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.main-filters {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  justify-content: flex-start;
  width: 100%;
}

.keyword-input {
  width: 220px;
  margin-right: 16px;
  flex-shrink: 0;
}
.action-buttons {
  margin-left: 16px;
  flex-shrink: 0;
}

.time-filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 350px;
  flex-shrink: 0;
}

.time-field-select {
  width: 120px;
  flex-shrink: 0;
}

.advanced-filters {
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  margin-top: 12px;

  .filter-item {
    width: 100%;
    transition: all 0.3s;

    &:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
  }
}

.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.table-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-right-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  margin-top: 20px;
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  background: #fff;
}

.id-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .id-text {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .copy-icon {
    cursor: pointer;
    color: #909399;
    transition: color 0.3s;

    &:hover {
      color: #409eff;
    }
  }
}

.icon-actions {
  display: flex;
  gap: 12px;
  justify-content: left;
  align-items: center;
}

.text-ellipsis {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-muted {
  color: #909399;
}

.drawer-content {
  padding: 0;
  height: 100%;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 20px;
  border: none;

  :deep(.el-card__header) {
    border-bottom: 1px solid #f0f0f0;
    background-color: #fafafa;
    padding: 12px 20px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #303133;
}

.drawer-footer,
.review-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.detail-content {
  padding: 0;

  .detail-header {
    margin-bottom: 20px;

    h2 {
      margin: 0;
      color: #303133;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .info-card,
  .achievements-card {
    margin-bottom: 20px;
    border: none;

    :deep(.el-card__body) {
      padding: 0;
    }
  }
}

.review-content {
  padding: 20px;
}

// 响应式调整
@media (max-width: 1200px) {
  .main-filters {
    flex-wrap: wrap;
    row-gap: 12px;
  }

  .action-buttons {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .attack-request-container {
    padding: 12px;
  }

  .filter-section {
    padding: 12px;
  }

  .main-filters {
    white-space: normal;
  }

  .keyword-input {
    width: 100%;
    margin-right: 0;
    margin-bottom: 12px;
  }

  .time-filter-group {
    min-width: auto;
    width: 100%;
    flex-wrap: wrap;
  }

  .advanced-filters {
    .el-col {
      margin-bottom: 12px;
    }
  }

  .table-actions {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .table-right-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .icon-actions {
    gap: 8px;

    .action-icon {
      font-size: 14px;
    }
  }
}

// 抽屉样式优化
:deep(.el-drawer) {
  .el-drawer__header {
    margin-bottom: 20px;
    padding: 20px 20px 0;
    border-bottom: 1px solid #f0f0f0;
  }

  .el-drawer__body {
    padding: 20px;
  }
}

// 表格样式优化
:deep(.el-table) {
  th {
    background-color: #f5f7fa;
    color: #606266;
    font-weight: 600;
  }

  .el-table__row:hover {
    background-color: #f5f7fa !important;
  }
}

// 按钮组样式优化
:deep(.el-button-group) {
  .el-button {
    border-radius: 0;

    &:first-child {
      border-top-left-radius: 4px;
      border-bottom-left-radius: 4px;
    }

    &:last-child {
      border-top-right-radius: 4px;
      border-bottom-right-radius: 4px;
    }
  }
}

// 分页样式优化
:deep(.el-pagination) {
  .btn-prev,
  .btn-next,
  .number {
    background-color: transparent;
    border: 1px solid #dcdfe6;

    &:hover {
      color: #409eff;
    }

    &.active {
      background-color: #409eff;
      border-color: #409eff;
      color: #fff;
    }
  }
}

// 工具提示样式优化
:deep(.el-tooltip__popper) {
  max-width: 300px;
  word-break: break-all;
}

// 输入框聚焦效果
:deep(.el-input) {
  .el-input__inner {
    transition: all 0.3s;

    &:focus {
      border-color: #409eff;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
    }
  }
}

// 选择框样式优化
:deep(.el-select) {
  width: 100%;
}

// 卡片阴影优化
:deep(.el-card) {
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.3s;

  &:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  }
}

// 滚动条样式优化
.drawer-content::-webkit-scrollbar {
  width: 6px;
}

.drawer-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.drawer-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.drawer-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
// 文件上传相关样式
.attachment-section {
  margin-top: 20px;

  .file-preview {
    margin-top: 16px;
    padding: 12px;
    background-color: #f8f9fa;
    border-radius: 4px;

    h4 {
      margin: 0 0 8px 0;
      font-size: 14px;
      color: #606266;
    }

    .file-list {
      .file-item {
        display: flex;
        align-items: center;
        padding: 8px;
        margin-bottom: 4px;
        background: white;
        border-radius: 4px;
        transition: background-color 0.3s;

        &:hover {
          background-color: #f5f7fa;
        }

        .el-icon {
          margin-right: 8px;
          color: #409eff;
        }

        .file-name {
          flex: 1;
          font-size: 14px;
          color: #303133;
        }

        .file-size {
          font-size: 12px;
          color: #909399;
          margin-right: 8px;
        }

        .remove-icon {
          cursor: pointer;
          color: #f56c6c;

          &:hover {
            color: #c45656;
          }
        }
      }
    }
  }
}

// 上传组件样式调整
:deep(.el-upload--picture-card) {
  width: 100px;
  height: 100px;
  line-height: 100px;
  border: 1px dashed #d9d9d9;

  &:hover {
    border-color: #409eff;
  }
}

:deep(.el-upload-list--picture-card) {
  .el-upload-list__item {
    width: 100px;
    height: 100px;
  }
}
.attachment-thumbnails {
  .thumbnail-container {
    display: flex;
    gap: 4px;
    justify-content: center;
  }

  .thumbnail-item {
    position: relative;
    cursor: pointer;
    border-radius: 4px;
    overflow: hidden;

    .thumbnail-image {
      width: 32px;
      height: 32px;
      border-radius: 4px;
      border: 1px solid #f0f0f0;
    }

    .thumbnail-error {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f5f5;
      color: #999;
    }

    .more-count {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: bold;
    }
  }
}

// 详情页附件样式
.attachments-card {
  margin-bottom: 20px;
}

.attachment-detail-list {
  .attachment-detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .attachment-info {
      display: flex;
      align-items: center;
      gap: 12px;
      flex: 1;

      .file-icon {
        font-size: 24px;
        color: #409eff;
      }

      .file-details {
        display: flex;
        flex-direction: column;
        gap: 4px;

        .file-name {
          font-weight: 500;
          color: #303133;
        }

        .file-size,
        .upload-time {
          font-size: 12px;
          color: #909399;
        }
      }
    }

    .attachment-actions {
      display: flex;
      gap: 8px;
    }
  }
}

// 图片预览网格
.image-preview-section {
  margin-top: 20px;

  h4 {
    margin: 0 0 12px 0;
    color: #303133;
    font-size: 14px;
    font-weight: 600;
  }

  .image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;

    .detail-image {
      width: 100%;
      height: 100px;
      border-radius: 4px;
      border: 1px solid #f0f0f0;
      cursor: pointer;
      transition: transform 0.3s;

      &:hover {
        transform: scale(1.05);
      }
    }

    .image-error {
      width: 100%;
      height: 100px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: #f5f5f5;
      color: #999;
      gap: 4px;
    }
  }
}

// 响应式调整
@media (max-width: 768px) {
  .attachment-thumbnails .thumbnail-container {
    justify-content: flex-start;
  }

  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)) !important;
  }

  .attachment-detail-item {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 12px;
  }
}
</style>
