// utils/bannerUtils.js

/**
 * 计算HTTP响应头的字节大小
 * @param {string} bannerText - HTTP响应头文本
 * @returns {number} 字节数
 */
export function calculateBannerSize(bannerText) {
  if (!bannerText || typeof bannerText !== 'string') {
    return 0
  }

  try {
    // 最准确的方法：使用Blob计算字节大小
    return new Blob([bannerText]).size
  } catch {
    // 备用方案：简单字符计数（不够准确但可用）
    return bannerText.length
  }
}

/**
 * 解析HTTP响应头为结构化对象
 * @param {string} bannerText - HTTP响应头文本
 * @returns {Object} 解析后的头信息
 */
export function parseBannerHeaders(bannerText) {
  if (!bannerText) return {}

  const lines = bannerText.split('\n')
  const headers = {}

  lines.forEach((line) => {
    const separatorIndex = line.indexOf(':')
    if (separatorIndex > 0) {
      const key = line.slice(0, separatorIndex).trim()
      const value = line.slice(separatorIndex + 1).trim()
      headers[key] = value
    }
  })

  return headers
}

/**
 * 获取Banner的统计信息
 * @param {string} bannerText - HTTP响应头文本
 * @returns {Object} 统计信息
 */
export function getBannerStats(bannerText) {
  if (!bannerText) {
    return { size: 0, lines: 0, chars: 0, headers: 0 }
  }

  const size = calculateBannerSize(bannerText)
  const lines = bannerText.split('\n').length
  const chars = bannerText.length
  const headers = Object.keys(parseBannerHeaders(bannerText)).length

  return { size, lines, chars, headers }
}

/**
 * 格式化Banner显示
 * @param {string} bannerText - HTTP响应头文本
 * @returns {string} 格式化后的文本
 */
export function formatBannerDisplay(bannerText) {
  if (!bannerText) return ''

  // 可以添加语法高亮、缩进等格式化逻辑
  return bannerText
}
