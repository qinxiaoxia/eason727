// src/utils/index.js

// 导出所有工具函数
export * from './date'
export * from './validate'
export * from './common'
export * from './dom'
export * from './file'
// 或者按需导出（推荐）
export {
  formatDate,
  formatFullTime,
  formatMillisecondsToTime,
  timeToMilliseconds,
  dateToTimestamp,
  calculateProjectStatus,
} from './date'

export {
  validateStartDate,
  validateEndDate,
  validateDailyStartTime,
  validateDailyEndTime,
  createFormRules,
} from './validate'

export { copyToClipboard, debounce, throttle, deepClone, generateId } from './common'

export { isElementInViewport, smoothScrollToElement } from './dom'
