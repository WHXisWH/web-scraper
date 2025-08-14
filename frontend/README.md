# 🛍️ 商品监控系统 - 前端

极简黑白设计的商品监控前端应用，部署在Vercel。

## 🚀 Vercel部署

### 1. 快速部署

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/product-monitor-frontend)

### 2. 手动部署步骤

1. **推送代码到GitHub**
   ```bash
   # 创建前端仓库
   git init
   git add .
   git commit -m "🎨 商品监控前端 - 极简黑白设计"
   git branch -M main
   git remote add origin https://github.com/yourusername/product-monitor-frontend.git
   git push -u origin main
   ```

2. **在Vercel创建项目**
   - 访问 [vercel.com](https://vercel.com)
   - 点击 "New Project"
   - 导入GitHub仓库
   - 选择 `frontend` 目录作为根目录

3. **配置环境变量**
   在Vercel项目设置中添加：
   ```env
   NODE_ENV=production
   ```

4. **配置后端API地址**
   在 `src/config.js` 中更新：
   ```javascript
   baseURL: 'https://your-backend.railway.app'
   ```

5. **部署完成**
   - Vercel自动分配域名: `https://your-project.vercel.app`
   - 支持自定义域名配置

## 🎨 设计特色

### 极简黑白风格
- **深色背景**: `#0a0a0a` 主背景色
- **纯白文字**: `#ffffff` 主要文本
- **灰色层次**: 多层次灰色营造层次感
- **无边框设计**: 圆角边框，现代感强

### 交互体验
- **直觉操作**: 单一垂直流程，无需学习
- **即时反馈**: 所有操作都有状态提示
- **响应式**: 完美支持手机和桌面端
- **API状态**: 实时显示后端连接状态

## 📱 本地开发

```bash
# 启动本地服务器
python -m http.server 3000
# 或使用Node.js
npx serve . -p 3000

# 访问
open http://localhost:3000
```

### 开发时配置API地址

1. **环境变量方式**:
   ```javascript
   window.API_BASE_URL = 'http://localhost:8000';
   ```

2. **URL参数方式**:
   ```
   http://localhost:3000?api=http://localhost:8000
   ```

## 🔧 核心功能

### 智能API配置
- 自动检测开发/生产环境
- 支持URL参数覆盖API地址
- 实时API状态检测和显示

### 本地存储
- 监控任务历史记录
- 用户偏好设置
- 离线数据缓存

### 错误处理
- 网络连接错误提示
- API超时自动重试
- 用户友好的错误信息

## 🎯 使用流程

1. **输入商品关键词**: 如"iPhone 15 Pro Max"
2. **选择监控网站**: Amazon、LV、楽天
3. **设置通知邮箱**: 接收库存变化通知
4. **开始监控**: 点击按钮即可启动
5. **查看结果**: 实时显示搜索和检测结果

## 🌐 浏览器支持

- **Chrome/Edge**: 完全支持
- **Firefox**: 完全支持  
- **Safari**: 完全支持
- **移动端**: iOS Safari, Android Chrome

## 🔒 安全特性

- **HTTPS部署**: Vercel自动配置SSL
- **CSP策略**: 内容安全策略防护
- **无敏感信息**: 前端不存储API密钥
- **CORS安全**: 仅与授权后端通信

## 📊 性能优化

- **静态部署**: 无服务器开销
- **CDN加速**: Vercel全球CDN
- **资源压缩**: 自动压缩CSS/JS
- **缓存策略**: 合理的缓存配置

## 🛠️ 自定义配置

### 修改主题色彩
```css
:root {
  --bg-primary: #0a0a0a;
  --text-primary: #ffffff;
  --accent-color: #00ff88;
}
```

### 添加新监控网站
在前端选项中添加新的网站选择框：
```html
<div class="site-option">
  <input type="checkbox" id="newsite" value="newsite.com">
  <label for="newsite" class="site-label">新网站</label>
</div>
```

### 自定义API超时时间
```javascript
// 在config.js中修改
timeout: 60000  // 60秒
```

## 🚨 故障排除

### Vercel部署问题
1. **构建失败**: 检查`vercel.json`配置
2. **404错误**: 确认路由配置正确
3. **CORS错误**: 检查后端CORS设置

### API连接问题  
1. **连接失败**: 检查后端API地址配置
2. **超时**: 调整`API_TIMEOUT`设置
3. **跨域**: 确认后端允许前端域名

## 📈 监控指标

Vercel提供的分析数据：
- **页面访问量**
- **加载性能**
- **错误率统计**
- **地理分布**

访问Vercel项目面板查看详细数据。