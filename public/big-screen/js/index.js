document.addEventListener("DOMContentLoaded", function () {
  // 初始化 ECharts 实例
  var provinceLossChart = echarts.init(document.getElementById('provinceLossChart'));

  // 生成随机数函数
  function getRandomValue(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
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
      { value: getRandomValue(0, 11000), name: '四川', itemStyle: { color: '#ffffff' } }
    ];
  }

  // 配置项
  var option = {
    legend: {
      top: 'bottom',
      textStyle: {
        color: '#fff' // 将图例文字颜色改为纯白色
      }
    },
    toolbox: {
      show: true,
      feature: {
        mark: { show: true },
        dataView: { show: true, readOnly: false },
        restore: { show: true },
        saveAsImage: { show: true }
      }
    },
    series: [
      {
        name: '省市失分',
        type: 'pie',
        radius: [0, '70%'], // 内半径为 0，外半径为 80%（充满容器）
        center: ['50%', '50%'], // 饼图中心位置
        roseType: 'area', // 南丁格尔图
        itemStyle: {
          borderRadius: 8 // 圆角
        },
        label: {
          formatter: '{b}: {c}', // 标签显示格式：名称 + 值
          align: 'center', // 文字对齐方式
          position: 'outer', // 标签位置：外部
          lineHeight: 16 // 行高
        },
        labelLine: {
          length: 1, // 第一段标注线长度（进一步缩短）
          length2: 1, // 第二段标注线长度
          lineStyle: {
            color: '#ccc' // 标注线颜色为灰色（默认）
          }
        },
        data: generateRandomData() // 初始数据
      }
    ]
  };

  // 使用配置项显示图表
  provinceLossChart.setOption(option);

  // 定时更新数据
  setInterval(function () {
    // 生成新的随机数据
    var newData = generateRandomData();
    // 更新饼图数据
    provinceLossChart.setOption({
      series: [{ data: newData }]
    });
    // 触发自定义事件，通知地图更新
    triggerPieDataUpdatedEvent(newData);
  }, 3000); // 每 3 秒更新一次数据

  // 监听窗口大小变化，自动调整图表大小
  window.addEventListener('resize', function () {
    provinceLossChart.resize();
  });

  // 触发自定义事件
  function triggerPieDataUpdatedEvent(data) {
    var event = new CustomEvent('pieDataUpdated', {
      detail: data // 将饼图数据作为事件参数传递
    });
    document.dispatchEvent(event);
  }
});

document.addEventListener("DOMContentLoaded", function() {
  // 初始化 ECharts 实例
  var myChart = echarts.init(document.getElementById('barRaceChart1'));

  // 示例数据（保留四个柱状图数据）
  var data = [100, 150, 200, 120]; // 初始数据
  var categories = ['攻击队1', '攻击队2', '攻击队3', '攻击队4']; // 柱状图标签

  // 定义纯色
  var colors = {
    '攻击队1': '#0B5FA9', // 纯色
    '攻击队2': '#088BFF', // 纯色
    '攻击队3': '#61B5FF', // 纯色
    '攻击队4': '#2CC6BD' // 纯色
  };

  // 示例配置项
  var option = {
    grid: {
      left: '20%', // 增加左侧空间，确保文字完整显示
      right: '10%',
      top: '10%',
      bottom: '10%'
    },
    xAxis: {
      max: 'dataMax',
      axisLabel: {
        show: false // 隐藏 X 轴上的数字
      },
      axisTick: {
        show: false // 隐藏 X 轴上的刻度线
      },
      axisLine: {
        show: false // 隐藏 X 轴线
      },
      splitLine: {
        show: false // 隐藏 X 轴的分隔线
      }
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
        overflow: 'break' // 如果文字过长，自动换行
      }
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
          color: '#fff' // 文字颜色设置为白色
        },
        itemStyle: {
          // 根据标签设置纯色
          color: function(params) {
            var category = categories[params.dataIndex];
            return colors[category]; // 直接返回纯色
          },
          // 设置圆角
          barBorderRadius: [0, 12, 12, 0] // 四个角的圆角半径（左上、右上、右下、左下）
        },
        barWidth: 24, // 将柱状图宽度调整为 24px（默认是 16px）
        barCategoryGap: '30%' // 将柱状图间距调整为 30%
      }
    ],
    animationDuration: 0,
    animationDurationUpdate: 3000,
    animationEasing: 'linear',
    animationEasingUpdate: 'linear'
  };

  // 动态更新数据并排序
  function run() {
    // 更新数据
    for (var i = 0; i < data.length; ++i) {
      if (Math.random() > 0.9) {
        data[i] += Math.round(Math.random() * 2000);
      } else {
        data[i] += Math.round(Math.random() * 200);
      }
    }

    // 对数据和标签进行排序（从高到低）
    var combined = categories.map((name, index) => {
      return { name: name, value: data[index] };
    });
    combined.sort((a, b) => b.value - a.value); // 按值从高到低排序

    // 更新排序后的数据和标签
    var sortedData = combined.map(item => item.value);
    var sortedCategories = combined.map(item => item.name);

    // 获取第一名数据
    var firstPlace = combined[0];

    // 更新其他数据框的内容
    var firstPlaceElement = document.getElementById('firstPlaceData');
    if (firstPlaceElement) {
      firstPlaceElement.textContent = `${firstPlace.name}`;
    }

    // 更新图表
    myChart.setOption({
      yAxis: {
        data: sortedCategories // 更新排序后的标签
      },
      series: [
        {
          data: sortedData, // 更新排序后的数据
          itemStyle: {
            // 根据排序后的标签重新设置纯色
            color: function(params) {
              var category = sortedCategories[params.dataIndex];
              return colors[category]; // 直接返回纯色
            },
            // 保持圆角设置
            barBorderRadius: [0, 12, 12, 0]
          }
        }
      ]
    });
  }

  // 初始运行
  setTimeout(function () {
    run();
  }, 0);

  // 定时更新（每 3 秒更新一次）
  setInterval(function () {
    run();
  }, 3000);

  // 使用配置项显示图表
  myChart.setOption(option);
});


