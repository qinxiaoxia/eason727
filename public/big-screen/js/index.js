/* eslint-disable no-undef */

// 全局函数：加载大屏数据
function loadDashboardData() {
  if (window.dashboardAPI && window.dashboardAPI.getData) {
    window.dashboardAPI
      .getData()
      .then(function (res) {
        if (res && res.code === 200 && res.data) {
          var data = res.data

          // 1. 更新顶部数据 - 被攻击总次数
          var totalLi = document.querySelector('.no-hd ul li:first-child')
          if (totalLi && data.totalAttacks !== undefined) {
            totalLi.textContent = data.totalAttacks
          }

          // 2. 更新顶部数据 - 第一名攻击队
          if (data.attackRank && data.attackRank.length > 0) {
            var firstPlaceLi = document.getElementById('firstPlaceData')
            if (firstPlaceLi) {
              firstPlaceLi.textContent = data.attackRank[0].name || '暂无'
            }
          }

          // 3. 触发自定义事件通知各图表更新
          if (data.attackRank) {
            var attackRankEvent = new CustomEvent('attackRankUpdated', { detail: data.attackRank })
            document.dispatchEvent(attackRankEvent)
          }

          if (data.provinceLoss) {
            var provinceEvent = new CustomEvent('provinceLossUpdated', {
              detail: data.provinceLoss,
            })
            document.dispatchEvent(provinceEvent)
          }

          if (data.top20Attacks) {
            var top20Event = new CustomEvent('top20AttacksUpdated', { detail: data.top20Attacks })
            document.dispatchEvent(top20Event)
          }

          console.log('大屏数据加载成功:', data)
        }
      })
      .catch(function (err) {
        console.error('加载大屏数据失败:', err)
      })
  }
}

document.addEventListener('DOMContentLoaded', function () {
  // 页面加载后等待1秒让dashboardApi加载，然后获取数据
  setTimeout(loadDashboardData, 1000)

  // 初始化 ECharts 实例
  var provinceLossChart = echarts.init(document.getElementById('provinceLossChart'))

  // 生成随机数函数
  function getRandomValue(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min
  }

  // 生成随机数据
  function generateRandomData() {
    return [
      { value: getRandomValue(0, 11000), name: '山东', itemStyle: { color: '#0B5FA9' } },
      { value: getRandomValue(0, 11000), name: '上海', itemStyle: { color: '#088BFF' } },
      { value: getRandomValue(0, 11000), name: '广东', itemStyle: { color: '#61B5FF' } },
      { value: getRandomValue(0, 11000), name: '黑龙江', itemStyle: { color: '#BADFFF' } },
      { value: getRandomValue(0, 11000), name: '天津', itemStyle: { color: '#2CC6BD' } },
      { value: getRandomValue(0, 11000), name: '河北', itemStyle: { color: '#35FFF4' } },
      { value: getRandomValue(0, 11000), name: '江西', itemStyle: { color: '#C7FFFC' } },
      { value: getRandomValue(0, 11000), name: '四川', itemStyle: { color: '#ffffff' } },
    ]
  }

  // 配置项
  var option = {
    legend: {
      top: 'bottom',
      textStyle: {
        color: '#fff', // 将图例文字颜色改为纯白色
      },
    },
    toolbox: {
      show: true,
      feature: {
        mark: { show: true },
        dataView: { show: true, readOnly: false },
        restore: { show: true },
        saveAsImage: { show: true },
      },
    },
    series: [
      {
        name: '省市失分',
        type: 'pie',
        radius: [0, '70%'], // 内半径为 0，外半径为 80%（充满容器）
        center: ['50%', '50%'], // 饼图中心位置
        roseType: 'area', // 南丁格尔图
        itemStyle: {
          borderRadius: 8, // 圆角
        },
        label: {
          formatter: '{b}: {c}', // 标签显示格式：名称 + 值
          align: 'center', // 文字对齐方式
          position: 'outer', // 标签位置：外部
          lineHeight: 16, // 行高
        },
        labelLine: {
          length: 1, // 第一段标注线长度（进一步缩短）
          length2: 1, // 第二段标注线长度
          lineStyle: {
            color: '#ccc', // 标注线颜色为灰色（默认）
          },
        },
        data: generateRandomData(), // 初始数据
      },
    ],
  }

  // 使用配置项显示图表
  provinceLossChart.setOption(option)

  // 定时更新数据（注释掉，使用真实接口数据）
  // setInterval(function () {
  //   var newData = generateRandomData()
  //   provinceLossChart.setOption({
  //     series: [{ data: newData }],
  //   })
  //   triggerPieDataUpdatedEvent(newData)
  // }, 3000)

  // 监听窗口大小变化，自动调整图表大小
  window.addEventListener('resize', function () {
    provinceLossChart.resize()
  })

  // 监听省份失分数据更新
  document.addEventListener('provinceLossUpdated', function (event) {
    var provinceData = event.detail
    if (provinceData && provinceData.length > 0) {
      var formattedData = provinceData.map(function (item, index) {
        return {
          name: item.name,
          value: item.value,
          itemStyle: {
            color: [
              '#0B5FA9',
              '#088BFF',
              '#61B5FF',
              '#BADFFF',
              '#2CC6BD',
              '#35FFF4',
              '#C7FFFC',
              '#ffffff',
            ][index % 8],
          },
        }
      })
      provinceLossChart.setOption({
        series: [{ data: formattedData }],
      })
      triggerPieDataUpdatedEvent(formattedData)
    }
  })

  // 触发自定义事件
  function triggerPieDataUpdatedEvent(data) {
    var event = new CustomEvent('pieDataUpdated', {
      detail: data, // 将饼图数据作为事件参数传递
    })
    document.dispatchEvent(event)
  }
})

