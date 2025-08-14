#!/usr/bin/env python3
"""
简单的应用测试脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        import app
        print("✅ app.py 导入成功")
        
        from backend_logic.database import db_manager
        print("✅ database.py 导入成功")
        
        from backend_logic.email_service import email_service
        print("✅ email_service.py 导入成功")
        
        from backend_logic.scheduler import monitor_scheduler
        print("✅ scheduler.py 导入成功")
        
        from backend_logic.product_checker import check_product_availability
        print("✅ product_checker.py 导入成功")
        
        from backend_logic.ai_filter import filter_relevant_products
        print("✅ ai_filter.py 导入成功")
        
        from backend_logic.search_products import search_product_pages
        print("✅ search_products.py 导入成功")
        
        from backend_logic.monitor_runner import run_product_monitoring
        print("✅ monitor_runner.py 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_database():
    """测试数据库功能"""
    print("\n🗄️ 测试数据库功能...")
    
    try:
        from backend_logic.database import db_manager
        
        # 测试获取活跃任务
        tasks = db_manager.get_active_tasks()
        print(f"✅ 数据库连接成功，当前活跃任务: {len(tasks)}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_api_routes():
    """测试API路由"""
    print("\n🌐 测试API路由...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # 测试主页
        response = client.get("/")
        print(f"✅ 主页路由: {response.status_code}")
        
        # 测试系统状态
        response = client.get("/api/system/status")
        print(f"✅ 系统状态API: {response.status_code}")
        
        # 测试监控列表
        response = client.get("/api/monitors")
        print(f"✅ 监控列表API: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ API路由测试失败: {e}")
        return False

def test_configuration():
    """测试配置"""
    print("\n⚙️ 测试配置...")
    
    # 检查必需的环境变量
    required_vars = ['OPENAI_API_KEY', 'SERPER_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️ 缺少环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("   请配置 .env 文件中的API密钥以启用完整功能")
    else:
        print("✅ 所有必需环境变量已配置")
    
    # 检查邮件配置
    email_vars = ['EMAIL_USER', 'EMAIL_PASSWORD']
    if all(os.getenv(var) for var in email_vars):
        print("✅ 邮件服务已配置")
    else:
        print("⚠️ 邮件服务未配置（可选功能）")
    
    return True

def main():
    """主测试函数"""
    print("🛍️ 商品监控系统 - 构建测试")
    print("=" * 50)
    
    # 创建必要目录
    directories = ['data', 'templates', 'static']
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
    
    success = True
    
    # 运行所有测试
    success &= test_imports()
    success &= test_database()
    success &= test_api_routes()
    success &= test_configuration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过！项目构建成功")
        print("\n📚 使用说明:")
        print("1. 配置 .env 文件中的API密钥")
        print("2. 运行: python3 start.py")
        print("3. 访问: http://localhost:8000")
    else:
        print("❌ 部分测试失败，请检查错误信息")
        return 1
    
    return 0

if __name__ == "__main__":
    # 安装测试依赖
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        print("正在安装测试依赖...")
        os.system("python3 -m pip install pytest httpx")
    
    sys.exit(main())