document.addEventListener("DOMContentLoaded", function () {
  // 初始化 ECharts 实例
  var myChart = echarts.init(document.querySelector(".bar1 .chart"));

  // 初始数据
  var titlename = ["www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com","www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com", "www.ada.com"];
  var valdata = [702, 350, 610, 793, 664, 777, 999, 666, 555, 444,702, 350, 610, 793, 664, 777, 999, 666, 555, 444];
  var myColor = ["#1089E7", "#F57474", "#56D0E3", "#F8B448", "#8B78F6","#1089E7", "#F57474", "#56D0E3", "#F8B448", "#8B78F6","#1089E7", "#F57474", "#56D0E3", "#F8B448", "#8B78F6","#1089E7", "#F57474", "#56D0E3", "#F8B448", "#8B78F6"];

  // 配置项
  var option = {
    grid: {
      top: "1%",
      left: "10%", // 调整左边距，使图表更紧凑
      bottom: "1%"
    },
    xAxis: {
      show: false // 隐藏 X 轴
    },
    yAxis: [
      {
        show: false, // 隐藏左边的 yAxis
        data: titlename,
        inverse: true,
        axisLine: {
          show: false
        },
        splitLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: "#fff",
          rich: {
            lg: {
              backgroundColor: "#339911",
              color: "#fff",
              borderRadius: 15,
              align: "center",
              width: 15,
              height: 15
            }
          }
        }
      },
      {
        show: true,
        inverse: true,
        data: valdata,
        axisLabel: {
          textStyle: {
            fontSize: 12,
            color: "#fff"
          }
        }
      }
    ],
    series: [
      {
        name: "条",
        type: "bar",
        yAxisIndex: 0,
        data: valdata,
        barCategoryGap: 50,
        barWidth: 24,
        barMinHeight: '50%', // 设置柱状图最小高度为 50%
        itemStyle: {
          normal: {
            barBorderRadius: 20,
            color: function (params) {
              return myColor[params.dataIndex % myColor.length];
            }
          }
        },
        label: {
          normal: {
            show: true,
            position: "inside", // 将 titlename 放在柱状图内部
            formatter: function (params) {
              return titlename[params.dataIndex]; // 显示 titlename
            },
            color: "#fff", // 文字颜色
            fontSize: 14 // 文字大小
          }
        }
      }
    ]
  };

  // 初始化图表
  myChart.setOption(option);

  // 动态更新数据
  setInterval(function () {
    // 随机更新数据
    valdata = valdata.map(function (value) {
      return value + Math.floor(Math.random() * 50 - 25); // 随机增减分值
    });

    // 对数据排序
    var sortedData = titlename
      .map(function (name, index) {
        return { name: name, value: valdata[index] };
      })
      .sort(function (a, b) {
        return b.value - a.value; // 按分值从高到低排序
      });

    // 更新 titlename 和 valdata
    titlename = sortedData.map(function (item) {
      return item.name;
    });
    valdata = sortedData.map(function (item) {
      return item.value;
    });

    // 更新图表
    myChart.setOption({
      yAxis: [
        {
          data: titlename
        },
        {
          data: valdata
        }
      ],
      series: [
        {
          data: valdata,
          label: {
            normal: {
              formatter: function (params) {
                return titlename[params.dataIndex]; // 更新 titlename 显示
              }
            }
          }
        }
      ]
    });
  }, 3000); // 每 3 秒更新一次

  // 窗口缩放时调整图表大小
  window.addEventListener("resize", function () {
    myChart.resize();
  });
});


