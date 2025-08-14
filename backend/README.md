# 🛍️ 商品监控系统 - 后端API

智能商品库存监控API服务，支持多平台电商监控和邮件通知。

## 🚀 Railway部署

### 1. 快速部署

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

### 2. 手动部署

1. **连接GitHub仓库**
   ```bash
   # 推送后端代码到GitHub
   git subtree push --prefix=backend origin backend-main
   ```

2. **在Railway创建新项目**
   - 连接GitHub仓库的`backend`目录
   - Railway会自动检测Python项目并安装依赖

3. **配置环境变量**
   ```env
   OPENAI_API_KEY=your_openai_api_key
   SERPER_API_KEY=your_serper_api_key
   FRONTEND_URL=https://your-frontend.vercel.app
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ENVIRONMENT=production
   ```

4. **部署完成**
   - Railway会自动分配域名: `https://your-project.railway.app`
   - API文档: `https://your-project.railway.app/docs`

## 🔧 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动服务
python app.py
```

访问 http://localhost:8000/docs 查看API文档。

## 📡 API端点

### 核心功能
- `POST /api/add-monitor` - 添加监控任务
- `GET /api/monitors` - 获取监控列表
- `DELETE /api/monitors/{task_id}` - 删除监控任务

### 系统管理
- `GET /api/system/status` - 系统状态
- `POST /api/system/test-email` - 测试邮件
- `GET /health` - 健康检查

## 🗄️ 数据存储

- **开发环境**: SQLite (自动创建在`data/`目录)
- **生产环境**: 支持PostgreSQL (通过`DATABASE_URL`配置)

## 📧 邮件配置

支持主流邮件服务商：
- **Gmail**: `smtp.gmail.com:587`
- **QQ邮箱**: `smtp.qq.com:587` 
- **163邮箱**: `smtp.163.com:587`

## 🔒 安全配置

- **CORS**: 仅允许配置的前端域名访问
- **环境变量**: 敏感信息通过环境变量管理
- **错误处理**: 生产环境不暴露详细错误信息

## 📊 监控特性

- **定时任务**: 每5分钟自动检查库存状态
- **智能过滤**: OpenAI GPT过滤相关商品
- **状态追踪**: 仅在状态变化时发送通知
- **容错机制**: 自动重试和错误恢复

## 🚨 故障排除

### Railway部署问题
1. **构建失败**: 检查`requirements.txt`依赖版本
2. **启动失败**: 确认`PORT`环境变量配置
3. **数据库错误**: 检查SQLite文件权限

### API连接问题
1. **CORS错误**: 确认`FRONTEND_URL`配置正确
2. **超时**: 检查Railway容器状态和日志
3. **404错误**: 确认API端点路径正确

## 🔧 自定义配置

### 修改检查频率
```python
# 在scheduler.py中修改
self.check_interval = 300  # 秒为单位
```

### 添加新电商网站
1. 在`product_checker.py`添加网站检测规则
2. 更新`get_site_detector()`函数
3. 测试检测准确性

### 扩展数据库
```python
# 使用PostgreSQL
DATABASE_URL=postgresql://user:pass@host:port/db
```

## 📈 性能监控

Railway提供内置监控：
- **CPU使用率**
- **内存占用** 
- **响应时间**
- **错误率统计**

访问Railway项目面板查看详细指标。