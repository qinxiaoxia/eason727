<template>
  <div class="time-range-picker">
    <el-popover
      v-model:visible="popoverVisible"
      placement="bottom-start"
      :width="popoverWidth"
      trigger="click"
    >
      <template #reference>
        <el-button class="trigger-button" :type="hasActiveFilter ? 'primary' : 'default'" plain>
          <span class="button-text">
            {{ displayText }}
          </span>
          <el-icon class="arrow-icon" :class="{ rotate: popoverVisible }">
            <arrow-down />
          </el-icon>
        </el-button>
      </template>

      <div class="popover-content">
        <!-- 左侧快速选择区域 -->
        <div class="quick-select-section">
          <div class="section-title">快速选择</div>
          <div class="quick-options">
            <div
              v-for="option in quickOptions"
              :key="option.value"
              class="quick-option"
              :class="{ active: activeQuickOption === option.value }"
              @click="handleQuickOptionClick(option.value)"
            >
              {{ option.label }}
            </div>
          </div>
        </div>

        <!-- 右侧日历选择区域 -->
        <div class="calendar-section">
          <div class="section-title">自定义时间</div>
          <div class="date-range-picker">
            <el-date-picker
              v-model="selectedDateRange"
              type="daterange"
              unlink-panels
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="shortcuts"
              :format="dateFormat"
              :value-format="valueFormat"
              @change="handleDateRangeChange"
            />
          </div>

          <!-- 时间字段选择 -->
          <div v-if="showTimeField" class="time-field-selector">
            <div class="field-label">筛选时间字段：</div>
            <el-radio-group v-model="selectedTimeField" @change="handleTimeFieldChange">
              <el-radio label="createdAt">首次发现时间</el-radio>
              <el-radio label="lastseenAt">最后更新时间</el-radio>
            </el-radio-group>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button size="small" @click="handleClear">清除</el-button>
            <el-button type="primary" size="small" @click="handleConfirm">确定</el-button>
          </div>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

// 组件属性
const props = defineProps({
  // 默认选中的时间字段
  timeField: {
    type: String,
    default: 'createdAt',
    validator: (value) => ['createdAt', 'lastseenAt'].includes(value),
  },
  // 是否显示时间字段选择
  showTimeField: {
    type: Boolean,
    default: true,
  },
  // 日期显示格式
  dateFormat: {
    type: String,
    default: 'YYYY-MM-DD',
  },
  // 值格式
  valueFormat: {
    type: String,
    default: 'x', // 时间戳
  },
  // 弹窗宽度
  popoverWidth: {
    type: Number,
    default: 680,
  },
  // 是否立即触发搜索
  immediate: {
    type: Boolean,
    default: false,
  },
})

// 定义事件
const emit = defineEmits([
  'change', // 时间范围变化
  'confirm', // 确认选择
  'clear', // 清除选择
  'update:timeField', // 更新时间字段
])

// 响应式数据
const popoverVisible = ref(false)
const activeQuickOption = ref('7d')
const selectedDateRange = ref([])
const selectedTimeField = ref(props.timeField)
const hasActiveFilter = ref(false)

// 快捷选项配置
const quickOptions = [
  { label: '最近一天', value: '1d' },
  { label: '最近三天', value: '3d' },
  { label: '最近七天', value: '7d' },
  { label: '最近一个月', value: '1m' },
  { label: '最近半年', value: '6m' },
  { label: '最近一年', value: '1y' },
]

// 日期快捷方式
const shortcuts = [
  {
    text: '今天',
    value: () => {
      const end = new Date()
      const start = new Date()
      return [start, end]
    },
  },
  {
    text: '昨天',
    value: () => {
      const end = new Date()
      end.setDate(end.getDate() - 1)
      const start = new Date()
      start.setDate(start.getDate() - 1)
      return [start, end]
    },
  },
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 7)
      return [start, end]
    },
  },
  {
    text: '最近一个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 1)
      return [start, end]
    },
  },
  {
    text: '最近三个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 3)
      return [start, end]
    },
  },
]

const displayText = computed(() => {
  if (selectedDateRange.value && selectedDateRange.value.length === 2) {
    const [start, end] = selectedDateRange.value
    const startDate = new Date(Number(start))
    const endDate = new Date(Number(end))

    return `${formatDate(startDate)} - ${formatDate(endDate)}`
  }

  const option = quickOptions.find((opt) => opt.value === activeQuickOption.value)
  return option ? option.label : '开始日期 - 结束日期'
})

