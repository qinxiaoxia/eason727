// src/utils/validate.js
//时间的通用验证方法

/**
 * 验证开始时间不能晚于或等于结束时间
 * @param {Object} formData - 表单数据对象
 * @returns {boolean|string} true表示验证通过，string表示错误信息
 */
export const validateStartDate = (formData) => {
  if (!formData.startDate) return true

  if (formData.endDate) {
    const start = new Date(formData.startDate.replace(' ', 'T'))
    const end = new Date(formData.endDate.replace(' ', 'T'))

    if (start >= end) {
      return '开始时间不能晚于或等于结束时间'
    }
  }
  return true
}

/**
 * 验证结束时间不能早于或等于开始时间
 * @param {Object} formData - 表单数据对象
 * @returns {boolean|string} true表示验证通过，string表示错误信息
 */
export const validateEndDate = (formData) => {
  if (!formData.endDate) return true

  if (formData.startDate) {
    const start = new Date(formData.startDate.replace(' ', 'T'))
    const end = new Date(formData.endDate.replace(' ', 'T'))

    if (end <= start) {
      return '结束时间不能早于或等于开始时间'
    }
  }
  return true
}

/**
 * 验证每日开始时间不能晚于或等于每日结束时间
 * @param {Object} formData - 表单数据对象
 * @returns {boolean|string} 验证结果
 */
export const validateDailyStartTime = (formData) => {
  if (!formData.dailyStartTime || !formData.dailyEndTime) return true

  const start = formData.dailyStartTime
  const end = formData.dailyEndTime

  if (start >= end) {
    return '每日开始时间不能晚于或等于每日结束时间'
  }
  return true
}

/**
 * 验证每日结束时间不能早于或等于每日开始时间
 * @param {Object} formData - 表单数据对象
 * @returns {boolean|string} 验证结果
 */
export const validateDailyEndTime = (formData) => {
  if (!formData.dailyEndTime || !formData.dailyStartTime) return true

  const start = formData.dailyStartTime
  const end = formData.dailyEndTime

  if (end <= start) {
    return '每日结束时间不能早于或等于每日开始时间'
  }
  return true
}

/**
 * 创建Element Plus表单验证规则
 * @param {Object} fieldRules - 字段验证规则配置
 * @returns {Object} Element Plus验证规则对象
 */
export const createFormRules = (fieldRules) => {
  const rules = {}

  Object.keys(fieldRules).forEach((fieldName) => {
    const fieldConfig = fieldRules[fieldName]
    rules[fieldName] = []

    // 必填验证
    if (fieldConfig.required) {
      rules[fieldName].push({
        required: true,
        message: fieldConfig.message || `请输入${fieldConfig.label}`,
        trigger: fieldConfig.trigger || 'blur',
      })
    }

    // 自定义验证器
    if (fieldConfig.validator) {
      rules[fieldName].push({
        validator: fieldConfig.validator,
        trigger: fieldConfig.trigger || 'change',
      })
    }
  })

  return rules
}
