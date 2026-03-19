# SupSub 托管接入 rss-wechat-pusher 指南

你已注册 SupSub，可按以下步骤完成托管并接入 rss-wechat-pusher，实现公众号/网站内容推送到企业微信。

---

## 一、在 SupSub 中添加订阅

### 1. 登录 SupSub

访问 [https://supsub.net/login](https://supsub.net/login) 登录你的账号。

### 2. 添加公众号订阅

1. 进入 **发现** 页：<https://supsub.net/explore>
2. 选择 **公众号** 标签
3. 在搜索框输入公众号名称或 ID
4. 找到目标公众号后，点击 **订阅** 或 **添加订阅**

### 3. 添加网站订阅（可选）

1. 同样在 **发现** 页
2. 选择 **网站** 标签
3. 输入网站 URL 或关键词
4. 添加你想订阅的网站

### 4. 管理订阅

- **我的订阅**：<https://supsub.net/subscriptions> 查看和管理已订阅内容
- **关注点**：<https://supsub.net/focus> 可创建关注点，筛选你关心的主题

---

## 二、获取 SupSub 的 RSS 订阅地址

SupSub 支持 RSS / Atom / JSON 格式输出，需要拿到你的**个人订阅地址**才能接入 rss-wechat-pusher。

### 常见获取方式

1. **我的订阅页**  
   在 [我的订阅](https://supsub.net/subscriptions) 页面，查找是否有：
   - 「订阅地址」「RSS 链接」「导出」等入口
   - 或每个订阅源旁的 RSS 图标/链接

2. **设置 / 账户页**  
   进入个人设置或账户中心，查看是否有：
   - 「Feed 地址」「订阅链接」「API / 导出」等选项

3. **关注点页**  
   若使用关注点，可能在 [关注点](https://supsub.net/focus) 页面有对应 RSS 链接

### SupSub RSS 地址格式

全部订阅的 RSS 地址格式为：

```
https://supsub.net/feed/{你的用户ID}/subscriptions/all/rss
```

例如：`https://supsub.net/feed/118f04b5-0c4b-4a3c-a139-73f582358aa1/subscriptions/all/rss`

- 用户 ID 可在 SupSub 的「我的订阅」或设置页获取
- 也支持 `/atom` 或 `/json` 后缀

---

## 三、接入 rss-wechat-pusher

拿到 SupSub 的 RSS 地址后，按下面步骤配置。

### 1. 确定 source_type

- **公众号来源**：用 `wewe_rss`（会走公众号规则分类、监管预警等）
- **网站 / 普通 RSS**：用 `rss`

SupSub 的公众号订阅建议使用 `wewe_rss`。

### 2. 配置 FEEDS_JSON

在 **GitHub Secrets** 或 **Zeabur 环境变量** 中设置 `FEEDS_JSON`，格式为 JSON 数组：

```json
[
  ["你的SupSub_RSS地址", "wewe_rss"],
  ["https://www.freebuf.com/feed", "rss"]
]
```

**示例**（使用你的 SupSub 地址）：

```json
[
  ["https://supsub.net/feed/118f04b5-0c4b-4a3c-a139-73f582358aa1/subscriptions/all/rss", "wewe_rss"],
  ["https://www.freebuf.com/feed", "rss"]
]
```

### 3. 本地 config.py（可选）

若本地调试，可在 `config.py` 中写死：

```python
FEEDS = [
    ("https://你的SupSub地址", "wewe_rss"),
    ("https://www.freebuf.com/feed", "rss"),
]
```

### 4. 验证

1. 保存配置后，触发一次 GitHub Actions 或 Zeabur 部署
2. 或本地运行：`python main.py --push-now`
3. 检查企业微信群是否收到推送

---

## 四、SupSub vs WeWe RSS 对比

| 项目       | SupSub                    | WeWe RSS              |
|------------|---------------------------|------------------------|
| 托管方式   | 云端托管，无需自建        | 需自建（如 Zeabur）   |
| 公众号订阅 | 支持                       | 支持                   |
| 网站订阅   | 支持                       | 需额外 RSS 源          |
| AI 摘要    | 内置                       | 无                     |
| 费用       | 月付 ¥10 / 年付 ¥100      | 自建成本               |
| RSS 输出   | RSS / Atom / JSON          | Atom / RSS             |

两者可同时使用：在 `FEEDS_JSON` 中同时加入 SupSub 和 WeWe RSS 的地址即可。

---

## 五、常见问题

**Q：SupSub 订阅地址找不到？**  
A：在「我的订阅」「设置」「关注点」等页面仔细查找 RSS/导出入口；或联系 SupSub 官方/作者确认。

**Q：SupSub 和 WeWe RSS 可以一起用吗？**  
A：可以。在 `FEEDS_JSON` 中分别添加两者的 URL，rss-wechat-pusher 会合并拉取并去重。

**Q：SupSub 的公众号用 wewe_rss 还是 rss？**  
A：建议用 `wewe_rss`，以便走公众号相关规则（监管预警、重大事件等）。

---

## 六、下一步

1. 在 SupSub 完成订阅并拿到 RSS 地址  
2. 将地址加入 `FEEDS_JSON`  
3. 触发部署或本地测试  
4. 在企业微信群确认推送是否正常  

如有问题，可参考项目内 `入门指南.md` 和 `GitHub-Actions部署指南.md`。
