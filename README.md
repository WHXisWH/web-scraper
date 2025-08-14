# 🛍️ 商品监控系统

智能商品库存监控与邮件通知系统，支持Amazon、Louis Vuitton、楽天等电商平台。

## ✨ 主要功能

- **智能监控**：AI过滤相关商品，精准检测库存状态
- **实时通知**：邮件即时推送库存变化信息
- **极简界面**：黑白设计风格，操作简单直观
- **后台任务**：定时监控，自动检查库存状态
- **数据持久化**：SQLite存储，支持历史记录查询

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo>
cd web-scraper

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件
vim .env
```

**必需配置**：
- `OPENAI_API_KEY`: OpenAI API密钥（用于AI过滤）
- `SERPER_API_KEY`: Serper搜索API密钥

**邮件通知配置**（可选）：
- `EMAIL_USER`: 发件邮箱
- `EMAIL_PASSWORD`: 邮箱应用密码
- `SMTP_SERVER`: SMTP服务器

### 3. 启动应用

```bash
# 开发环境
python app.py

# 生产环境
uvicorn app:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000

## 📧 邮件服务配置

### Gmail 配置示例

1. 启用两步验证
2. 生成应用专用密码
3. 配置环境变量：

```env
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-16-digit-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 其他邮件服务

| 服务商 | SMTP服务器 | 端口 |
|--------|-----------|------|
| 163邮箱 | smtp.163.com | 587 |
| QQ邮箱 | smtp.qq.com | 587 |
| Outlook | smtp-mail.outlook.com | 587 |

## 🔧 API接口

### 添加监控任务
```http
POST /api/add-monitor
Content-Type: application/json

{
  "keyword": "iPhone 15 Pro Max",
  "target_sites": ["amazon.co.jp", "louisvuitton.com"],
  "notification_email": "user@example.com"
}
```

### 查看监控列表
```http
GET /api/monitors
```

### 删除监控任务
```http
DELETE /api/monitors/{task_id}
```

### 系统状态
```http
GET /api/system/status
```

## 📂 项目结构

```
web-scraper/
├── app.py                      # FastAPI主应用
├── requirements.txt            # 项目依赖
├── .env.example               # 环境变量示例
├── templates/
│   └── index.html             # 前端页面
├── static/
│   └── main.js                # 前端逻辑
├── backend_logic/
│   ├── database.py            # 数据库模型
│   ├── scheduler.py           # 定时任务调度
│   ├── email_service.py       # 邮件服务
│   ├── monitor_runner.py      # 监控执行器
│   ├── search_products.py     # 商品搜索
│   ├── ai_filter.py          # AI智能过滤
│   └── product_checker.py     # 商品检测
└── data/
    └── monitor.db             # SQLite数据库
```

## ⚙️ 配置说明

### 监控频率
- 默认每5分钟检查一次
- 可通过 `CHECK_INTERVAL` 环境变量调整

### 并发控制
- 默认最大5个并发任务
- 可通过 `MAX_WORKERS` 环境变量调整

### 数据库
- 默认使用SQLite存储在 `data/monitor.db`
- 支持PostgreSQL，通过 `DATABASE_URL` 配置

## 🎯 支持网站

- **Amazon Japan** (amazon.co.jp)
- **Louis Vuitton** (louisvuitton.com) 
- **楽天市場** (rakuten.co.jp)
- **其他网站**：通用检测逻辑

## 🔍 检测逻辑

### 库存状态检测
- 购买按钮可用性
- 库存文本识别
- 价格信息提取
- 页面完整性验证

### AI智能过滤
- 使用GPT过滤相关商品
- 避免误报和无关结果
- 支持中文、日文、英文

## 📊 监控流程

1. **关键词搜索** → Serper API搜索商品页面
2. **AI智能过滤** → GPT筛选相关商品
3. **库存检测** → 多维度检测可用性
4. **状态对比** → 检测库存变化
5. **邮件通知** → 即时推送变化信息

## 🚀 部署

### Railway部署

1. 连接GitHub仓库
2. 设置环境变量
3. 自动部署

### Docker部署

```bash
# 构建镜像
docker build -t product-monitor .

# 运行容器
docker run -d -p 8000:8000 --env-file .env product-monitor
```

## 🔧 故障排除

### 常见问题

1. **搜索无结果**
   - 检查SERPER_API_KEY配置
   - 确认关键词准确性

2. **邮件发送失败**
   - 验证邮箱配置
   - 检查应用密码

3. **库存检测不准确**
   - 网站反爬虫限制
   - 页面结构变化

### 日志查看

```bash
# 查看应用日志
tail -f app.log

# 调试模式运行
python app.py --log-level DEBUG
```

## 📝 开发

### 添加新网站支持

1. 在 `product_checker.py` 添加网站检测规则
2. 更新 `get_site_detector()` 函数
3. 测试检测准确性

### 自定义邮件模板

编辑 `email_service.py` 中的邮件模板函数。

## 📄 许可证

MIT License

## 🙏 致谢

- OpenAI GPT API
- Serper搜索API
- FastAPI框架
- SQLAlchemy ORM