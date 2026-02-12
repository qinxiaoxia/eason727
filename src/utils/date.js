// src/utils/date.js
//用于时间格式化
//用于自动计算项目时间
/**
 * 格式化日期为本地日期字符串 (YYYY-MM-DD)
 * @param {string|number} dateStr - 日期字符串或时间戳
 * @returns {string} 格式化后的日期
 */
export const formatDate = (dateStr) => {
  if (!dateStr) return '-'

  try {
    // 处理各种日期格式
    const date = new Date(dateStr)
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      return String(dateStr) // 如果无效，返回原字符串
    }

    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  } catch (error) {
    console.error('日期格式化错误:', error)
    return String(dateStr)
  }
}

/**
 * 格式化完整日期时间 (YYYY-MM-DD HH:mm:ss)
 * @param {string|number} timeStr - 时间字符串或时间戳
 * @returns {string} 格式化后的完整时间
 */
export const formatFullTime = (timeStr) => {
  if (!timeStr) return '-'

  try {
    const date = new Date(timeStr)
    if (isNaN(date.getTime())) {
      return String(timeStr)
    }

    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch (error) {
    console.error('完整时间格式化错误:', error)
    return String(timeStr)
  }
}

/**
 * 将毫秒数转换为 HH:mm:ss 格式
 * @param {number} milliseconds - 毫秒数
 * @returns {string} 格式化的时间字符串
 */
export const formatMillisecondsToTime = (milliseconds) => {
  if (!milliseconds && milliseconds !== 0) return ''

  try {
    const totalSeconds = Math.floor(milliseconds / 1000)
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = totalSeconds % 60

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  } catch (error) {
    console.error('毫秒转时间错误:', error)
    return ''
  }
}

/**
 * 将 HH:mm:ss 格式的时间字符串转换为毫秒数
 * @param {string} timeStr - 时间字符串 (HH:mm:ss)
 * @returns {number|null} 毫秒数或null
 */
export const timeToMilliseconds = (timeStr) => {
  if (!timeStr) return null

  try {
    if (typeof timeStr === 'string') {
      const [hours, minutes, seconds] = timeStr.split(':').map(Number)
      return (hours * 3600 + minutes * 60 + seconds) * 1000
    } else if (typeof timeStr === 'number') {
      return timeStr
    }
    return null
  } catch (error) {
    console.error('时间转毫秒错误:', error)
    return null
  }
}

/**
 * 将日期字符串转换为时间戳
 * @param {string} dateStr - 日期字符串
 * @returns {number|null} 时间戳或null
 */
export const dateToTimestamp = (dateStr) => {
  if (!dateStr) return null

  try {
    // 处理 "YYYY-MM-DD HH:mm:ss" 格式
    if (typeof dateStr === 'string' && dateStr.includes(' ')) {
      const date = new Date(dateStr.replace(' ', 'T'))
      return isNaN(date.getTime()) ? null : date.getTime()
    } else if (typeof dateStr === 'number') {
      return dateStr
    }
    return null
  } catch (error) {
    console.error('日期转时间戳错误:', error)
    return null
  }
}

/**
 * 计算项目状态（根据开始和结束时间）
 * @param {string} startDate - 开始时间
 * @param {string} endDate - 结束时间
 * @returns {string} 状态值: 'unstarted' | 'progress' | 'completed'
 */
export const calculateProjectStatus = (startDate, endDate) => {
  if (!startDate || !endDate) return 'unstarted'

  try {
    const now = new Date().getTime()
    const startTime = new Date(startDate).getTime()
    const endTime = new Date(endDate).getTime()

    if (now < startTime) {
      return 'unstarted'
    } else if (now >= startTime && now <= endTime) {
      return 'progress'
    } else {
      return 'completed'
    }
  } catch (error) {
    console.error('计算项目状态错误:', error)
    return 'unstarted'
  }
}