document.addEventListener('DOMContentLoaded', function () {
  // 初始化 ECharts 实例
  var myChart = echarts.init(document.getElementById('barRaceChart1'))

  // 示例数据（保留四个柱状图数据）
  var data = [100, 150, 200, 120] // 初始数据
  var categories = ['攻击队1', '攻击队2', '攻击队3', '攻击队4'] // 柱状图标签

  // 定义纯色
  var colors = {
    攻击队1: '#0B5FA9', // 纯色
    攻击队2: '#088BFF', // 纯色
    攻击队3: '#61B5FF', // 纯色
    攻击队4: '#2CC6BD', // 纯色
  }

  // 示例配置项
  var option = {
    grid: {
      left: '20%', // 增加左侧空间，确保文字完整显示
      right: '10%',
      top: '10%',
      bottom: '10%',
    },
    xAxis: {
      max: 'dataMax',
      axisLabel: {
        show: false, // 隐藏 X 轴上的数字
      },
      axisTick: {
        show: false, // 隐藏 X 轴上的刻度线
      },
      axisLine: {
        show: false, // 隐藏 X 轴线
      },
      splitLine: {
        show: false, // 隐藏 X 轴的分隔线
      },
    },
    yAxis: {
      type: 'category',
      data: categories, // 保留四个柱状图
      inverse: true,
      animationDuration: 300,
      animationDurationUpdate: 300,
      max: 3, // 只显示四个柱状图
      axisLabel: {
        color: '#fff', // 文字颜色设置为白色
        width: 120, // 设置宽度，确保文字完整显示
        overflow: 'break', // 如果文字过长，自动换行
      },
    },
    series: [
      {
        realtimeSort: true,
        type: 'bar',
        data: data,
        label: {
          show: true,
          position: 'right',
          valueAnimation: true,
          color: '#fff', // 文字颜色设置为白色
        },
        itemStyle: {
          // 根据标签设置纯色
          color: function (params) {
            var category = categories[params.dataIndex]
            return colors[category] // 直接返回纯色
          },
          // 设置圆角
          barBorderRadius: [0, 12, 12, 0], // 四个角的圆角半径（左上、右上、右下、左下）
        },
        barWidth: 24, // 将柱状图宽度调整为 24px（默认是 16px）
        barCategoryGap: '30%', // 将柱状图间距调整为 30%
      },
    ],
    animationDuration: 0,
    animationDurationUpdate: 3000,
    animationEasing: 'linear',
    animationEasingUpdate: 'linear',
  }

  // 动态更新数据并排序
  function run() {
    // 更新数据
    for (var i = 0; i < data.length; ++i) {
      if (Math.random() > 0.9) {
        data[i] += Math.round(Math.random() * 2000)
      } else {
        data[i] += Math.round(Math.random() * 200)
      }
    }

    // 对数据和标签进行排序（从高到低）
    var combined = categories.map((name, index) => {
      return { name: name, value: data[index] }
    })
    combined.sort((a, b) => b.value - a.value) // 按值从高到低排序

    // 更新排序后的数据和标签
    var sortedData = combined.map((item) => item.value)
    var sortedCategories = combined.map((item) => item.name)

    // 获取第一名数据
    var firstPlace = combined[0]

    // 更新其他数据框的内容
    var firstPlaceElement = document.getElementById('firstPlaceData')
    if (firstPlaceElement) {
      firstPlaceElement.textContent = `${firstPlace.name}`
    }

    // 更新图表
    myChart.setOption({
      yAxis: {
        data: sortedCategories, // 更新排序后的标签
      },
      series: [
        {
          data: sortedData, // 更新排序后的数据
          itemStyle: {
            // 根据排序后的标签重新设置纯色
            color: function (params) {
              var category = sortedCategories[params.dataIndex]
              return colors[category] // 直接返回纯色
            },
            // 保持圆角设置
            barBorderRadius: [0, 12, 12, 0],
          },
        },
      ],
    })
  }

  // 初始运行（注释掉，使用真实接口数据）
  // setTimeout(function () {
  //   run()
  // }, 0)

  // 定时更新（每 3 秒更新一次，注释掉，使用真实接口数据）
  // setInterval(function () {
  //   run()
  // }, 3000)

  // 使用配置项显示图表
  myChart.setOption(option)
})

