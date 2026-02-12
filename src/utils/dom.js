// src/utils/dom.js

/**
 * 检查元素是否在视口内
 * @param {Element} element - DOM元素
 * @returns {boolean} 是否在视口内
 */
export const isElementInViewport = (element) => {
  if (!element) return false

  const rect = element.getBoundingClientRect()
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  )
}

/**
 * 平滑滚动到元素
 * @param {Element|string} element - DOM元素或选择器
 * @param {Object} options - 滚动选项
 */
export const smoothScrollToElement = (element, options = {}) => {
  const target = typeof element === 'string' ? document.querySelector(element) : element

  if (!target) return

  const { behavior = 'smooth', block = 'start', inline = 'nearest' } = options
  target.scrollIntoView({ behavior, block, inline })
}
