from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, JSON, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
import os

# 数据库基类
Base = declarative_base()

# 监控任务模型
class MonitoringTask(Base):
    __tablename__ = "monitoring_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), nullable=False, index=True)
    target_sites = Column(JSON, nullable=False)  # ['amazon.co.jp', 'louisvuitton.com']
    user_email = Column(String(255), nullable=True)
    status = Column(String(50), default="active")  # active, paused, stopped
    created_at = Column(DateTime, default=func.now())
    last_check = Column(DateTime, nullable=True)
    
    # 关联关系
    product_checks = relationship("ProductCheck", back_populates="task", cascade="all, delete-orphan")

# 商品检查记录模型
class ProductCheck(Base):
    __tablename__ = "product_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("monitoring_tasks.id"), nullable=False)
    product_url = Column(Text, nullable=False)
    product_title = Column(Text, nullable=True)
    is_available = Column(Boolean, default=False)
    price = Column(DECIMAL(10, 2), nullable=True)
    availability_details = Column(JSON, nullable=True)  # 详细检查结果
    check_time = Column(DateTime, default=func.now())
    
    # 关联关系
    task = relationship("MonitoringTask", back_populates="product_checks")

# 数据库管理类
class DatabaseManager:
    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            # 默认使用SQLite
            db_path = os.path.join(os.path.dirname(__file__), "..", "data", "monitor.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 创建表
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def create_monitoring_task(
        self, 
        keyword: str, 
        target_sites: List[str], 
        user_email: Optional[str] = None
    ) -> MonitoringTask:
        """创建监控任务"""
        session = self.get_session()
        try:
            task = MonitoringTask(
                keyword=keyword,
                target_sites=target_sites,
                user_email=user_email,
                status="active"
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        finally:
            session.close()
    
    def get_active_tasks(self) -> List[MonitoringTask]:
        """获取所有活跃的监控任务"""
        session = self.get_session()
        try:
            return session.query(MonitoringTask).filter(
                MonitoringTask.status == "active"
            ).all()
        finally:
            session.close()
    
    def update_task_last_check(self, task_id: int):
        """更新任务最后检查时间"""
        session = self.get_session()
        try:
            session.query(MonitoringTask).filter(
                MonitoringTask.id == task_id
            ).update({
                "last_check": datetime.now()
            })
            session.commit()
        finally:
            session.close()
    
    def create_product_check(
        self,
        task_id: int,
        product_url: str,
        product_title: Optional[str],
        is_available: bool,
        price: Optional[float] = None,
        availability_details: Optional[dict] = None
    ) -> ProductCheck:
        """记录商品检查结果"""
        session = self.get_session()
        try:
            check = ProductCheck(
                task_id=task_id,
                product_url=product_url,
                product_title=product_title,
                is_available=is_available,
                price=price,
                availability_details=availability_details
            )
            session.add(check)
            session.commit()
            session.refresh(check)
            return check
        finally:
            session.close()
    
    def get_latest_product_status(self, task_id: int, product_url: str) -> Optional[ProductCheck]:
        """获取商品最新状态"""
        session = self.get_session()
        try:
            return session.query(ProductCheck).filter(
                ProductCheck.task_id == task_id,
                ProductCheck.product_url == product_url
            ).order_by(ProductCheck.check_time.desc()).first()
        finally:
            session.close()
    
    def get_task_by_id(self, task_id: int) -> Optional[MonitoringTask]:
        """根据ID获取任务"""
        session = self.get_session()
        try:
            return session.query(MonitoringTask).filter(
                MonitoringTask.id == task_id
            ).first()
        finally:
            session.close()
    
    def delete_task(self, task_id: int) -> bool:
        """删除监控任务"""
        session = self.get_session()
        try:
            task = session.query(MonitoringTask).filter(
                MonitoringTask.id == task_id
            ).first()
            if task:
                session.delete(task)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_availability_changes(self, task_id: int, hours: int = 24) -> List[ProductCheck]:
        """获取指定时间内的库存状态变化"""
        session = self.get_session()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return session.query(ProductCheck).filter(
                ProductCheck.task_id == task_id,
                ProductCheck.check_time >= cutoff_time
            ).order_by(ProductCheck.check_time.desc()).all()
        finally:
            session.close()

# 全局数据库实例
db_manager = DatabaseManager()