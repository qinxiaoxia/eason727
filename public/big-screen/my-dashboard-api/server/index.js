const express = require('express');
const app = express();
const port = 3000;

// 模拟数据
const mockData = {
  attackRank: [
    { name: '攻击队1', value: 100 },
    { name: '攻击队2', value: 150 },
    { name: '攻击队3', value: 200 },
    { name: '攻击队4', value: 120 }
  ],
  provinceLoss: [
    { name: '山东', value: 5000 },
    { name: '上海', value: 3000 },
    { name: '广东', value: 7000 },
    { name: '黑龙江', value: 2000 },
    { name: '天津', value: 4000 },
    { name: '河北', value: 6000 },
    { name: '江西', value: 1000 },
    { name: '四川', value: 8000 }
  ],
  top20Attacks: [
    { name: 'www.ada.com', value: 702 },
    { name: 'www.ada.com', value: 350 },
    { name: 'www.ada.com', value: 610 },
    { name: 'www.ada.com', value: 793 },
    { name: 'www.ada.com', value: 664 },
    { name: 'www.ada.com', value: 777 },
    { name: 'www.ada.com', value: 999 },
    { name: 'www.ada.com', value: 666 },
    { name: 'www.ada.com', value: 555 },
    { name: 'www.ada.com', value: 444 }
  ]
};

// 允许跨域请求
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

// 提供攻击队排名数据
app.get('/api/attackRank', (req, res) => {
  res.json(mockData.attackRank);
});

// 提供省市失分数据
app.get('/api/provinceLoss', (req, res) => {
  res.json(mockData.provinceLoss);
});

// 提供被攻击次数TOP20数据
app.get('/api/top20Attacks', (req, res) => {
  res.json(mockData.top20Attacks);
});

app.listen(port, () => {
  console.log(`API server is running on http://localhost:${port}`);
});