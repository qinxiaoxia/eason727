// 等待页面加载完成
document.addEventListener("DOMContentLoaded", function () {
    // 获取 ECharts 实例
    const barRaceChart1 = echarts.init(document.getElementById("barRaceChart1"));
  
    // 假设这是 ECharts 的配置和数据
    const option = {
      xAxis: {
        type: "value",
      },
      yAxis: {
        type: "category",
        data: ["攻击队1", "攻击队2", "攻击队3","攻击队4"], // 攻击队名称
      },
      series: [
        {
          name: "攻击得分",
          type: "bar",
          data: [1200, 1100, 1000], // 攻击队的得分
        },
      ],
    };
  
    // 设置 ECharts 配置
    barRaceChart1.setOption(option);
  
    // 获取排名第一的队伍名称
    function updateTopAttacker() {
      // 获取 ECharts 实例中的数据
      const currentOption = barRaceChart1.getOption();
      const teamNames = currentOption.yAxis[0].data; // 攻击队名称
      const teamScores = currentOption.series[0].data; // 攻击队得分
  
      // 找到得分最高的队伍
      let maxScore = -1;
      let topTeam = "";
      teamScores.forEach((score, index) => {
        if (score > maxScore) {
          maxScore = score;
          topTeam = teamNames[index];
        }
      });
  
      // 更新“第一名攻击队”数据框
      document.getElementById("topAttacker").textContent = topTeam;
    }
  
    // 初始更新
    updateTopAttacker();
  
    // 监听 ECharts 数据变化（如果有动态更新）
    barRaceChart1.on("dataZoom", updateTopAttacker);
    barRaceChart1.on("legendselectchanged", updateTopAttacker);
  });