// 日期格式化函数
const formatDate = (date) => {
  if (!(date instanceof Date)) {
    date = new Date(Number(date))
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 在 TimeRangePicker.vue 中修复时间计算
const calculateTimeRange = (option) => {
  const end = new Date()
  const endTime = end.getTime() // 当前时间戳
  let startTime

  switch (option) {
    case '1d':
      startTime = endTime - 24 * 60 * 60 * 1000 // 1天前
      break
    case '3d':
      startTime = endTime - 3 * 24 * 60 * 60 * 1000 // 3天前
      break
    case '7d':
      startTime = endTime - 7 * 24 * 60 * 60 * 1000 // 7天前
      break
    case '1m':
      startTime = endTime - 30 * 24 * 60 * 60 * 1000 // 30天前
      break
    case '6m':
      startTime = endTime - 180 * 24 * 60 * 60 * 1000 // 180天前
      break
    case '1y':
      startTime = endTime - 365 * 24 * 60 * 60 * 1000 // 365天前
      break
    default:
      startTime = endTime - 7 * 24 * 60 * 60 * 1000 // 默认7天前
  }

  const startDate = formatDate(startTime)
  const endDate = formatDate(endTime)
  console.log('⏰ TimeRangePicker 计算的时间范围:', {
    option,
    startTime,
    endTime,
    startDate: startDate,
    endDate: endDate,
    isFuture: startTime > endTime,
  })

  return { startTime, endTime, startDate, endDate }
}

// 处理快捷选项点击
const handleQuickOptionClick = (option) => {
  activeQuickOption.value = option
  selectedDateRange.value = [] // 清空日期选择

  const timeRange = calculateTimeRange(option)
  hasActiveFilter.value = true

  emit('change', {
    startTime: timeRange.startTime,
    endTime: timeRange.endTime,
    timeField: selectedTimeField.value,
    startStr: timeRange.startDate,
    endStr: timeRange.endDate,
    type: 'quick',
    option,
  })

  if (props.immediate) {
    emit('confirm', {
      startTime: timeRange.startTime,
      endTime: timeRange.endTime,
      timeField: selectedTimeField.value,
    })
    popoverVisible.value = false
  }
}

// 处理日期范围变化
const handleDateRangeChange = (range) => {
  if (range && range.length === 2) {
    activeQuickOption.value = 'custom'
    hasActiveFilter.value = true

    const [start, end] = range
    const endTime = new Date(Number(end)).setHours(23, 59, 59, 999)

    emit('change', {
      startTime: Number(start),
      endTime: endTime,
      timeField: selectedTimeField.value,
      startStr: formatDate(start),
      endStr: formatDate(end),
      type: 'custom',
    })

    if (props.immediate) {
      emit('confirm', {
        startTime: Number(start),
        endTime: endTime,
        timeField: selectedTimeField.value,
        startStr: formatDate(start),
        endStr: formatDate(end),
      })
      popoverVisible.value = false
    }
  }
}

// 处理时间字段变化
const handleTimeFieldChange = (field) => {
  selectedTimeField.value = field
  emit('update:timeField', field)

  // 重新触发当前筛选
  if (hasActiveFilter.value) {
    if (selectedDateRange.value && selectedDateRange.value.length === 2) {
      handleDateRangeChange(selectedDateRange.value)
    } else {
      handleQuickOptionClick(activeQuickOption.value)
    }
  }
}

// 处理确认
const handleConfirm = () => {
  if (selectedDateRange.value && selectedDateRange.value.length === 2) {
    const [start, end] = selectedDateRange.value
    const endTime = new Date(Number(end)).setHours(23, 59, 59, 999)

    emit('confirm', {
      startTime: Number(start),
      endTime: endTime,
      startStr: formatDate(start),
      endStr: formatDate(end),
      timeField: selectedTimeField.value,
    })
  } else {
    const timeRange = calculateTimeRange(activeQuickOption.value)
    emit('confirm', {
      startTime: timeRange.startTime,
      endTime: timeRange.endTime,
      startStr: formatDate(timeRange.startTime),
      endStr: formatDate(timeRange.endTime),
      timeField: selectedTimeField.value,
    })
  }

  popoverVisible.value = false
}

// 处理清除
const handleClear = () => {
  activeQuickOption.value = '7d'
  selectedDateRange.value = []
  hasActiveFilter.value = false

  emit('clear')
  emit('confirm', {
    startTime: null,
    endTime: null,
    timeField: selectedTimeField.value,
  })

  popoverVisible.value = false
}

// 暴露方法给父组件
defineExpose({
  clear: handleClear,
  getValue: () => ({
    startTime: selectedDateRange.value[0] ? Number(selectedDateRange.value[0]) : null,
    endTime: selectedDateRange.value[1]
      ? new Date(Number(selectedDateRange.value[1])).setHours(23, 59, 59, 999)
      : null,
    timeField: selectedTimeField.value,
    quickOption: activeQuickOption.value,
  }),
})

// 初始化
onMounted(() => {})
</script>

<style scoped>
.time-range-picker {
  display: inline-block;
}

.trigger-button {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  font-size: 14px;
}

.button-text {
  display: flex;
  align-items: center;
  gap: 4px;
}

.arrow-icon {
  margin-left: 4px;
  transition: transform 0.2s;
}

.arrow-icon.rotate {
  transform: rotate(180deg);
}

.popover-content {
  display: flex;
  background: white;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.quick-select-section {
  width: 120px;
  padding: 16px 0;
  border-right: 1px solid #e6e6e6;
  background-color: #fafafa;
}

.section-title {
  padding: 0 16px 12px 16px;
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  border-bottom: 1px solid #e6e6e6;
  margin-bottom: 8px;
}

.quick-options {
  display: flex;
  flex-direction: column;
  padding: 0 8px;
}

.quick-option {
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: all 0.2s ease;
  user-select: none;
}

.quick-option:hover {
  background-color: #f5f7fa;
  color: #409eff;
}

.quick-option.active {
  background-color: #ecf5ff;
  color: #409eff;
  font-weight: 500;
}

.calendar-section {
  flex: 1;
  padding: 16px;
  min-width: 500px;
}

.date-range-picker {
  margin-bottom: 20px;
}

.time-field-selector {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e6e6e6;
}

.field-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
}

.time-field-selector .el-radio-group {
  display: flex;
  gap: 20px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e6e6e6;
}
</style>
