//表达式转换为中文
export const cronToChinese = (cronExpression) => {
  if (!cronExpression) return '未设置'

  try {
    const parts = cronExpression.split(' ')
    if (parts.length < 6) return cronExpression

    const [second, minute, hour, day, month, week] = parts

    let description = ''

    // 处理秒
    if (second !== '0' && second !== '*') {
      description += `每${second}秒`
      return description
    }

    // 处理分钟和小时
    if (minute === '*' && hour === '*') {
      description += '每分钟'
    } else if (minute === '0' && hour === '*') {
      description += '每小时'
    } else if (minute === '0' && hour !== '*') {
      description += `每天 ${hour.padStart(2, '0')}:00`
    } else if (minute !== '*' && hour !== '*') {
      description += `每天 ${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`
    } else if (minute !== '*' && hour === '*') {
      description += `每小时第${minute}分钟`
    }

    // 处理日期
    if (day !== '*' && day !== '?') {
      if (day.includes('/')) {
        const interval = day.split('/')[1]
        description += `，每${interval}天`
      } else {
        description += `，每月${day}号`
      }
    }

    // 处理星期
    if (week !== '*' && week !== '?') {
      const weekDays = {
        1: '星期一',
        2: '星期二',
        3: '星期三',
        4: '星期四',
        5: '星期五',
        6: '星期六',
        7: '星期日',
        MON: '星期一',
        TUE: '星期二',
        WED: '星期三',
        THU: '星期四',
        FRI: '星期五',
        SAT: '星期六',
        SUN: '星期日',
      }
      description += `，每${weekDays[week] || week}`
    }

    // 处理月份
    if (month !== '*') {
      if (month.includes('/')) {
        const interval = month.split('/')[1]
        description += `，每${interval}个月`
      }
    }

    return description || `自定义计划: ${cronExpression}`
  } catch {
    return cronExpression
  }
}

/**
 * 常用的定时任务预设
 */
export const schedulePresets = [
  {
    label: '每分钟执行',
    value: '0 * * * * ?',
  },
  {
    label: '每5分钟执行',
    value: '0 */5 * * * ?',
  },
  {
    label: '每30分钟执行',
    value: '0 */30 * * * ?',
  },
  {
    label: '每小时执行',
    value: '0 0 * * * ?',
  },
  {
    label: '每天凌晨执行',
    value: '0 0 0 * * ?',
  },
  {
    label: '每天上午6点执行',
    value: '0 0 6 * * ?',
  },
  {
    label: '每天上午9点执行',
    value: '0 0 9 * * ?',
  },
  {
    label: '每天下午6点执行',
    value: '0 0 18 * * ?',
  },
  {
    label: '每周一上午9点执行',
    value: '0 0 9 ? * MON',
  },
  {
    label: '每月1号上午9点执行',
    value: '0 0 9 1 * ?',
  },
]

/**
 * 验证Cron表达式格式
 */
export const validateCronExpression = (cronExpression) => {
  if (!cronExpression) return false

  const cronRegex =
    /^(\*|([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])|\*\/([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])) (\*|([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])|\*\/([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])) (\*|([0-9]|1[0-9]|2[0-3])|\*\/([0-9]|1[0-9]|2[0-3])) (\*|([1-9]|1[0-9]|2[0-9]|3[0-1])|\*\/([1-9]|1[0-9]|2[0-9]|3[0-1])) (\*|([1-9]|1[0-2])|\*\/([1-9]|1[0-2])) (\*|([0-7])|\*\/([0-7]))$/

  return cronRegex.test(cronExpression)
}
