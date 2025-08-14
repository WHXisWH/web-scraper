// API配置
const API_CONFIG = {
    // 开发环境
    development: {
        baseURL: 'http://localhost:8000',
        timeout: 30000
    },
    // 生产环境 - 替换为你的Railway后端URL
    production: {
        baseURL: process.env.NODE_ENV === 'production' 
            ? 'https://your-backend.railway.app'  // 替换为实际的Railway域名
            : 'http://localhost:8000',
        timeout: 60000
    }
};

// 当前环境配置
const currentConfig = API_CONFIG[process.env.NODE_ENV] || API_CONFIG.development;

// 从环境变量或URL参数获取API地址
const getApiBaseUrl = () => {
    // 优先使用环境变量
    if (window.API_BASE_URL) {
        return window.API_BASE_URL;
    }
    
    // URL参数覆盖 (用于调试: ?api=http://localhost:8000)
    const urlParams = new URLSearchParams(window.location.search);
    const apiParam = urlParams.get('api');
    if (apiParam) {
        return apiParam;
    }
    
    // 自动检测环境
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return API_CONFIG.development.baseURL;
    }
    
    return currentConfig.baseURL;
};

// 导出配置
window.API_BASE_URL = getApiBaseUrl();
window.API_TIMEOUT = currentConfig.timeout;

console.log('🔧 API配置:', {
    baseURL: window.API_BASE_URL,
    timeout: window.API_TIMEOUT,
    environment: process.env.NODE_ENV || 'development'
});