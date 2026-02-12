import { ref, onMounted, onUnmounted, computed } from 'vue'
import { screenDataApi } from '@/api/services/overview/screenDataApi'
import * as echarts from 'echarts'

export function useScreenData() {
  // 响应式数据
  const screenData = ref({
    // 监控范围概览
    overview: {
      domain: 0,
      ip: 0,
      port: 0,
      app: 0,
      backend: 0,
    },
    // 两高一弱态势
    riskStatus: {
      highRiskVuln: 0,
      highRiskPort: 0,
      weakPassword: 0,
    },
    // 工单状态
    orderStatus: {
      total: 0,
      pending: 0,
      rate: 0,
    },
    // 告警列表
    warningList: [],
    // 风险趋势
    riskTrend: [],
    // SLA效率
    slaEfficiency: [],
  })

  // 图表实例
  const charts = {
    orderChart: null,
    trendChart: null,
    orderTypeChart: null,
    efficiencyChart: null,
  }
  // 计算属性
  const highRiskVulnCount = computed(() => {
    return screenData.value.warningList.filter((w) => w.kind === '高危漏洞').length
  })

  const highRiskPortCount = computed(() => {
    return screenData.value.warningList.filter((w) => w.kind === '高危端口').length
  })

  const weakPasswordCount = computed(() => {
    return screenData.value.warningList.filter((w) => w.kind === '弱口令').length
  })

  // 过滤显示的告警列表（可控制显示数量）
  const filteredWarnings = computed(() => {
    return screenData.value.warningList.slice(0, 5) // 显示前10条
  })

  const getWarningIcon = (kind) => {
    const iconMap = {
      高危漏洞: '⚠️',
      高危端口: '📡',
      弱口令: '🔒',
    }
    return iconMap[kind] || 'ℹ️'
  }

  const getStatusText = (status) => {
    if (status === 'ignored') return '已排除'
    if (status === 'await') return '待处置'
    if (status === 'valid') return '有效'
    if (status === 'invalid') return '无效'
    return status || '未处置'
  }
  // 在useScreenData hook中添加计算属性
  const maxRiskValue = computed(() => {
    const values = [
      screenData.value.riskStatus.highRiskVuln,
      screenData.value.riskStatus.highRiskPort,
      screenData.value.riskStatus.weakPassword,
    ]
    return Math.max(...values, 1) // 至少为1，避免除以0
  })
  // 获取数据
  const fetchData = async () => {
    try {
      const response = await screenDataApi.getInfo({})
      if (response.code === 200) {
        const data = response.data

        // 更新监控范围概览
        screenData.value.overview = {
          domain: data.rootDomainCount,
          ip: data.ipCount,
          port: data.portCount,
          app: data.webCount,
          backend: data.adminCount,
        }

        // 更新两高一弱态势
        screenData.value.riskStatus = {
          highRiskVuln: data.vulnCount,
          highRiskPort: data.riskServiceCount,
          weakPassword: data.weakPwdCount,
        }

        // 更新工单状态
        screenData.value.orderStatus = {
          total: data.orderFinishedCount + data.orderProcessingCount,
          pending: data.orderProcessingCount,
          rate: parseFloat(data.completedRate || 0).toFixed(2),
        }

        // 更新告警列表
        screenData.value.warningList = data.warningList

        // 更新风险趋势
        screenData.value.riskTrend = data.riskList

        // 更新SLA效率
        screenData.value.slaEfficiency = data.orderList

        // 初始化图表
        initCharts()
      }
    } catch (error) {
      console.error('获取大屏数据失败:', error)
    }
  }

  // 初始化工单状态饼图（优化版）
  const initOrderChart = () => {
    if (!charts.orderChart) {
      const chartDom = document.getElementById('orderChart')
      if (!chartDom) return
      charts.orderChart = echarts.init(chartDom)
    }

    const completedCount = screenData.value.orderStatus.total - screenData.value.orderStatus.pending
    const pendingCount = screenData.value.orderStatus.pending

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}',
      },
      legend: {
        show: false,
      },
      series: [
        {
          name: '工单状态',
          type: 'pie',
          radius: ['40%', '58%'], // 增大圆环半径
          center: ['50%', '40%'], // 完全居中
          avoidLabelOverlap: false,
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: true,
            position: 'outer', // 使用外部标签
            alignTo: 'edge',
            margin: 20, // 标签外边距
            formatter: '{b}\n{c}',
            color: '#19222f',
            fontSize: 12, // 减小字体
            fontWeight: 'bold',
          },
          labelLine: {
            show: true,
            length: 10,
            length2: 15,
            smooth: true,
          },
          emphasis: {
            scale: true,
            scaleSize: 5,
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
            },
          },
          data: [
            {
              value: completedCount,
              name: '已处置',
              itemStyle: {
                color: '#36c6d9',
              },
            },
            {
              value: pendingCount,
              name: '待处置',
              itemStyle: {
                color: '#f1c40f',
              },
            },
          ],
        },
      ],
    }

    charts.orderChart.setOption(option)
  }
  // 初始化风险趋势折线图
  const initTrendChart = () => {
    if (!charts.trendChart) {
      const chartDom = document.getElementById('trendChart')
      if (!chartDom) return
      charts.trendChart = echarts.init(chartDom)
    }

    const dates = screenData.value.riskTrend.map((item) => item.dateKey)
    const values = screenData.value.riskTrend.map((item) => item.value)

    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: '{b}<br/>风险值: {c}',
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLine: {
          lineStyle: {
            color: '#19222f',
          },
        },
        axisLabel: {
          color: '#19222f',
        },
      },
      yAxis: {
        type: 'value',
        axisLine: {
          lineStyle: {
            color: '#19222f',
          },
        },
        axisLabel: {
          color: '#19222f',
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.1)',
          },
        },
      },
      series: [
        {
          name: '风险值',
          type: 'line',
          smooth: true,
          lineStyle: {
            width: 3,
            color: '#19222f',
          },
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: {
            color: '#36c6d9',
            borderColor: '#fff',
            borderWidth: 2,
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(54, 198, 217, 0.3)' },
              { offset: 1, color: 'rgba(54, 198, 217, 0.1)' },
            ]),
          },
          data: values,
        },
      ],
    }

    charts.trendChart.setOption(option)
  }

  // 初始化工单类型占比饼图
  const initOrderTypeChart = () => {
    if (!charts.orderTypeChart) {
      const chartDom = document.getElementById('orderTypeChart')
      if (!chartDom) return
      charts.orderTypeChart = echarts.init(chartDom)
    }

    const orderTypeData = screenData.value.slaEfficiency

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: function (params) {
          const data = params.data
          return `${params.name}<br/>总数: ${data.count}个<br/>已完成: ${data.completedCount}个<br/>完成率: ${data.percent.toFixed(2)}%<br/>平均响应时长: ${data.averageResponseTime}小时<br/>平均处理时长: ${data.averageProcessTime}小时`
        },
      },
      legend: {
        show: false,
      },
      series: [
        {
          name: '工单类型',
          type: 'pie',
          radius: '95%',
          center: ['50%', '50%'],
          top: '30%',
          label: {
            show: true,
            formatter: '{b}\n{c}个', // 这里用 \n 换行
            color: '#19222f',
            fontSize: 14,
            lineHeight: 18, // 可以调整行高
          },
          labelLine: {
            show: true,
            length: 50, // 第一段线的长度
            length2: 70, // 第二段线的长度
            smooth: 0.8,
          },
          data: orderTypeData.map((item) => ({
            value: item.total,
            name: item.kindName,
            count: item.total,
            completedCount: item.completedCount,
            percent: item.completedRate,
            averageResponseTime: item.averageDuringTime,
            averageProcessTime: item.averageProcessTime,
            itemStyle: {
              color: getOrderTypeColor(item.kind),
            },
          })),
        },
      ],
    }

    charts.orderTypeChart.setOption(option) // 此行现在不会报错
  }
  // 工单类型颜色映射
  const getOrderTypeColor = (kind) => {
    const colorMap = {
      RiskCheck: '#964f394e',
      AssetConfirm: '#3498db',
      AssetCheck: '#f39c12',
      Report: '#1d89757c',
    }
    return colorMap[kind] || '#dc4e2bff'
  }
  const initEfficiencyChart = () => {
    if (!charts.efficiencyChart) {
      const chartDom = document.getElementById('efficiencyChart')
      if (!chartDom) return
      charts.efficiencyChart = echarts.init(chartDom)
    }

    const orderTypeData = screenData.value.slaEfficiency

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
        formatter: function (params) {
          const item = orderTypeData[params[0].dataIndex]
          return `
          <div style="text-align: left; padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 8px; color: #19222f;">${item.kindName}</div>
            <div style="margin-bottom: 4px;">工单总数: <span style="color: #05121eb4; font-weight: bold;">${item.total}个</span></div>
            <div style="margin-bottom: 4px;">已完成: <span style="color: #0b4d08db; font-weight: bold;">${item.completedCount}个</span></div>
            <div style="margin-bottom: 4px;">完成率: <span style="color: #61190eff; font-weight: bold;">${(item.completedRate * 100).toFixed(1)}%</span></div>
            <div style="color: #666; font-size: 12px;">平均处理: ${item.averageProcessTime}小时</div>
          </div>
        `
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: orderTypeData.map((item) => item.kindName),
        axisLine: {
          lineStyle: {
            color: '#19222f',
          },
        },
        axisLabel: {
          color: '#19222f',
          fontSize: 12,
          interval: 0,
          rotate: orderTypeData.length > 3 ? 30 : 0, // 如果类型多就旋转标签
        },
      },
      yAxis: [
        {
          type: 'value',
          name: '数量',
          nameTextStyle: {
            color: '#19222f',
          },
          axisLine: {
            lineStyle: {
              color: '#19222f',
            },
          },
          axisLabel: {
            color: '#19222f',
            formatter: '{value}',
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(255, 255, 255, 0.1)',
            },
          },
        },
        {
          type: 'value',
          name: '完成率%',
          nameTextStyle: {
            color: '#19222f',
          },
          min: 0,
          max: 100,
          axisLine: {
            lineStyle: {
              color: '#19222f',
            },
          },
          axisLabel: {
            color: '#19222f',
            formatter: '{value}%',
          },
          splitLine: {
            show: false,
          },
        },
      ],
      series: [
        {
          name: '工单总数',
          type: 'bar',
          barWidth: '40%',
          data: orderTypeData.map((item) => ({
            value: item.total,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(116, 150, 195, 0.9)' }, // 浅莫兰迪蓝
                { offset: 1, color: 'rgba(79, 114, 162, 0.8)' }, // 深莫兰迪蓝
              ]),
              borderRadius: [8, 8, 0, 0], // 圆角：左上、右上、右下、左下
              shadowColor: 'rgba(116, 150, 195, 0.3)', // 阴影颜色
              shadowBlur: 6, // 阴影模糊
              borderWidth: 0,
            },
          })),
          label: {
            show: true,
            position: 'top',
            color: '#19222f',
            fontSize: 12,
            formatter: '{c}',
          },
        },
        {
          name: '完成率',
          type: 'line',
          yAxisIndex: 1,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3,
            color: '#faad14',
          },
          itemStyle: {
            color: '#faad14',
            borderColor: '#fff',
            borderWidth: 2,
          },
          data: orderTypeData.map((item) => ({
            value: item.completedRate.toFixed(1),
            itemStyle: {
              color: '#faad14',
            },
          })),
          label: {
            show: true,
            position: 'top',
            color: '#faad14',
            fontSize: 12,
            fontWeight: 'bold',
            formatter: '{c}%',
          },
        },
      ],
    }

    charts.efficiencyChart.setOption(option)
  }
  // 初始化所有图表
  const initCharts = () => {
    initOrderChart()
    initTrendChart()
    //initOrderTypeChart()
    initEfficiencyChart()
  }

  const handleResize = () => {
    Object.values(charts).forEach((chart) => {
      if (chart) {
        chart.resize()
      }
    })
  }

  // 定时刷新
  let timer = null
  const startAutoRefresh = () => {
    timer = setInterval(fetchData, 30000) // 30秒刷新一次
  }

  // 组件挂载
  onMounted(() => {
    fetchData()
    startAutoRefresh()
    window.addEventListener('resize', handleResize)
  })

  // 组件卸载
  onUnmounted(() => {
    if (timer) {
      clearInterval(timer)
    }
    window.removeEventListener('resize', handleResize)
    Object.values(charts).forEach((chart) => {
      if (chart) {
        chart.dispose()
      }
    })
  })

  return {
    screenData,
    highRiskVulnCount,
    highRiskPortCount,
    weakPasswordCount,
    filteredWarnings,
    getWarningIcon,
    getStatusText,
    maxRiskValue,
  }
}
