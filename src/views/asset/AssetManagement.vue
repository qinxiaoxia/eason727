<template>
  <div class="asset-management-container">
    <!-- 搜索区域 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="queryParams" inline>
        <el-form-item label="系统名称">
          <el-input
            v-model="queryParams.data.systemName"
            placeholder="请输入系统名称"
            clearable
            style="width: 220px"
            @input="handleSearch"
            @keyup.enter="handleImmediateSearch"
            @clear="handleReset"
          />
        </el-form-item>

        <el-form-item label="所属省">
          <el-input
            v-model="queryParams.data.province"
            placeholder="请输入所属省"
            clearable
            style="width: 220px"
            @change="handleSearch"
          />
        </el-form-item>

        <el-form-item label="所属组织">
          <el-input
            v-model="queryParams.data.organization"
            placeholder="请输入所属组织"
            clearable
            style="width: 220px"
            @change="handleSearch"
          />
        </el-form-item>

        <el-form-item label="是否靶标">
          <el-select
            v-model="queryParams.data.isTarget"
            placeholder="请选择是否靶标"
            clearable
            style="width: 220px"
            @change="handleSearch"
          >
            <el-option label="是" value="yes" />
            <el-option label="否" value="no" />
          </el-select>
        </el-form-item>

        <el-form-item>
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
            新增资源
          </el-button>
          <el-button
            :disabled="selectedRows.length === 0"
            @click="handleBatchDelete"
            class="action-btn"
          >
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
          <el-button
            :disabled="selectedRows.length === 0"
            @click="handleDispatch"
            type="warning"
            class="action-btn"
          >
            <el-icon><Share /></el-icon>
            分配资源
          </el-button>
          <el-upload
            action="/mgr/asset/import"
            :headers="uploadHeaders"
            :show-file-list="false"
            :before-upload="beforeUpload"
            :on-success="handleImportSuccess"
            :on-error="handleImportError"
          >
            <el-button type="success" class="action-btn">
              <el-icon><Upload /></el-icon>
              导入资源
            </el-button>
          </el-upload>
        </div>
        <div class="operation-stats">
          <el-tag type="info">共 {{ total }} 个资源</el-tag>
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
        class="asset-table"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="systemName" label="系统名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="assetType" label="资源类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getAssetTypeTag(row.assetType)" effect="light">
              {{ getAssetTypeText(row.assetType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ipAddress" label="IP地址" width="150" />
        <el-table-column prop="networkLevel" label="网络层级" width="120">
          <template #default="{ row }">
            <el-tag :type="getNetworkLevelTag(row.networkLevel)" effect="light">
              {{ getNetworkLevelText(row.networkLevel) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="organization" label="所属组织" width="120" show-overflow-tooltip />
        <el-table-column prop="isTarget" label="是否靶标" width="100">
          <template #default="{ row }">
            <el-tag :type="row.isTarget === 'yes' ? 'success' : 'info'" effect="light">
              {{ row.isTarget === 'yes' ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isMonitored" label="是否监控" width="100">
          <template #default="{ row }">
            <el-tag :type="row.isMonitored === 'yes' ? 'success' : 'info'" effect="light">
              {{ row.isMonitored === 'yes' ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="teamName" label="分配队伍" width="150">
          <template #default="{ row }">
            <el-tooltip
              :content="getTeamAllocationTooltip(row)"
              placement="top"
              :disabled="!row.teamId"
            >
              <span :class="{ 'allocated-team': row.teamId }">
                {{ getTeamDisplayName(row) }}
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="province" label="省份" width="120" />
        <el-table-column prop="city" label="城市" width="120" />

        <el-table-column label="操作" width="110" fixed="right" align="left">
          <template #default="{ row }">
            <div class="icon-actions">
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
                <el-icon class="action-icon" @click="handleDelete(row.id)">
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
      size="800px"
      class="asset-drawer wide-drawer"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="系统名称" prop="systemName">
              <el-input
                v-model="formData.systemName"
                placeholder="请输入系统名称"
                maxlength="100"
                show-word-limit
                class="custom-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="资源类型" prop="assetType">
              <el-select
                v-model="formData.assetType"
                placeholder="请选择资源类型"
                class="custom-input"
              >
                <el-option label="服务器" value="server" />
                <el-option label="网络设备" value="network" />
                <el-option label="安全设备" value="security" />
                <el-option label="应用系统" value="application" />
                <el-option label="数据库" value="database" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="IP地址" prop="ipAddress">
              <el-input
                v-model="formData.ipAddress"
                placeholder="请输入IP地址"
                maxlength="50"
                class="custom-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="域名" prop="domainName">
              <el-input
                v-model="formData.domainName"
                placeholder="请输入域名"
                maxlength="100"
                class="custom-input"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="网络层级" prop="networkLevel">
              <el-select
                v-model="formData.networkLevel"
                placeholder="请选择网络层级"
                class="custom-input"
              >
                <el-option label="互联网区" value="internet" />
                <el-option label="DMZ区" value="dmz" />
                <el-option label="核心区" value="core" />
                <el-option label="办公区" value="office" />
                <el-option label="测试区" value="test" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属组织" prop="organization">
              <el-input
                v-model="formData.organization"
                placeholder="请输入所属组织"
                maxlength="100"
                class="custom-input"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="是否靶标" prop="isTarget">
              <el-select v-model="formData.isTarget" class="custom-input">
                <el-option label="是" value="yes" />
                <el-option label="否" value="no" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="是否监控" prop="isMonitored">
              <el-select v-model="formData.isMonitored" class="custom-input">
                <el-option label="是" value="yes" />
                <el-option label="否" value="no" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="省份" prop="province">
              <el-input
                v-model="formData.province"
                placeholder="请输入省份"
                maxlength="20"
                class="custom-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="城市" prop="city">
              <el-input
                v-model="formData.city"
                placeholder="请输入城市"
                maxlength="20"
                class="custom-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="端口" prop="ports">
              <el-input
                v-model="formData.ports"
                placeholder="如: 80,443,22"
                maxlength="200"
                class="custom-input"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="内部IP范围" prop="internalIpRange">
          <el-input
            v-model="formData.internalIpRange"
            type="textarea"
            rows="2"
            placeholder="请输入内部IP范围，多个用逗号分隔"
            maxlength="500"
            show-word-limit
            resize="none"
          />
        </el-form-item>

        <el-form-item label="URL地址" prop="url">
          <el-input
            v-model="formData.url"
            placeholder="请输入URL地址"
            maxlength="500"
            class="custom-input"
          />
        </el-form-item>

        <!-- 修改：将项目ID改为下拉框 -->
        <el-form-item label="项目" prop="projectId">
          <el-select
            v-model="formData.projectId"
            placeholder="请选择项目"
            filterable
            clearable
            style="width: 100%"
            @change="handleProjectSelectChange"
          >
            <el-option
              v-for="project in projectOptions"
              :key="project.id"
              :label="project.projectName"
              :value="project.id"
            />
          </el-select>
        </el-form-item>

        <!-- 修改：将队伍ID改为下拉框 -->
        <el-form-item label="队伍" prop="teamId">
          <el-select
            v-model="formData.teamId"
            placeholder="请选择队伍"
            filterable
            clearable
            style="width: 100%"
            @change="handleTeamSelectChange"
          >
            <el-option
              v-for="team in teamOptions"
              :key="team.id"
              :label="team.teamName"
              :value="team.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <div class="footer-left">
            <el-tag v-if="drawerMode === 'edit'" type="info" size="large">
              资源ID: {{ formData.id }}
            </el-tag>
          </div>
          <div class="footer-right">
            <el-button @click="drawerVisible = false" class="cancel-btn">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving" class="save-btn">
              <el-icon><Check /></el-icon>
              保存
            </el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="资源详情"
      direction="rtl"
      size="1000px"
      class="detail-drawer"
    >
      <el-descriptions :column="2" border v-if="currentAssetDetail">
        <el-descriptions-item label="资源ID">{{
          currentAssetDetail.id || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="系统名称">{{
          currentAssetDetail.systemName || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="资源类型">
          <el-tag :type="getAssetTypeTag(currentAssetDetail.assetType)" effect="light">
            {{ getAssetTypeText(currentAssetDetail.assetType) || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="IP地址">{{
          currentAssetDetail.ipAddress || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="域名">{{
          currentAssetDetail.domainName || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="网络层级">
          <el-tag :type="getNetworkLevelTag(currentAssetDetail.networkLevel)" effect="light">
            {{ getNetworkLevelText(currentAssetDetail.networkLevel) || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="所属组织">{{
          currentAssetDetail.organization || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="是否靶标">
          <el-tag :type="currentAssetDetail.isTarget === 'yes' ? 'success' : 'info'" effect="light">
            {{ currentAssetDetail.isTarget === 'yes' ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="是否监控">
          <el-tag
            :type="currentAssetDetail.isMonitored === 'yes' ? 'success' : 'info'"
            effect="light"
          >
            {{ currentAssetDetail.isMonitored === 'yes' ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="省份">{{
          currentAssetDetail.province || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="城市">{{
          currentAssetDetail.city || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="端口">{{
          currentAssetDetail.ports || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="内部IP范围" :span="2">
          {{ currentAssetDetail.internalIpRange || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="URL地址" :span="2">
          {{ currentAssetDetail.url || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="分配队伍">
          <el-tag v-if="currentAssetDetail.teamId" type="success">
            {{ getTeamNameById(currentAssetDetail.teamId) }}
          </el-tag>
          <span v-else>-</span>
        </el-descriptions-item>

        <el-descriptions-item label="分配项目">
          <el-tag v-if="currentAssetDetail.projectId" type="primary">
            {{ getProjectNameById(currentAssetDetail.projectId) }}
          </el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="detailDrawerVisible = false">关闭</el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 分配弹窗 -->
    <el-dialog
      v-model="dispatchDialogVisible"
      :title="dispatchTitle"
      width="600px"
      class="dispatch-dialog"
      :close-on-click-modal="false"
    >
      <el-form :model="dispatchForm" label-width="100px">
        <el-form-item label="选择项目" required>
          <el-select
            v-model="dispatchForm.projectId"
            placeholder="请选择项目"
            filterable
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.projectName"
              :value="project.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="选择队伍" required>
          <el-select
            v-model="dispatchForm.teamId"
            placeholder="请选择攻击队伍"
            filterable
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="team in attackTeams"
              :key="team.id"
              :label="team.teamName"
              :value="team.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="已选资源">
          <el-tag
            v-for="asset in selectedRows"
            :key="asset.id"
            closable
            @close="removeSelectedAsset(asset.id)"
            style="margin: 4px"
          >
            {{ asset.systemName }} ({{ asset.ipAddress }})
          </el-tag>
          <div v-if="selectedRows.length === 0" class="no-selection">未选择任何资源</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dispatchDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleDispatchConfirm" :loading="dispatching">
            确定分配
          </el-button>
        </span>
      </template>
    </el-dialog>
    <el-dialog
      v-model="allocationDialogVisible"
      :title="allocationTitle"
      width="500px"
      class="allocation-dialog"
      :close-on-click-modal="false"
    >
      <el-form :model="allocationForm" label-width="80px">
        <el-form-item label="当前分配">
          <el-tag v-if="currentAllocationAsset.teamName" type="success">
            {{ currentAllocationAsset.teamName }}
          </el-tag>
          <el-tag v-else type="info">未分配</el-tag>
        </el-form-item>

        <el-form-item label="选择项目">
          <el-select
            v-model="allocationForm.projectId"
            placeholder="请选择项目"
            filterable
            clearable
            style="width: 100%"
            @change="handleAllocationProjectChange"
          >
            <el-option
              v-for="project in projectOptions"
              :key="project.id"
              :label="project.projectName"
              :value="project.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="选择队伍">
          <el-select
            v-model="allocationForm.teamId"
            placeholder="请选择队伍"
            filterable
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="team in allocationTeamOptions"
              :key="team.id"
              :label="team.teamName"
              :value="team.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button
            v-if="currentAllocationAsset.teamName"
            type="danger"
            @click="handleCancelAllocation"
            :loading="allocating"
          >
            取消分配
          </el-button>
          <el-button @click="allocationDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleAllocationConfirm" :loading="allocating">
            {{ allocationForm.teamId ? '确认分配' : '取消分配' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, Delete, View, Edit, Check, Upload, Share } from '@element-plus/icons-vue'

// 正确导入API
import assetApi from '@/api/services/asset/asset'
import attackAssetApi from '@/api/services/asset/attackAsset'
import teamApi from '@/api/services/team/team'
import { projectApi } from '@/api/services/project/project'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const dispatching = ref(false)
const tableData = ref([])
const total = ref(0)
const drawerVisible = ref(false)
const dispatchDialogVisible = ref(false)
const drawerTitle = ref('')
const dispatchTitle = ref('')
const drawerMode = ref('add')
const selectedRows = ref([])
const detailDrawerVisible = ref(false)
const currentAssetDetail = ref(null)
const formRef = ref()
const allocationDialogVisible = ref(false)
const allocating = ref(false)
const currentAllocationAsset = ref({})
const allocationTitle = ref('')

// 队伍和项目数据
const attackTeams = ref([])
const projects = ref([])
const allTeams = ref([]) // 新增：所有队伍数据
const allProjects = ref([]) // 新增：所有项目数据

// 表单数据
const formData = reactive({
  id: '',
  systemName: '',
  assetType: '',
  ipAddress: '',
  domainName: '',
  networkLevel: '',
  organization: '',
  isTarget: 'no',
  isMonitored: 'no',
  province: '',
  city: '',
  ports: '',
  internalIpRange: '',
  url: '',
  projectId: '',
  teamId: '',
  projectName: '', // 新增：项目名称
  teamName: '', // 新增：队伍名称
})

// 表单验证规则
const rules = {
  systemName: [
    { required: true, message: '系统名称不能为空', trigger: 'blur' },
    { min: 2, max: 100, message: '系统名称长度在2到100个字符', trigger: 'blur' },
  ],
  assetType: [{ required: true, message: '请选择资源类型', trigger: 'change' }],
  ipAddress: [{ required: true, message: 'IP地址不能为空', trigger: 'blur' }],
}

// 分配表单数据
const dispatchForm = reactive({
  projectId: '',
  teamId: '',
  assetIds: [],
})
// 分配表单数据
const allocationForm = reactive({
  assetId: '',
  projectId: '',
  teamId: '',
})
const allocationTeamOptions = computed(() => {
  if (!allocationForm.projectId) {
    return teamOptions.value
  }
  return teamOptions.value.filter((team) => team.projectId === allocationForm.projectId)
})

// 项目选择变化处理
const handleAllocationProjectChange = () => {
  allocationForm.teamId = '' // 清空队伍选择
}

// 确认分配/取消分配
const handleAllocationConfirm = async () => {
  if (!allocationForm.assetId) {
    ElMessage.error('未选择资源')
    return
  }

  try {
    allocating.value = true

    // 准备提交数据
    const submitData = {
      id: allocationForm.assetId,
      projectId: allocationForm.projectId ? Number(allocationForm.projectId) : null,
      teamId: allocationForm.teamId ? Number(allocationForm.teamId) : null,
      projectName: allocationForm.projectId ? getProjectName(allocationForm.projectId) : '',
      teamName: allocationForm.teamId ? getTeamName(allocationForm.teamId) : '',
    }

    // 调用修改接口
    const response = await assetApi.modify(submitData)

    if (response && response.code === 200) {
      ElMessage.success(allocationForm.teamId ? '分配成功' : '取消分配成功')
      allocationDialogVisible.value = false
      getPageList() // 刷新列表
    } else {
      ElMessage.error(response?.message || '操作失败')
    }
  } catch (error) {
    console.error('分配操作失败:', error)
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  } finally {
    allocating.value = false
  }
}

// 取消分配确认
const handleCancelAllocation = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要取消"${currentAllocationAsset.value.systemName}"的分配吗？`,
      '取消分配确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      },
    )

    // 执行取消分配
    allocationForm.teamId = ''
    allocationForm.projectId = ''
    await handleAllocationConfirm()
  } catch {
    // 用户点击取消
    console.log('用户取消操作')
  }
}
// 查询参数（修改：只保留四个搜索条件）
const queryParams = reactive({
  page: 1,
  limit: 20,
  data: {
    systemName: '',
    province: '',
    organization: '',
    isTarget: '',
  },
  hasTimeRange: 0,
  timeField: 'createTime',
})

// 计算属性：获取项目和队伍的下拉选项
const projectOptions = computed(() => {
  return allProjects.value.map((project) => ({
    id: project.id,
    projectName: project.projectName || `项目${project.id}`,
  }))
})

const teamOptions = computed(() => {
  return allTeams.value.map((team) => ({
    id: team.id,
    teamName: team.teamName || `队伍${team.id}`,
  }))
})

// 上传headers
const uploadHeaders = reactive({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
})

// 资源类型标签映射
const getAssetTypeTag = (type) => {
  const typeMap = {
    server: 'primary',
    network: 'success',
    security: 'warning',
    application: 'info',
    database: 'danger',
  }
  return typeMap[type] || 'info'
}

const getAssetTypeText = (type) => {
  const textMap = {
    server: '服务器',
    network: '网络设备',
    security: '安全设备',
    application: '应用系统',
    database: '数据库',
  }
  return textMap[type] || type
}

// 网络层级标签映射
const getNetworkLevelTag = (level) => {
  const levelMap = {
    internet: 'danger',
    dmz: 'warning',
    core: 'success',
    office: 'primary',
    test: 'info',
  }
  return levelMap[level] || 'info'
}

const getNetworkLevelText = (level) => {
  const textMap = {
    internet: '互联网区',
    dmz: 'DMZ区',
    core: '核心区',
    office: '办公区',
    test: '测试区',
  }
  return textMap[level] || level
}

// 根据ID获取项目名称
const getProjectName = (projectId) => {
  const project = allProjects.value.find((p) => p.id === projectId)
  return project ? project.projectName : projectId
}

// 根据ID获取队伍名称
const getTeamName = (teamId) => {
  const team = allTeams.value.find((t) => t.id === teamId)
  return team ? team.teamName : teamId
}

// 获取所有项目和队伍数据
const loadAllProjectsAndTeams = async () => {
  try {
    // 加载所有项目
    const projectParams = {
      page: 1,
      limit: 1000,
      data: {},
    }

    const projectResult = await projectApi.getPageList(projectParams)
    if (projectResult && projectResult.code === 200) {
      allProjects.value = projectResult.data || []
    }

    // 加载所有队伍（不仅仅是攻击队伍）
    const teamParams = {
      page: 1,
      limit: 1000,
      data: {},
    }

    const teamResult = await teamApi.getPageList(teamParams)
    if (teamResult && teamResult.code === 200) {
      allTeams.value = teamResult.data || []
    }

    console.log('加载所有项目和队伍数据成功:', {
      allProjects: allProjects.value.length,
      allTeams: allTeams.value.length,
    })
  } catch (error) {
    console.error('加载所有项目和队伍数据失败:', error)
  }
}

// 获取资源列表
const getPageList = async () => {
  loading.value = true
  try {
    const response = await assetApi.getPageList(queryParams)
    console.log('资源列表接口返回数据:', response)
    if (response && response.code === 200) {
      // 处理数据，将teamId转换为队伍名称
      tableData.value = (response.data || []).map((item) => ({
        ...item,
        // 将teamId转换为队伍名称
        teamDisplayName: getTeamNameById(item.teamId),
      }))
      total.value = response.count || 0
    } else {
      tableData.value = []
      total.value = 0
      ElMessage.error(response?.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取资源列表失败:', error)
    ElMessage.error('获取数据失败')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}
const getTeamNameById = (teamId) => {
  if (!teamId) return '未分配'

  const team = allTeams.value.find((t) => t.id === teamId)
  return team ? team.teamName : `队伍${teamId}`
}
// 新增方法：获取队伍显示名称
const getTeamDisplayName = (row) => {
  return getTeamNameById(row.teamId)
}

// 新增方法：获取队伍分配提示信息
const getTeamAllocationTooltip = (row) => {
  if (!row.teamId) return ''

  const teamName = getTeamNameById(row.teamId)
  const projectName = row.projectName || getProjectNameById(row.projectId) || '未知项目'

  return `项目: ${projectName}\n队伍: ${teamName}`
}

// 新增方法：根据projectId获取项目名称
const getProjectNameById = (projectId) => {
  if (!projectId) return ''

  const project = allProjects.value.find((p) => p.id === projectId)
  return project ? project.projectName : `项目${projectId}`
}
// 加载队伍和项目数据
const loadTeamsAndProjects = async () => {
  try {
    // 加载攻击队伍（用于分配功能）
    const teamParams = {
      page: 1,
      limit: 1000,
      data: {
        teamType: 'attack',
      },
    }

    const teamResult = await teamApi.getPageList(teamParams)
    if (teamResult && teamResult.code === 200) {
      attackTeams.value = teamResult.data || []
    }

    // 加载项目（用于分配功能）
    const projectParams = {
      page: 1,
      limit: 1000,
      data: {},
    }

    const projectResult = await projectApi.getPageList(projectParams)
    if (projectResult && projectResult.code === 200) {
      projects.value = projectResult.data || []
    }
  } catch (error) {
    console.error('加载队伍和项目数据失败:', error)
    attackTeams.value = []
    projects.value = []
  }
}

// 项目选择变化处理
const handleProjectSelectChange = (projectId) => {
  const project = allProjects.value.find((p) => p.id === projectId)
  if (project) {
    formData.projectName = project.projectName
  } else {
    formData.projectName = ''
  }
}

// 队伍选择变化处理
const handleTeamSelectChange = (teamId) => {
  const team = allTeams.value.find((t) => t.id === teamId)
  if (team) {
    formData.teamName = team.teamName
  } else {
    formData.teamName = ''
  }
}

// 新增资源
const handleAdd = () => {
  drawerMode.value = 'add'
  drawerTitle.value = '新增资源'
  Object.keys(formData).forEach((key) => {
    if (key === 'isTarget' || key === 'isMonitored') {
      formData[key] = 'no'
    } else {
      formData[key] = ''
    }
  })
  drawerVisible.value = true
}

// 编辑资源
const handleEdit = async (row) => {
  drawerMode.value = 'edit'
  drawerTitle.value = '编辑资源'
  Object.keys(formData).forEach((key) => {
    if (row[key] !== undefined && row[key] !== null) {
      formData[key] = row[key]
    } else {
      if (key === 'isTarget' || key === 'isMonitored') {
        formData[key] = 'no'
      } else {
        formData[key] = ''
      }
    }
  })
  drawerVisible.value = true
}

// 查看详情
const handleViewDetail = (row) => {
  currentAssetDetail.value = { ...row }
  detailDrawerVisible.value = true
}

// 保存资源
const handleSave = async () => {
  try {
    if (!formRef.value) {
      ElMessage.error('表单引用未找到')
      return
    }

    // 表单验证
    await formRef.value.validate()
    saving.value = true

    // 准备提交数据
    const submitData = { ...formData }

    // 确保ID为数字
    if (submitData.projectId) {
      submitData.projectId = Number(submitData.projectId)
    }
    if (submitData.teamId) {
      submitData.teamId = Number(submitData.teamId)
    }

    let response

    if (drawerMode.value === 'edit') {
      response = await assetApi.modify(submitData)
    } else {
      response = await assetApi.add(submitData)
    }

    if (response && response.code === 200) {
      ElMessage.success(drawerMode.value === 'add' ? '新增成功' : '编辑成功')
      drawerVisible.value = false
      getPageList()
    } else {
      ElMessage.error(response?.message || '操作失败')
    }
  } catch (error) {
    console.error('保存资源失败:', error)
    if (error.errors) {
      ElMessage.error('请检查表单填写是否正确')
    } else {
      ElMessage.error('保存失败: ' + (error.message || '未知错误'))
    }
  } finally {
    saving.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  queryParams.page = 1
  getPageList()
}

const handleImmediateSearch = () => {
  queryParams.page = 1
  getPageList()
}

const handleReset = () => {
  Object.assign(queryParams, {
    page: 1,
    limit: 20,
    data: {
      systemName: '',
      province: '',
      organization: '',
      isTarget: '',
    },
    hasTimeRange: 0,
  })
  getPageList()
}

const handleRefresh = () => {
  getPageList()
  ElMessage.success('数据已刷新')
}

// 分配处理函数
const handleDispatch = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要分配的资源')
    return
  }

  dispatchTitle.value = `分配资源 (${selectedRows.value.length}个)`
  dispatchForm.projectId = ''
  dispatchForm.teamId = ''
  dispatchForm.assetIds = selectedRows.value.map((asset) => asset.id)
  dispatchDialogVisible.value = true
}

// 移除已选资源
const removeSelectedAsset = (assetId) => {
  const index = selectedRows.value.findIndex((asset) => asset.id === assetId)
  if (index > -1) {
    selectedRows.value.splice(index, 1)
    const assetIndex = dispatchForm.assetIds.indexOf(assetId)
    if (assetIndex > -1) {
      dispatchForm.assetIds.splice(assetIndex, 1)
    }
  }
}

// 确认分配
const handleDispatchConfirm = async () => {
  try {
    if (!dispatchForm.projectId) {
      ElMessage.warning('请选择项目')
      return
    }

    if (!dispatchForm.teamId) {
      ElMessage.warning('请选择攻击队伍')
      return
    }

    if (dispatchForm.assetIds.length === 0) {
      ElMessage.warning('请选择要分配的资源')
      return
    }

    dispatching.value = true

    // 批量分配资源
    const dispatchPromises = dispatchForm.assetIds.map((assetId) => {
      const dispatchData = {
        assetId: assetId,
        projectId: dispatchForm.projectId,
        teamId: dispatchForm.teamId,
      }
      return attackAssetApi.add(dispatchData)
    })

    const results = await Promise.all(dispatchPromises)
    const successCount = results.filter((result) => result && result.code === 200).length

    if (successCount === dispatchForm.assetIds.length) {
      ElMessage.success(`成功分配 ${successCount} 个资源`)
      dispatchDialogVisible.value = false
      selectedRows.value = []
    } else {
      ElMessage.warning(
        `成功分配 ${successCount} 个资源，${dispatchForm.assetIds.length - successCount} 个分配失败`,
      )
    }
  } catch (error) {
    console.error('分配失败:', error)
    ElMessage.error('分配失败: ' + (error.message || '未知错误'))
  } finally {
    dispatching.value = false
  }
}

// 表格选择变化
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 分页处理
const handleSizeChange = (newSize) => {
  queryParams.limit = newSize
  queryParams.page = 1
  getPageList()
}

const handleCurrentChange = (newPage) => {
  queryParams.page = newPage
  getPageList()
}

// 文件上传处理
const beforeUpload = (file) => {
  const isExcel =
    file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
    file.type === 'application/vnd.ms-excel'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isExcel) {
    ElMessage.error('只能上传 Excel 文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return true
}

const handleImportSuccess = (response) => {
  if (response && response.code === 200) {
    ElMessage.success('导入成功')
    getPageList()
  } else {
    ElMessage.error(response?.message || '导入失败')
  }
}

const handleImportError = (error) => {
  console.error('导入失败:', error)
  ElMessage.error('导入失败: ' + (error.message || '未知错误'))
}

// 删除资源（保持原有逻辑）

// 初始化
onMounted(() => {
  getPageList()
  loadTeamsAndProjects()
  loadAllProjectsAndTeams() // 新增：加载所有项目和队伍数据
})
</script>

<style scoped lang="scss">
.asset-management-container {
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

.table-card {
  border-radius: 8px;
  border: 1px solid #e4e7ed;

  :deep(.el-card__body) {
    padding: 0;
  }
}

.asset-table {
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

.icon-actions {
  display: flex;
  gap: 12px;
  justify-content: left;
  align-items: center;
}

.pagination-container {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  background: #fff;
}

.asset-drawer {
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

.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;

  .cancel-btn {
    border-radius: 8px;
    padding: 10px 24px;
    border: 1px solid #d1d5db;
    color: #6b7280;
    background-color: #ffffff;
    transition: all 0.3s ease;
    font-weight: 500;

    &:hover {
      border-color: #3b82f6;
      color: #3b82f6;
      background-color: #f0f9ff;
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
    }

    &:active {
      transform: translateY(0);
    }
  }

  .save-btn {
    border-radius: 8px;
    padding: 10px 24px;
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    border: none;
    color: #ffffff;
    font-weight: 500;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
      background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
    }

    &:active {
      transform: translateY(0);
    }

    &:disabled {
      background: #9ca3af;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;

      &:hover {
        background: #9ca3af;
        transform: none;
        box-shadow: none;
      }
    }
  }
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;

  .el-tag {
    border-radius: 16px;
    font-weight: 500;
    padding: 4px 12px;

    &.el-tag--info {
      background: #f0f9ff;
      border-color: #e0f2fe;
      color: #0369a1;
    }
  }
}

// 响应式适配
@media (max-width: 768px) {
  .asset-management-container {
    padding: 16px;
  }

  .operation-container {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .asset-drawer,
  .detail-drawer {
    :deep(.el-drawer) {
      width: 95% !important;

      .el-drawer__header {
        padding: 16px 20px;
      }

      .el-drawer__body {
        padding: 16px 20px;
      }
    }
  }
}

@media (max-width: 480px) {
  .asset-management-container {
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

  .icon-actions {
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px;

    .action-icon {
      width: 24px;
      height: 24px;
    }
  }
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
/* 分配弹窗样式 */
.dispatch-dialog {
  :deep(.el-dialog__body) {
    padding: 20px;
  }

  .no-selection {
    color: #909399;
    font-style: italic;
    padding: 8px 0;
  }
}

/* 已选资源标签样式 */
:deep(.el-tag) {
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
}

/* 分配按钮样式 */
.operation-left .action-btn[type='warning'] {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border: none;
  color: white;

  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(245, 158, 11, 0.3);
  }
}
.asset-management-container {
  background-color: #f5f7fa;
  min-height: calc(100vh - 84px);
  padding: 20px;
}
.resource-allocation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background-color: #f5f7fa;
  }

  .allocation-text {
    color: #909399;
    font-size: 14px;

    &.has-allocation {
      color: #409eff;
      font-weight: 500;
    }
  }

  .edit-icon {
    color: #c0c4cc;
    font-size: 14px;
    padding: 4px;
    border-radius: 3px;
    transition: all 0.3s ease;

    &:hover {
      color: #409eff;
      background-color: #ecf5ff;
    }
  }
}

// 分配弹窗样式
.allocation-dialog {
  :deep(.el-dialog__body) {
    padding: 20px;
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 12px;
  }
}

// 表格行样式优化
.asset-table {
  :deep(.el-table__body) {
    .resource-allocation-cell {
      padding: 4px 8px;
    }
  }
}

// 响应式适配
@media (max-width: 768px) {
  .resource-allocation {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;

    .edit-icon {
      align-self: flex-end;
    }
  }
}
</style>
