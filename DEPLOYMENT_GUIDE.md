# 🚀 前后端分离部署指南

## 📋 架构概览

```
[用户] → [Vercel前端] → [Railway后端API]
         静态网站        FastAPI服务
```

---

## 🔧 后端部署 (Railway)

### 1. 准备后端代码

```bash
# 进入后端目录
cd backend

# 查看文件结构
backend/
├── app.py              # FastAPI主应用 (已配置CORS)
├── backend_logic/      # 业务逻辑模块
├── requirements.txt    # 依赖列表
├── railway.json        # Railway配置
├── Procfile           # 启动命令
├── .env.example       # 环境变量示例
└── README.md          # 后端说明文档
```

### 2. Railway部署步骤

1. **创建GitHub仓库**
   ```bash
   cd backend
   git init
   git add .
   git commit -m "🚀 商品监控API后端"
   git remote add origin https://github.com/yourusername/product-monitor-backend.git
   git push -u origin main
   ```

2. **在Railway部署**
   - 访问 [railway.app](https://railway.app)
   - 点击 "New Project" → "Deploy from GitHub repo"
   - 选择后端仓库
   - Railway自动检测Python项目并部署

3. **配置环境变量**
   在Railway项目设置中添加：
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   FRONTEND_URL=https://your-frontend.vercel.app
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ENVIRONMENT=production
   ```

4. **获取后端域名**
   - Railway自动分配: `https://your-project.railway.app`
   - API文档: `https://your-project.railway.app/docs`

---

## 🎨 前端部署 (Vercel)

### 1. 准备前端代码

```bash
# 查看前端文件结构
frontend/
├── index.html          # 主页面
├── src/
│   ├── app.js         # 前端逻辑 (已配置API调用)
│   ├── config.js      # API配置管理
│   └── styles.css     # 极简黑白样式
├── package.json       # 项目配置
├── vercel.json        # Vercel配置
└── README.md          # 前端说明文档
```

### 2. Vercel部署步骤

1. **创建GitHub仓库**
   ```bash
   cd frontend
   git init
   git add .
   git commit -m "🎨 商品监控前端 - 极简黑白设计"
   git remote add origin https://github.com/yourusername/product-monitor-frontend.git
   git push -u origin main
   ```

2. **在Vercel部署**
   - 访问 [vercel.com](https://vercel.com)
   - 点击 "New Project" → "Import Git Repository"
   - 选择前端仓库
   - Vercel自动检测静态网站并部署

3. **配置后端API地址**
   编辑 `src/config.js`：
   ```javascript
   production: {
     baseURL: 'https://your-backend.railway.app', // 替换为Railway域名
     timeout: 60000
   }
   ```

4. **重新部署**
   - 提交配置更改后Vercel自动重新部署
   - 获取前端域名: `https://your-project.vercel.app`

---

## 🔗 连接前后端

### 1. 更新后端CORS配置

在Railway后端环境变量中设置：
```env
FRONTEND_URL=https://your-frontend.vercel.app
```

### 2. 测试连接

访问前端网站，检查：
- ✅ 页面正常加载
- ✅ API状态显示为"🟢 API在线"
- ✅ 可以添加监控任务
- ✅ 系统状态正常显示

---

## 🧪 部署验证清单

### 后端API (Railway)
- [ ] `/` 返回API信息
- [ ] `/health` 返回healthy状态
- [ ] `/docs` API文档可访问
- [ ] `/api/system/status` 系统状态正常
- [ ] CORS正确配置，允许前端域名

### 前端网站 (Vercel)
- [ ] 页面正常加载，样式正确
- [ ] API状态指示器显示在线
- [ ] 表单提交功能正常
- [ ] 监控列表正常显示
- [ ] 响应式设计在移动端正常

### 功能测试
- [ ] 搜索框输入关键词
- [ ] 网站选择功能正常
- [ ] 邮箱输入可选
- [ ] 提交后显示处理状态
- [ ] 监控任务保存到本地存储

---

## 🚨 常见问题排除

### CORS错误
```
Access to fetch at 'https://backend.railway.app/api/...' from origin 'https://frontend.vercel.app' has been blocked by CORS policy
```
**解决**: 检查后端`FRONTEND_URL`环境变量是否正确配置

### API连接失败
```
TypeError: Failed to fetch
```
**解决**: 
1. 确认后端Railway服务正常运行
2. 检查前端`config.js`中API地址是否正确
3. 尝试直接访问后端API文档页面

### 部署失败
**Railway后端**:
- 检查`requirements.txt`依赖版本
- 确认Python版本兼容性
- 查看Railway构建日志

**Vercel前端**:
- 检查`vercel.json`配置格式
- 确认静态文件路径正确
- 查看Vercel构建日志

---

## 📊 部署后监控

### Railway后端监控
- CPU使用率 < 50%
- 内存使用 < 512MB
- 响应时间 < 2秒
- 错误率 < 1%

### Vercel前端监控
- 页面加载时间 < 3秒
- Core Web Vitals 评分 > 90
- 错误率 < 0.1%

---

## 🎉 部署完成！

恭喜！您已成功将商品监控系统部署为前后端分离架构：

- 🎨 **前端**: `https://your-project.vercel.app`
- 🔧 **后端**: `https://your-project.railway.app`
- 📚 **API文档**: `https://your-project.railway.app/docs`

现在用户可以通过前端网站使用商品监控功能，系统会自动调用后端API进行商品搜索、AI过滤、库存检测和邮件通知！