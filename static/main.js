class MonitorApp {
    constructor() {
        this.monitorTasks = JSON.parse(localStorage.getItem('monitorTasks') || '[]');
        this.init();
    }
    
    init() {
        this.updateMonitorList();
        this.bindEvents();
    }
    
    bindEvents() {
        // 回车键快捷提交
        document.getElementById('keyword').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.startMonitoring();
            }
        });
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
        
        const button = document.getElementById('startBtn');
        button.disabled = true;
        button.textContent = '搜索中...';
        
        this.showStatus('正在搜索商品页面，AI分析相关性，检查库存状态...', 'loading');
        
        try {
            const response = await fetch('/api/add-monitor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keyword: keyword,
                    target_sites: selectedSites,
                    notification_email: email || null
                })
            });
            
            if (!response.ok) {
                throw new Error(`服务器错误 (${response.status})`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showStatus(data.summary, 'success');
                
                // 保存监控任务
                const task = {
                    keyword: keyword,
                    sites: selectedSites,
                    email: email || null,
                    timestamp: data.timestamp,
                    results: data.results
                };
                
                this.monitorTasks.unshift(task); // 添加到开头
                localStorage.setItem('monitorTasks', JSON.stringify(this.monitorTasks));
                this.updateMonitorList();
                
                // 显示结果
                this.displayResults(data.results);
                
                // 清空输入框
                document.getElementById('keyword').value = '';
                
            } else {
                this.showStatus(data.message || '监控添加失败', 'error');
            }
            
        } catch (error) {
            this.showStatus(`错误: ${error.message}`, 'error');
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