document.addEventListener('DOMContentLoaded', function () {
  // 初始化 ECharts 实例
  var myChart = echarts.init(document.querySelector('.bar1 .chart'))

  // 初始数据
  var titlename = [
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
    'www.ada.com',
  ]
  var valdata = [
    702, 350, 610, 793, 664, 777, 999, 666, 555, 444, 702, 350, 610, 793, 664, 777, 999, 666, 555,
    444,
  ]
  var myColor = [
    '#1089E7',
    '#F57474',
    '#56D0E3',
    '#F8B448',
    '#8B78F6',
    '#1089E7',
    '#F57474',
    '#56D0E3',
    '#F8B448',
    '#8B78F6',
    '#1089E7',
    '#F57474',
    '#56D0E3',
    '#F8B448',
    '#8B78F6',
    '#1089E7',
    '#F57474',
    '#56D0E3',
    '#F8B448',
    '#8B78F6',
  ]

  // 配置项 - 优化左对齐
  var option = {
    grid: {
      top: '2%',
      left: '2%',
      right: '15%',
      bottom: '2%',
      containLabel: false,
    },
    xAxis: {
      show: false,
      max: 'dataMax',
    },
    yAxis: [
      {
        show: false,
        data: titlename,
        inverse: true,
      },
      {
        show: true,
        type: 'category',
        data: valdata,
        inverse: true,
        axisLine: { show: false },
        splitLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#fff',
          fontSize: 11,
        },
        position: 'right',
      },
    ],
    series: [
      {
        name: '条',
        type: 'bar',
        data: valdata,
        barCategoryGap: 15,
        barWidth: 22,
        barMinHeight: 18,
        itemStyle: {
          normal: {
            barBorderRadius: [0, 10, 10, 0],
            color: function (params) {
              return myColor[params.dataIndex % myColor.length]
            },
          },
        },
        label: {
          normal: {
            show: true,
            position: 'inside',
            align: 'left',
            formatter: function (params) {
              return titlename[params.dataIndex]
            },
            color: '#fff',
            fontSize: 11,
            padding: [0, 0, 0, 8],
          },
        },
      },
    ],
  }

  // 初始化图表
  myChart.setOption(option)

  // 动态更新数据（注释掉，使用真实接口数据）
  // setInterval(function () {
  //   valdata = valdata.map(function (value) {
  //     return value + Math.floor(Math.random() * 50 - 25)
  //   })
  //   var sortedData = titlename
  //     .map(function (name, index) {
  //       return { name: name, value: valdata[index] }
  //     })
  //     .sort(function (a, b) {
  //       return b.value - a.value
  //     })
  //   titlename = sortedData.map(function (item) { return item.name })
  //   valdata = sortedData.map(function (item) { return item.value })
  //   myChart.setOption({
  //     yAxis: [{ data: titlename }, { data: valdata }],
  //     series: [{ data: valdata, label: {...} }]
  //   })
  // }, 3000)

  // 窗口缩放时调整图表大小
  window.addEventListener('resize', function () {
    myChart.resize()
  })

  // 监听攻击队排名数据更新
  document.addEventListener('attackRankUpdated', function (event) {
    var rankData = event.detail
    if (rankData && rankData.length > 0) {
      var categories = rankData.slice(0, 4).map(function (item) {
        return item.name
      })
      var values = rankData.slice(0, 4).map(function (item) {
        return item.value
      })
      myChart.setOption({
        yAxis: [{ data: categories }],
        series: [{ data: values }],
      })
    }
  })

  // 监听Top20攻击目标数据更新
  document.addEventListener('top20AttacksUpdated', function (event) {
    var top20Data = event.detail
    if (top20Data && top20Data.length > 0) {
      var top20List = top20Data.slice(0, 20)
      var titles = top20List.map(function (item) {
        return item.name
      })
      var values = top20List.map(function (item) {
        return item.value
      })

      myChart.setOption({
        yAxis: [{ data: titles }],
        series: [
          {
            data: values,
            label: {
              normal: {
                show: true,
                position: 'inside',
                align: 'left',
                formatter: function (params) {
                  return titles[params.dataIndex]
                },
                color: '#fff',
                fontSize: 11,
                padding: [0, 0, 0, 8],
              },
            },
          },
        ],
      })
    }
  })
})
