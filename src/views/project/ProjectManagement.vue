<template>
  <div class="project-management-container">
    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="main-filters">
        <!-- 关键词搜索 -->
        <el-input
          v-model="filterParams.projectName"
          placeholder="搜索项目名称"
          clearable
          @input="handleSearch"
          @clear="handleSearch"
          class="keyword-input"
        />

        <!-- 时间筛选 -->
        <div class="time-filter-group">
          <el-select
            v-model="selectedTimeField"
            placeholder="创建时间"
            class="time-field-select"
            style="width: 120px"
            @change="handleTimeFieldChange"
          >
            <el-option label="创建时间" value="createTime" />
            <el-option label="开始时间" value="startDate" />
            <el-option label="结束时间" value="endDate" />
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

        <!-- 状态筛选 -->
        <el-select
          v-model="filterParams.status"
          placeholder="项目状态"
          clearable
          @change="handleSearch"
          @clear="handleSearch"
          style="width: 120px"
        >
          <el-option
            v-for="option in statusOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>

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
                v-model="filterParams.organization"
                placeholder="所属组织"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.industry"
                placeholder="所属行业"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.location"
                placeholder="项目地点"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                class="filter-item"
              />
            </el-col>
            <el-col :xs="12" :sm="8" :md="6" :lg="4">
              <el-input
                v-model="filterParams.leaderName"
                placeholder="负责人"
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
          <el-button type="primary" @click="handleAddProject">
            <el-icon><Plus /></el-icon>新增项目
          </el-button>
          <el-button @click="handleImport" plain>
            <el-icon><Upload /></el-icon>导入项目
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
        key="project-table"
        :row-key="(row) => row.id"
        @expand-change="handleExpandChange"
      >
        <el-table-column type="expand" width="30">
          <template #default="{ row }">
            <div
              class="material-expand-panel"
              v-if="row.expandMaterials && row.expandMaterials.length > 0"
            >
              <div class="expand-header">
                <h4>项目材料列表 ({{ row.expandMaterials.length }})</h4>
                <el-button
                  type="primary"
                  size="small"
                  @click="handleAddMaterial(row)"
                  class="expand-add-btn"
                >
                  <el-icon><Plus /></el-icon>添加材料
                </el-button>
              </div>

              <el-table
                :data="row.expandMaterials"
                size="small"
                border
                class="material-sub-table"
                style="width: 100%"
              >
                <!-- 材料名称 -->
                <el-table-column
                  prop="materialName"
                  label="材料名称"
                  width="380"
                  show-overflow-tooltip
                >
                  <template #default="{ row: material }">
                    <div class="material-name-cell">
                      <el-tooltip :content="material.materialName" placement="top">
                        <span class="material-name-text">{{ material.materialName }}</span>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>

                <!-- 材料分类 -->
                <el-table-column prop="category" label="分类" width="160" align="center">
                  <template #default="{ row: material }">
                    <el-tag
                      :type="getMaterialCategoryType(material.category)"
                      size="small"
                      effect="plain"
                    >
                      {{ getMaterialCategoryText(material.category).slice(0, 2) }}
                    </el-tag>
                  </template>
                </el-table-column>

                <!-- 附件类型 -->
                <el-table-column prop="attachmentType" label="类型" width="160" align="center">
                  <template #default="{ row: material }">
                    <el-tag
                      v-if="material.attachmentType"
                      :type="getAttachmentTypeTagType(material.attachmentType)"
                      size="small"
                    >
                      {{ getAttachmentTypeText(material.attachmentType) }}
                    </el-tag>
                    <span v-else>-</span>
                  </template>
                </el-table-column>

                <!-- 文件大小 -->
                <el-table-column prop="attachmentSize" label="大小" width="160" align="center">
                  <template #default="{ row: material }">
                    <span class="file-size">{{ formatFileSize(material.attachmentSize) }}</span>
                  </template>
                </el-table-column>

                <!-- 操作列 - 固定在右侧 -->
                <el-table-column label="操作" min-width="160" fixed="right" align="left">
                  <template #default="{ row: material }">
                    <div class="icon-actions">
                      <!-- 下载 -->
                      <el-tooltip content="下载" placement="top">
                        <el-icon
                          class="action-icon download-icon"
                          @click="handleDownloadMaterial(material)"
                        >
                          <Download />
                        </el-icon>
                      </el-tooltip>

                      <!-- 删除 -->
                      <el-tooltip content="删除" placement="top">
                        <el-icon
                          class="action-icon delete-icon"
                          @click="handleDeleteMaterial(material, row)"
                        >
                          <Delete />
                        </el-icon>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div v-else class="no-material-panel">
              <el-empty description="暂无材料" :image-size="80">
                <el-button type="primary" @click="handleAddMaterial(row)">添加材料</el-button>
              </el-empty>
            </div>
          </template>
        </el-table-column>
        <!-- 选择列 -->
        <el-table-column type="selection" width="50" align="center" />

        <!-- 项目ID -->
        <el-table-column prop="id" label="项目ID" min-width="80"> </el-table-column>

        <!-- 项目名称 -->
        <el-table-column prop="projectName" label="项目名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="id-cell">
              <el-tooltip :content="String(row.projectName)" placement="top">
                <span class="id-text">{{ row.projectName }}</span>
              </el-tooltip>
              <el-icon class="copy-icon" @click="copyToClipboard(row.projectName)">
                <DocumentCopy />
              </el-icon>
            </div>
          </template>
        </el-table-column>

        <!-- 所属组织 -->
        <el-table-column prop="organization" label="所属组织" width="150" show-overflow-tooltip />

        <!-- 所属行业 -->
        <el-table-column prop="industry" label="所属行业" width="120" show-overflow-tooltip />

        <!-- 项目地点 -->
        <el-table-column prop="location" label="项目地点" width="120" show-overflow-tooltip />

        <!-- 负责人 -->
        <el-table-column prop="leaderName" label="负责人" width="120" align="center" />

        <!-- 开始时间 -->
        <el-table-column prop="startDate" label="开始时间" width="120" align="center" sortable>
          <template #default="{ row }">
            <span>{{ formatDate(row.startDate) }}</span>
          </template>
        </el-table-column>

        <!-- 结束时间 -->
        <el-table-column prop="endDate" label="结束时间" width="120" align="center" sortable>
          <template #default="{ row }">
            <span>{{ formatDate(row.endDate) }}</span>
          </template>
        </el-table-column>

        <!-- 参与人数统计 -->
        <el-table-column label="参与人数" width="200" align="center">
          <template #default="{ row }">
            <div class="participant-stats">
              <span class="stat-item">攻: {{ row.attackerCount || 0 }}</span>
              <span class="stat-item">防: {{ row.defenderCount || 0 }}</span>
              <span class="stat-item">裁: {{ row.refereeCount || 0 }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 目标系统数 -->
        <el-table-column prop="targetSystemCount" label="目标系统" width="100" align="center" />
        <!-- 状态列 -->
        <el-table-column prop="status" label="状态" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="light">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="icon-actions">
              <!-- 查看详情 -->
              <el-tooltip content="查看详情" placement="top">
                <el-icon class="action-icon view-icon" @click="handleViewDetail(row)">
                  <View />
                </el-icon>
              </el-tooltip>
              <el-tooltip content="添加材料" placement="top">
                <el-icon class="action-icon add-icon" @click="handleAddMaterial(row)">
                  <Plus />
                </el-icon>
              </el-tooltip>
              <!-- 编辑 -->
              <el-tooltip content="编辑" placement="top">
                <el-icon class="action-icon edit-icon" @click="handleEditProject(row)">
                  <Edit />
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
      class="project-drawer"
      :close-on-click-modal="true"
    >
      <div class="drawer-content" v-if="drawerVisible">
        <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
          <!-- 基础信息 -->
          <el-card shadow="never" class="form-section">
            <template #header>
              <div class="card-header">
                <span>基础信息</span>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="项目名称" prop="projectName">
                  <el-input v-model="formData.projectName" placeholder="请输入项目名称" clearable />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="所属组织" prop="organization">
                  <el-input
                    v-model="formData.organization"
                    placeholder="请输入所属组织"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="所属行业" prop="industry">
                  <el-input v-model="formData.industry" placeholder="请输入所属行业" clearable />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="项目地点" prop="location">
                  <el-input v-model="formData.location" placeholder="请输入项目地点" clearable />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="开始时间" prop="startDate">
                  <el-date-picker
                    v-model="formData.startDate"
                    type="datetime"
                    placeholder="选择开始时间"
                    value-format="YYYY-MM-DD HH:mm:ss"
                    format="YYYY-MM-DD HH:mm:ss"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="结束时间" prop="endDate">
                  <el-date-picker
                    v-model="formData.endDate"
                    type="datetime"
                    placeholder="选择结束时间"
                    value-format="YYYY-MM-DD HH:mm:ss"
                    format="YYYY-MM-DD HH:mm:ss"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="每日开始时间" prop="dailyStartTime">
                  <el-time-picker
                    v-model="formData.dailyStartTime"
                    placeholder="选择每日开始时间"
                    value-format="HH:mm:ss"
                    format="HH:mm:ss"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="每日结束时间" prop="dailyEndTime">
                  <el-time-picker
                    v-model="formData.dailyEndTime"
                    placeholder="选择每日结束时间"
                    value-format="HH:mm:ss"
                    format="HH:mm:ss"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-card>

          <!-- 负责人信息 -->
          <el-card shadow="never" class="form-section">
            <template #header>
              <div class="card-header">
                <span>负责人信息</span>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="负责人姓名" prop="leaderName">
                  <el-input
                    v-model="formData.leaderName"
                    placeholder="请输入负责人姓名"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="负责人组织" prop="leaderOrganization">
                  <el-input
                    v-model="formData.leaderOrganization"
                    placeholder="请输入负责人组织"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="负责人部门" prop="leaderDepartment">
                  <el-input
                    v-model="formData.leaderDepartment"
                    placeholder="请输入负责人部门"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="负责人职位" prop="leaderPosition">
                  <el-input
                    v-model="formData.leaderPosition"
                    placeholder="请输入负责人职位"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-card>

          <!-- 联系人信息 -->
          <el-card shadow="never" class="form-section">
            <template #header>
              <div class="card-header">
                <span>联系人信息</span>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="联系人姓名" prop="contactName">
                  <el-input
                    v-model="formData.contactName"
                    placeholder="请输入联系人姓名"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="联系人电话" prop="contactPhone">
                  <el-input
                    v-model="formData.contactPhone"
                    placeholder="请输入联系人电话"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="联系人组织" prop="contactOrganization">
                  <el-input
                    v-model="formData.contactOrganization"
                    placeholder="请输入联系人组织"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="联系人部门" prop="contactDepartment">
                  <el-input
                    v-model="formData.contactDepartment"
                    placeholder="请输入联系人部门"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="联系人职位" prop="contactPosition">
              <el-input
                v-model="formData.contactPosition"
                placeholder="请输入联系人职位"
                clearable
              />
            </el-form-item>
          </el-card>

          <!-- 参与人数统计 -->
          <el-card shadow="never" class="form-section">
            <template #header>
              <div class="card-header">
                <span>参与人数统计</span>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="攻击方人数">
                  <el-input-number
                    v-model="formData.attackerCount"
                    :min="0"
                    controls-position="right"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="防守方人数">
                  <el-input-number
                    v-model="formData.defenderCount"
                    :min="0"
                    controls-position="right"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="裁判人数">
                  <el-input-number
                    v-model="formData.refereeCount"
                    :min="0"
                    controls-position="right"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="目标系统数">
              <el-input-number
                v-model="formData.targetSystemCount"
                :min="0"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-card>
        </el-form>
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
      :title="`项目详情 - ID: ${currentDetail?.id || '未知'}`"
      direction="rtl"
      size="70%"
      class="detail-drawer"
    >
      <div class="detail-content" v-if="currentDetail">
        <div class="detail-header">
          <h2>项目详情</h2>
        </div>

        <el-card shadow="never" class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目ID">{{
              currentDetail.id || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="项目名称">{{
              currentDetail.projectName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="所属组织">{{
              currentDetail.organization || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="所属行业">{{
              currentDetail.industry || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="项目地点">{{
              currentDetail.location || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="项目状态">
              <el-tag :type="getStatusType(currentDetail.status)">
                {{ getStatusText(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="开始时间">{{
              formatFullTime(currentDetail.startDate)
            }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{
              formatFullTime(currentDetail.endDate)
            }}</el-descriptions-item>
            <el-descriptions-item label="每日开始时间">{{
              currentDetail.dailyStartTime || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="每日结束时间">{{
              currentDetail.dailyEndTime || '-'
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 负责人信息 -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <span>负责人信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="负责人姓名">{{
              currentDetail.leaderName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="负责人组织">{{
              currentDetail.leaderOrganization || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="负责人部门">{{
              currentDetail.leaderDepartment || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="负责人职位">{{
              currentDetail.leaderPosition || '-'
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 联系人信息 -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <span>联系人信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="联系人姓名">{{
              currentDetail.contactName || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="联系人电话">{{
              currentDetail.contactPhone || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="联系人组织">{{
              currentDetail.contactOrganization || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="联系人部门">{{
              currentDetail.contactDepartment || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="联系人职位">{{
              currentDetail.contactPosition || '-'
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 参与人数统计 -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <span>参与人数统计</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="攻击方人数">{{
              currentDetail.attackerCount || 0
            }}</el-descriptions-item>
            <el-descriptions-item label="防守方人数">{{
              currentDetail.defenderCount || 0
            }}</el-descriptions-item>
            <el-descriptions-item label="裁判人数">{{
              currentDetail.refereeCount || 0
            }}</el-descriptions-item>
            <el-descriptions-item label="目标系统数">{{
              currentDetail.targetSystemCount || 0
            }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </el-drawer>

    <!-- 导入对话框 -->
    <el-dialog v-model="importVisible" title="导入项目" width="500px">
      <el-upload
        ref="uploadRef"
        action="#"
        :before-upload="beforeImportUpload"
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls"
      >
        <template #trigger>
          <el-button type="primary">选择文件</el-button>
        </template>
        <template #tip>
          <div class="el-upload__tip">请上传Excel文件(.xlsx, .xls格式)，单个文件不超过10MB</div>
        </template>
      </el-upload>

      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" @click="handleImportSubmit">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Delete,
  Refresh,
  Filter,
  DocumentCopy,
  View,
  Edit,
  Upload,
} from '@element-plus/icons-vue'
import TimeRangePicker from '@/components/TimeRangePicker.vue'
import { useRouter } from 'vue-router'
import { projectApi } from '@/api/services/project/project.js'
import { projectMaterialApi } from '@/api/services/project/projectMaterial.js'
import {
  formatDate,
  formatFullTime,
  formatMillisecondsToTime,
  calculateProjectStatus,
  validateStartDate,
  validateEndDate,
  validateDailyStartTime,
  validateDailyEndTime,
  copyToClipboard,
} from '@/utils'

const statusOptions = [
  { label: '项目未开始', value: 'unstarted' },
  { label: '项目进行中', value: 'progress' },
  { label: '项目已结束', value: 'completed' },
]

// 状态
const loading = ref(false)
const saving = ref(false)
const showMoreFilters = ref(false)
const drawerVisible = ref(false)
const detailVisible = ref(false)
const importVisible = ref(false)
const tableData = ref([])
const selectedRows = ref([])
const formRef = ref()
const uploadRef = ref()
const router = useRouter()
const isComponentMounted = ref(true)
const pendingTimeouts = []

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

// 筛选参数
const filterParams = reactive({
  projectName: '',
  organization: '',
  industry: '',
  location: '',
  leaderName: '',
  status: '',
})

// 时间筛选
const selectedTimeField = ref('createTime')
const searchTimeRange = reactive({
  hasTimeRange: 0,
  timeField: 'createTime',
  minTime: '',
  maxTime: '',
})

// 抽屉模式
const drawerMode = ref('add') // 'add' | 'edit'
const drawerTitle = computed(() => (drawerMode.value === 'add' ? '新增项目' : '编辑项目'))

// 表单数据
const formData = reactive({
  projectName: '',
  organization: '',
  industry: '',
  location: '',
  startDate: '',
  endDate: '',
  dailyStartTime: '',
  dailyEndTime: '',
  leaderName: '',
  leaderOrganization: '',
  leaderDepartment: '',
  leaderPosition: '',
  contactName: '',
  contactPhone: '',
  contactOrganization: '',
  contactDepartment: '',
  contactPosition: '',
  attackerCount: 0,
  defenderCount: 0,
  refereeCount: 0,
  targetSystemCount: 0,
  status: 'not_started',
})

// 表单验证规则
const formRules = {
  projectName: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  organization: [{ required: true, message: '请输入所属组织', trigger: 'blur' }],
  startDate: [
    { required: true, message: '请选择开始时间', trigger: 'change' },
    { validator: validateStartDate, trigger: 'change' },
  ],
  endDate: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    { validator: validateEndDate, trigger: 'change' },
  ],
  leaderName: [{ required: true, message: '请输入负责人姓名', trigger: 'blur' }],
  dailyStartTime: [{ validator: validateDailyStartTime, trigger: 'change' }],
  dailyEndTime: [{ validator: validateDailyEndTime, trigger: 'change' }],
}
// 当前操作的数据
const currentDetail = ref(null)
const importFile = ref(null)

const materialCategoryMap = {
  document: '项目文档',
  word: '技战法',
  test: '测试报告',
  meeting: '会议记录',
  other: '其他',
}

const handleAddMaterial = (project) => {
  console.log('添加材料，项目信息:', project)

  // 使用Vue Router跳转到项目材料管理页面
  router.push({
    path: '/project/ProjectMaterialManagement',
    query: {
      projectId: project.id, // 传递项目ID
      projectName: project.projectName, // 传递项目名称（用于显示）
      action: 'add',
      timestamp: Date.now(),
    },
  })
}
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'

  // 确保是数字类型
  if (typeof bytes === 'string') {
    bytes = parseInt(bytes)
  }

  if (isNaN(bytes) || bytes < 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const index = Math.min(i, sizes.length - 1)

  let sizeValue = bytes / Math.pow(k, index)

  if (index === 0) {
    // 字节单位，不保留小数
    return Math.round(sizeValue) + ' ' + sizes[index]
  } else {
    if (sizeValue < 10) {
      return sizeValue.toFixed(2) + ' ' + sizes[index] // 小于10保留2位小数
    } else if (sizeValue < 100) {
      return sizeValue.toFixed(1) + ' ' + sizes[index] // 小于100保留1位小数
    } else {
      return Math.round(sizeValue) + ' ' + sizes[index] // 大于100取整
    }
  }
}
// 展开行变化处理
const handleExpandChange = async (row, expandedRows) => {
  console.log('展开行变化:', row, expandedRows)

  if (!isComponentMounted.value) {
    return
  }

  if (expandedRows.includes(row)) {
    // 展开时加载材料数据
    try {
      await loadProjectMaterials(row)
    } catch (error) {
      console.error('加载材料数据失败:', error)
      if (isComponentMounted.value) {
        ElMessage.error('加载材料数据失败')
      }
    }
  } else {
    // 收起时清理数据
    row.expandMaterials = []
  }
}

// 加载项目材料
// 加载项目材料 - 修复版本
const loadProjectMaterials = async (project) => {
  if (!isComponentMounted.value) {
    return
  }

  try {
    console.log('加载项目材料，项目ID:', project.id)

    const result = await projectMaterialApi.getPageList({
      page: 1,
      limit: 100,
      data: {
        projectId: project.id,
      },
    })

    if (isComponentMounted.value) {
      if (result && result.code === 200) {
        project.expandMaterials = result.data || []
        console.log('加载到的材料数量:', project.expandMaterials.length)
      } else {
        project.expandMaterials = []
        console.log('该项目暂无材料')
      }
    }
  } catch (error) {
    console.error('加载项目材料失败:', error)
    if (isComponentMounted.value) {
      project.expandMaterials = []
    }
  }
}

// 下载材料
const handleDownloadMaterial = async (material) => {
  try {
    console.log('下载材料:', material)

    // 调用项目材料管理的下载函数
    const requestData = {
      id: material.id,
      attachmentName: material.attachmentName,
    }

    const response = await projectMaterialApi.download(requestData)

    if (response && response.data) {
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = material.attachmentName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      ElMessage.success('开始下载...')
    }
  } catch (error) {
    console.error('下载材料失败:', error)
    ElMessage.error('下载失败: ' + error.message)
  }
}

// 删除材料
const handleDeleteMaterial = async (material, project) => {
  try {
    await ElMessageBox.confirm(`确定删除材料"${material.materialName}"吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await projectMaterialApi.batchRemove([material.id])

    if (result && result.code === 200) {
      ElMessage.success('删除成功')
      // 重新加载该项目的材料
      await loadProjectMaterials(project)
    } else {
      const errorMsg = result?.message || '删除失败'
      ElMessage.error('删除失败:' + errorMsg)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败:' + error.message)
    }
  }
}

// 材料分类工具函数
const getMaterialCategoryType = (category) => {
  const typeMap = {
    document: 'primary',
    word: 'success',
    test: 'warning',
    meeting: 'info',
    other: 'default',
  }
  return typeMap[category] || 'default'
}

const getMaterialCategoryText = (category) => {
  return materialCategoryMap[category] || category
}

// 附件类型工具函数（复用项目材料管理的）
const getAttachmentTypeTagType = (type) => {
  const typeMap = {
    pdf: 'primary',
    jpg: 'success',
    png: 'warning',
    jpeg: 'info',
  }
  return typeMap[type] || 'default'
}

const getAttachmentTypeText = (type) => {
  const textMap = {
    pdf: 'PDF',
    jpg: 'JPG',
    png: 'PNG',
    jpeg: 'JPEG',
  }
  return textMap[type] || type
} // ========= 数据获取函数 =========
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      limit: pagination.pageSize,
      data: { ...filterParams },
      ...searchTimeRange,
    }

    const result = await projectApi.getPageList(params)

    if (result && result.code === 200) {
      tableData.value = result.data || []
      pagination.total = result.total || 0

      if (tableData.value.length === 0) {
        ElMessage.info('没有查询到数据')
      }
    } else {
      ElMessage.warning('无数据')
      tableData.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('无数据:', error)
    ElMessage.error('无数据: ' + error.message)
  } finally {
    loading.value = false
  }
}

// ========= 搜索相关函数 =========
const handleSearch = () => {
  pagination.currentPage = 1
  fetchData()
}

const handleReset = () => {
  Object.keys(filterParams).forEach((key) => {
    filterParams[key] = ''
  })
  searchTimeRange.hasTimeRange = 0
  searchTimeRange.minTime = ''
  searchTimeRange.maxTime = ''
  pagination.currentPage = 1
  fetchData()
}

const handleRefresh = () => {
  fetchData()
  ElMessage.success('数据已刷新')
}

// ========= 时间筛选 =========
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

// ========= 表格操作 =========
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

const handleAddProject = () => {
  drawerMode.value = 'add'
  // 重置表单数据
  Object.keys(formData).forEach((key) => {
    formData[key] = key.includes('Count') ? 0 : ''
  })
  drawerVisible.value = true
}

const handleEditProject = (row) => {
  console.log('编辑行数据:', row)

  drawerMode.value = 'edit'
  currentDetail.value = row

  // 重置表单数据
  Object.keys(formData).forEach((key) => {
    formData[key] = key.includes('Count') ? 0 : ''
  })

  // 安全填充数据
  Object.keys(formData).forEach((key) => {
    const value = row[key]
    if (value !== null && value !== undefined && value !== '') {
      // 处理时间字段
      if (key === 'startDate' || key === 'endDate') {
        // 日期时间字段：时间戳转换为 "YYYY-MM-DD HH:mm:ss"
        if (typeof value === 'number') {
          const date = new Date(value)
          if (!isNaN(date.getTime())) {
            const year = date.getFullYear()
            const month = (date.getMonth() + 1).toString().padStart(2, '0')
            const day = date.getDate().toString().padStart(2, '0')
            const hours = date.getHours().toString().padStart(2, '0')
            const minutes = date.getMinutes().toString().padStart(2, '0')
            const seconds = date.getSeconds().toString().padStart(2, '0')
            formData[key] = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
          }
        } else {
          formData[key] = value
        }
      } else if (key === 'dailyStartTime' || key === 'dailyEndTime') {
        // 时间字段：毫秒数转换为 "HH:mm:ss"
        if (typeof value === 'number') {
          formData[key] = formatMillisecondsToTime(value)
        } else {
          formData[key] = value
        }
      } else {
        formData[key] = value
      }
    }
  })

  console.log('填充后的表单数据:', formData)
  drawerVisible.value = true
}
const handleViewDetail = async (row) => {
  try {
    console.log('查看详情，ID:', row.id)

    // 发送正确的格式
    const result = await projectApi.getInfo({ id: row.id })

    console.log('详情接口返回:', result)

    if (result && result.code === 200 && result.data) {
      const data = result.data

      // 转换时间字段格式用于显示
      const formattedData = {
        ...data,
        // 转换时间戳为日期字符串
        startDate: data.startDate ? new Date(data.startDate).toLocaleString() : '',
        endDate: data.endDate ? new Date(data.endDate).toLocaleString() : '',
        // 转换毫秒数为时间字符串
        dailyStartTime: data.dailyStartTime ? formatMillisecondsToTime(data.dailyStartTime) : '',
        dailyEndTime: data.dailyEndTime ? formatMillisecondsToTime(data.dailyEndTime) : '',
      }

      currentDetail.value = formattedData
      detailVisible.value = true
      console.log('格式化后的详情数据:', formattedData)
    } else {
      const errorMsg = result?.message || '未知错误'
      ElMessage.error('获取详情失败: ' + errorMsg)
    }
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取详情失败: ' + error.message)
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除项目 "${row.projectName}" 吗?`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await projectApi.batchRemove([row.id])

    if (result && result.code === 200) {
      ElMessage.success('删除成功')
      await fetchData()
    } else {
      const errorMsg = result?.message || '删除失败'
      ElMessage.error('删除失败: ' + errorMsg)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

const handleBatchDelete = async () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要删除的项目')
    return
  }

  try {
    const ids = selectedRows.value.map((item) => item.id)
    await ElMessageBox.confirm(`确定删除选中的 ${ids.length} 个项目吗?`, '批量删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const result = await projectApi.batchRemove(ids)

    if (result && result.code === 200) {
      ElMessage.success(`成功删除 ${ids.length} 个项目`)
      selectedRows.value = []
      await fetchData()
    } else {
      const errorMsg = result?.message || '批量删除失败'
      ElMessage.error('批量删除失败: ' + errorMsg)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败: ' + error.message)
    }
  }
}

const handleSave = async () => {
  try {
    if (!formRef.value) return
    const valid = await formRef.value.validate()
    if (!valid) return

    saving.value = true
    const calculatedStatus = calculateProjectStatus(formData.startDate, formData.endDate)
    // 工具函数：将 "HH:mm:ss" 转换为毫秒数
    const timeToMilliseconds = (timeStr) => {
      if (!timeStr) return null

      try {
        if (typeof timeStr === 'string') {
          const [hours, minutes, seconds] = timeStr.split(':')
          return (parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds)) * 1000
        } else if (typeof timeStr === 'number') {
          return timeStr
        }
        return null
      } catch (error) {
        console.error('时间转换错误:', error)
        return null
      }
    }

    // 转换函数：将日期时间字符串转换为时间戳
    const dateToTimestamp = (dateStr) => {
      if (!dateStr) return null

      try {
        if (typeof dateStr === 'string' && dateStr.includes(' ')) {
          const date = new Date(dateStr.replace(' ', 'T'))
          return isNaN(date.getTime()) ? null : date.getTime()
        } else if (typeof dateStr === 'number') {
          return dateStr
        }
        return null
      } catch (error) {
        console.error('日期转换错误:', error)
        return null
      }
    }

    // 准备保存数据
    const saveData = {
      ...formData,
      // 发送时间戳
      status: calculatedStatus,
      startDate: dateToTimestamp(formData.startDate),
      endDate: dateToTimestamp(formData.endDate),
      // 发送毫秒数
      dailyStartTime: timeToMilliseconds(formData.dailyStartTime),
      dailyEndTime: timeToMilliseconds(formData.dailyEndTime),
      attackerCount: Number(formData.attackerCount) || 0,
      defenderCount: Number(formData.defenderCount) || 0,
      refereeCount: Number(formData.refereeCount) || 0,
      targetSystemCount: Number(formData.targetSystemCount) || 0,
    }

    // 移除前端使用的临时字段
    delete saveData.id

    console.log('保存数据:', JSON.stringify(saveData, null, 2))

    let result
    if (drawerMode.value === 'edit' && currentDetail.value?.id) {
      saveData.id = currentDetail.value.id
      result = await projectApi.modify(saveData)
    } else {
      result = await projectApi.add(saveData)
    }

    if (result && result.code === 200) {
      ElMessage.success(drawerMode.value === 'add' ? '创建成功' : '更新成功')
      drawerVisible.value = false
      await fetchData()
    } else {
      const errorMsg = result?.message || '保存失败'
      ElMessage.error('保存失败:' + errorMsg)
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败:' + error.message)
  } finally {
    saving.value = false
  }
}
// ========= 导入功能 =========
const handleImport = () => {
  importVisible.value = true
}

const beforeImportUpload = (file) => {
  const isExcel = /\.(xlsx|xls)$/i.test(file.name)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isExcel) {
    ElMessage.error('只能上传Excel文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }

  importFile.value = file
  return false // 手动上传
}

const handleImportSubmit = async () => {
  if (!importFile.value) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }

  try {
    loading.value = true
    const result = await projectApi.importProject(importFile.value)

    if (result && result.code === 200) {
      ElMessage.success('导入成功')
      importVisible.value = false
      importFile.value = null
      if (uploadRef.value) {
        uploadRef.value.clearFiles()
      }
      await fetchData()
    } else {
      const errorMsg = result?.message || '导入失败'
      ElMessage.error('导入失败: ' + errorMsg)
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// ========= 状态处理函数 =========
const getStatusType = (status) => {
  const statusMap = {
    unstarted: 'info',
    progress: 'primary',
    completed: 'success',
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    unstarted: '项目未开始',
    progress: '项目进行中',
    completed: '项目已结束',
  }
  return textMap[status] || status
}

// 监听日期变化，自动更新状态预览
watch([() => formData.startDate, () => formData.endDate], ([startDate, endDate]) => {
  if (startDate && endDate) {
    const status = calculateProjectStatus(startDate, endDate)
    // 可以在这里更新状态预览
    console.log('预计项目状态:', getStatusText(status))
  }
})

// 监听每日时间变化
watch([() => formData.dailyStartTime, () => formData.dailyEndTime], ([startTime, endTime]) => {
  if (startTime && endTime && startTime >= endTime) {
    ElMessage.warning('每日开始时间不能晚于结束时间')
  }
})
onUnmounted(() => {
  console.log('组件卸载，清理资产...')
  isComponentMounted.value = false

  // 清理所有定时器
  pendingTimeouts.forEach((timer) => {
    clearTimeout(timer)
  })
  pendingTimeouts.length = 0
})
// 初始化
onMounted(() => {
  fetchData()

  // 每5分钟自动刷新一次状态
  setInterval(
    () => {
      if (tableData.value.length > 0) {
        fetchData()
        console.log('自动刷新项目状态')
      }
    },
    5 * 60 * 1000,
  )
})
</script>

<style scoped lang="scss">
.project-management-container {
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

  .table-right-actions {
    display: flex;
    gap: 8px;
  }
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
.participant-stats {
  display: flex;
  justify-content: space-around;
  align-items: center;

  .stat-item {
    font-size: 12px;
    color: #666;
  }
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

.drawer-footer {
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

  .info-card {
    margin-bottom: 20px;
    border: none;

    :deep(.el-card__body) {
      padding: 0;
    }
  }
}

// 响应式设计
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
  .project-management-container {
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

    .table-right-actions {
      width: 100%;
      justify-content: flex-end;
    }
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
.material-expand-panel {
  padding: 12px;
  background-color: #fafafa;
  border-radius: 4px;
  width: 65%;

  .expand-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    h4 {
      margin: 0;
      color: #303133;
      font-size: 14px;
      font-weight: 500;
    }

    .expand-add-btn {
      margin-left: auto;
      font-size: 12px;
      padding: 5px 10px;
      height: auto;
    }
  }

  .material-sub-table {
    width: 100%;
    min-width: auto;

    :deep(.el-table) {
      // 移除横向滚动
      overflow-x: hidden;

      .el-table__body-wrapper {
        overflow-x: hidden;
      }

      // 设置固定宽度
      .el-table__header-wrapper,
      .el-table__body-wrapper {
        width: 100% !important;
      }

      // 单元格样式
      .el-table__cell {
        padding: 6px 0;
        height: 36px;
      }

      // 操作列固定
      .el-table__fixed-right {
        box-shadow: none;
      }
    }
  }
}

// 简化材料名称显示
.material-name-cell {
  .material-name-text {
    display: block;
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
  }
}

// 文件大小样式
.file-size {
  font-size: 12px;
  color: #606266;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}
</style>
