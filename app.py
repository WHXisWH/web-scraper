from pathlib import Path
import traceback
from datetime import datetime
from typing import List, Optional
import logging
import os

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager

from backend_logic.monitor_runner import run_product_monitoring
from backend_logic.database import db_manager
from backend_logic.scheduler import monitor_scheduler
from backend_logic.email_service import email_service

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    logger.info("正在启动商品监控系统...")
    
    # 启动监控调度器
    monitor_scheduler.start()
    logger.info("监控调度器已启动")
    
    yield
    
    # 关闭时
    logger.info("正在关闭商品监控系统...")
    monitor_scheduler.stop()
    logger.info("监控调度器已停止")

# 创建目录
ROOT_DIR = Path(__file__).resolve().parent
templates_dir = ROOT_DIR / "templates"
static_dir = ROOT_DIR / "static"
data_dir = ROOT_DIR / "data"

for d in (templates_dir, static_dir, data_dir):
    d.mkdir(exist_ok=True)

# 创建FastAPI应用
app = FastAPI(
    title="商品监控系统",
    version="2.0.0",
    description="智能商品库存监控与邮件通知系统",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# API数据模型
class MonitorRequest(BaseModel):
    keyword: str
    target_sites: Optional[List[str]] = ["amazon.co.jp", "louisvuitton.com"]
    notification_email: Optional[str] = None

class MonitorTaskResponse(BaseModel):
    task_id: int
    keyword: str
    status: str
    created_at: datetime
    last_check: Optional[datetime]
    user_email: Optional[str]

class ProductCheckResponse(BaseModel):
    id: int
    product_url: str
    product_title: Optional[str]
    is_available: bool
    price: Optional[float]
    check_time: datetime

# 路由处理器
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """主页"""
    try:
        index_html = templates_dir / "index.html"
        if index_html.exists():
            return templates.TemplateResponse("index.html", {"request": request})
        else:
            raise HTTPException(status_code=404, detail="模板文件未找到")
    except Exception as e:
        logger.error(f"主页加载失败: {str(e)}")
        raise HTTPException(status_code=500, detail="页面加载失败")

@app.post("/api/add-monitor")
def add_monitor(req: MonitorRequest, background_tasks: BackgroundTasks):
    """添加监控任务"""
    try:
        logger.info(f"添加监控任务: {req.keyword}")
        
        # 验证输入
        if not req.keyword.strip():
            raise HTTPException(status_code=400, detail="商品关键词不能为空")
        
        if not req.target_sites:
            raise HTTPException(status_code=400, detail="必须选择至少一个监控网站")
        
        # 创建监控任务
        task = db_manager.create_monitoring_task(
            keyword=req.keyword.strip(),
            target_sites=req.target_sites,
            user_email=req.notification_email
        )
        
        logger.info(f"监控任务已创建: ID={task.id}, 关键词={task.keyword}")
        
        # 在后台执行首次检查
        background_tasks.add_task(
            perform_initial_check, 
            task.id, 
            req.keyword, 
            req.target_sites, 
            req.notification_email
        )
        
        return {
            "status": "success",
            "message": "监控任务已添加，正在进行首次检查",
            "task_id": task.id,
            "keyword": req.keyword,
            "summary": f"已添加监控任务，将在后台持续监控",
            "timestamp": datetime.now().timestamp()
        }
        
    except Exception as e:
        logger.error(f"添加监控任务失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"添加监控任务失败: {str(e)}")

def perform_initial_check(task_id: int, keyword: str, target_sites: List[str], notification_email: Optional[str]):
    """执行首次检查（后台任务）"""
    try:
        logger.info(f"开始执行首次检查: 任务ID={task_id}")
        
        # 执行商品监控
        result = run_product_monitoring(
            keyword=keyword,
            target_sites=target_sites,
            notification_email=notification_email,
            task_id=task_id  # 传递task_id用于数据库记录
        )
        
        logger.info(f"首次检查完成: 任务ID={task_id}, 结果={result.get('status')}")
        
    except Exception as e:
        logger.error(f"首次检查失败: 任务ID={task_id}, 错误={str(e)}")

@app.get("/api/monitors", response_model=List[MonitorTaskResponse])
def get_monitors():
    """获取监控任务列表"""
    try:
        tasks = db_manager.get_active_tasks()
        return [
            MonitorTaskResponse(
                task_id=task.id,
                keyword=task.keyword,
                status=task.status,
                created_at=task.created_at,
                last_check=task.last_check,
                user_email=task.user_email
            )
            for task in tasks
        ]
    except Exception as e:
        logger.error(f"获取监控任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取监控任务失败")

@app.delete("/api/monitors/{task_id}")
def delete_monitor(task_id: int):
    """删除监控任务"""
    try:
        success = db_manager.delete_task(task_id)
        if success:
            logger.info(f"监控任务已删除: ID={task_id}")
            return {"status": "success", "message": "监控任务已删除"}
        else:
            raise HTTPException(status_code=404, detail="监控任务未找到")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除监控任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除监控任务失败")

@app.get("/api/monitors/{task_id}/checks", response_model=List[ProductCheckResponse])
def get_task_checks(task_id: int, limit: int = 20):
    """获取任务的检查历史"""
    try:
        # 获取任务
        task = db_manager.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="监控任务未找到")
        
        # 获取检查记录（限制数量）
        session = db_manager.get_session()
        try:
            from backend_logic.database import ProductCheck
            checks = session.query(ProductCheck).filter(
                ProductCheck.task_id == task_id
            ).order_by(ProductCheck.check_time.desc()).limit(limit).all()
            
            return [
                ProductCheckResponse(
                    id=check.id,
                    product_url=check.product_url,
                    product_title=check.product_title,
                    is_available=check.is_available,
                    price=float(check.price) if check.price else None,
                    check_time=check.check_time
                )
                for check in checks
            ]
        finally:
            session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取检查历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取检查历史失败")

@app.get("/api/system/status")
def get_system_status():
    """获取系统状态"""
    try:
        active_tasks = db_manager.get_active_tasks()
        scheduler_running = monitor_scheduler.running
        email_configured = email_service.is_configured()
        
        return {
            "status": "running" if scheduler_running else "stopped",
            "scheduler_running": scheduler_running,
            "email_configured": email_configured,
            "active_tasks_count": len(active_tasks),
            "version": "2.0.0",
            "features": {
                "database_storage": True,
                "email_notifications": email_configured,
                "background_monitoring": scheduler_running,
                "ai_filtering": bool(os.getenv("OPENAI_API_KEY")),
                "search_api": bool(os.getenv("SERPER_API_KEY"))
            }
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/api/system/test-email")
def test_email(email: str):
    """测试邮件发送"""
    try:
        if not email_service.is_configured():
            raise HTTPException(status_code=503, detail="邮件服务未配置")
        
        success = email_service.send_email(
            to_email=email,
            subject="商品监控系统 - 测试邮件",
            html_content="""
            <h2>🛍️ 邮件服务测试成功</h2>
            <p>您的商品监控系统邮件服务已正确配置。</p>
            <p>现在可以接收库存变化通知了！</p>
            """,
            text_content="邮件服务测试成功！现在可以接收库存变化通知了。"
        )
        
        if success:
            return {"status": "success", "message": "测试邮件发送成功"}
        else:
            raise HTTPException(status_code=500, detail="邮件发送失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试邮件发送失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"邮件发送失败: {str(e)}")

# 调试和健康检查端点
@app.get("/debug/status")
def debug_status():
    """调试状态信息（兼容旧版本）"""
    return get_system_status()

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 异常处理器
@app.exception_handler(500)
async def internal_server_error(request: Request, exc: Exception):
    logger.error(f"内部服务器错误: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误，请稍后重试"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    )