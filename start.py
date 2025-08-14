#!/usr/bin/env python3
"""
商品监控系统启动脚本
"""

import os
import sys
import logging
from pathlib import Path

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_environment():
    """检查环境配置"""
    required_vars = ['OPENAI_API_KEY', 'SERPER_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 缺少必需的环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请参考 .env.example 文件配置环境变量")
        return False
    
    print("✅ 环境变量检查通过")
    return True

def check_directories():
    """检查并创建必要目录"""
    dirs = ['data', 'templates', 'static']
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"✅ 创建目录: {dir_name}")

def main():
    """主启动函数"""
    print("🛍️ 商品监控系统启动中...")
    
    # 设置日志
    setup_logging()
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 检查目录
    check_directories()
    
    # 导入并启动应用
    try:
        import uvicorn
        from app import app
        
        port = int(os.getenv("PORT", 8000))
        
        print(f"🚀 启动服务器: http://localhost:{port}")
        print("📧 邮件服务状态:", "已配置" if os.getenv("EMAIL_USER") else "未配置")
        print("🤖 AI过滤状态:", "已启用" if os.getenv("OPENAI_API_KEY") else "未启用")
        print("🔍 搜索API状态:", "已启用" if os.getenv("SERPER_API_KEY") else "未启用")
        print("\n按 Ctrl+C 停止服务")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()