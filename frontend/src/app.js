// 加载配置
document.head.appendChild(Object.assign(document.createElement('script'), {
    src: 'src/config.js'
}));

class MonitorApp {
    constructor() {
        this.monitorTasks = JSON.parse(localStorage.getItem('monitorTasks') || '[]');
        this.apiStatus = 'unknown';
        this.init();
    }
    
    init() {
        this.checkApiStatus();
        this.updateMonitorList();
        this.bindEvents();
        this.createApiStatusIndicator();
    }
    
    bindEvents() {
        // 回车键快捷提交
        document.getElementById('keyword').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.startMonitoring();
            }
        });
        
        // 页面可见性变化时重新检查API状态
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkApiStatus();
            }
        });
    }
    
    createApiStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'apiStatusIndicator';
        indicator.className = 'api-status offline';
        indicator.textContent = '连接中...';
        document.body.appendChild(indicator);
    }
    
    updateApiStatus(status) {
        const indicator = document.getElementById('apiStatusIndicator');
        if (indicator) {
            this.apiStatus = status;
            if (status === 'online') {
                indicator.className = 'api-status online';
                indicator.textContent = '🟢 API在线';
            } else {
                indicator.className = 'api-status offline';
                indicator.textContent = '🔴 API离线';
            }
        }
    }
    
    async checkApiStatus() {
        try {
            const response = await this.apiRequest('/health', { method: 'GET' }, 5000);
            if (response.status === 'healthy') {
                this.updateApiStatus('online');
                return true;
            }
        } catch (error) {
            console.error('API状态检查失败:', error);
        }
        this.updateApiStatus('offline');
        return false;
    }
    
    async apiRequest(endpoint, options = {}, timeout = null) {
        const url = `${window.API_BASE_URL}${endpoint}`;
        const requestTimeout = timeout || window.API_TIMEOUT || 30000;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), requestTimeout);
        
        try {
            const response = await fetch(url, {
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('请求超时');
            }
            throw error;
        }
    }
    
    updateMonitorList() {
        const listContainer = document.getElementById('monitorList');
        
        if (this.monitorTasks.length === 0) {
            listContainer.innerHTML = '<div class="empty-state">暂无监控任务</div>';
            return;
        }
        
        listContainer.innerHTML = this.monitorTasks.map((task, index) => `
            <div class="monitor-item">
                <div>
                    <div class="monitor-keyword">${task.keyword}</div>
                    <div class="monitor-time">
                        ${task.sites ? task.sites.join(' · ') : 'Amazon · Louis Vuitton'}
                    </div>
                    <div class="monitor-time">
                        ${new Date(task.timestamp * 1000).toLocaleString()}
                    </div>
                </div>
                <button class="delete-btn" onclick="app.removeMonitor(${index})">删除</button>
            </div>
        `).join('');
    }
    
    removeMonitor(index) {
        this.monitorTasks.splice(index, 1);
        localStorage.setItem('monitorTasks', JSON.stringify(this.monitorTasks));
        this.updateMonitorList();
    }
    
    async startMonitoring() {
        const keyword = document.getElementById('keyword').value.trim();
        const email = document.getElementById('email').value.trim();
        
        if (!keyword) {
            this.showStatus('请输入商品关键词', 'error');
            return;
        }
        
        // 获取选中的网站
        const selectedSites = Array.from(
            document.querySelectorAll('.site-checkbox:checked')
        ).map(cb => cb.value);
        
        if (selectedSites.length === 0) {
            this.showStatus('请选择至少一个监控网站', 'error');
            return;
        }
        
        // 检查API状态
        if (this.apiStatus === 'offline') {
            const isOnline = await this.checkApiStatus();
            if (!isOnline) {
                this.showStatus('后端API不可用，请检查网络连接或稍后重试', 'error');
                return;
            }
        }
        
        const button = document.getElementById('startBtn');
        button.disabled = true;
        button.textContent = '搜索中...';
        
        this.showStatus('正在搜索商品页面，AI分析相关性，检查库存状态...', 'loading');
        
        try {
            const response = await this.apiRequest('/api/add-monitor', {
                method: 'POST',
                body: JSON.stringify({
                    keyword: keyword,
                    target_sites: selectedSites,
                    notification_email: email || null
                })
            });
            
            if (response.status === 'success') {
                this.showStatus(response.summary || '监控任务已添加', 'success');
                
                // 保存监控任务
                const task = {
                    keyword: keyword,
                    sites: selectedSites,
                    email: email || null,
                    timestamp: response.timestamp || Date.now() / 1000,
                    task_id: response.task_id
                };
                
                this.monitorTasks.unshift(task);
                localStorage.setItem('monitorTasks', JSON.stringify(this.monitorTasks));
                this.updateMonitorList();
                
                // 显示结果（如果有的话）
                if (response.results && response.results.length > 0) {
                    this.displayResults(response.results);
                }
                
                // 清空输入框
                document.getElementById('keyword').value = '';
                
            } else {
                this.showStatus(response.message || '监控添加失败', 'error');
            }
            
        } catch (error) {
            let errorMessage = `错误: ${error.message}`;
            
            // 根据错误类型提供更具体的提示
            if (error.message.includes('Failed to fetch')) {
                errorMessage = '无法连接到后端服务，请检查网络连接';
                this.updateApiStatus('offline');
            } else if (error.message.includes('请求超时')) {
                errorMessage = '请求超时，请稍后重试或检查网络连接';
            }
            
            this.showStatus(errorMessage, 'error');
            console.error('监控添加失败:', error);
        } finally {
            button.disabled = false;
            button.textContent = '开始监控';
        }
    }
    
    showStatus(message, type) {
        const statusArea = document.getElementById('statusArea');
        const statusText = document.getElementById('statusText');
        
        statusArea.className = `status-area visible status-${type}`;
        statusText.textContent = message;
        
        // 自动隐藏成功消息
        if (type === 'success') {
            setTimeout(() => {
                statusArea.className = 'status-area';
            }, 5000);
        }
    }
    
    displayResults(results) {
        const resultsList = document.getElementById('resultsList');
        
        if (!results || results.length === 0) {
            resultsList.innerHTML = '<div class="empty-state">未找到相关商品</div>';
            return;
        }
        
        resultsList.innerHTML = results.map(result => {
            const availability = result.availability;
            let statusClass = 'unknown';
            let statusText = '状态未知';
            
            if (availability && availability.status === 'success') {
                if (availability.is_available) {
                    statusClass = 'available';
                    statusText = '有库存';
                } else {
                    statusClass = 'unavailable';
                    statusText = '缺货';
                }
            } else {
                statusText = '检查失败';
            }
            
            return `
                <div class="result-item">
                    <div class="result-title">${result.title || '商品页面'}</div>
                    <div class="result-url">${result.url}</div>
                    <span class="result-status status-${statusClass}">${statusText}</span>
                </div>
            `;
        }).join('');
    }
}

// 全局变量供HTML调用
let app;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    app = new MonitorApp();
});

// 全局函数供HTML调用
function startMonitoring() {
    app.startMonitoring();
}

// 错误处理
window.addEventListener('error', (event) => {
    console.error('JavaScript错误:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason);
});