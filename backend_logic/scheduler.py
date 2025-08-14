import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .database import db_manager, MonitoringTask
from .email_service import email_service
from .product_checker import check_product_availability
from .ai_filter import filter_relevant_products

logger = logging.getLogger(__name__)

class MonitorScheduler:
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        self.check_interval = 300  # 5分钟检查一次
        self.max_workers = 5  # 最大并发检查数
        
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("商品监控调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("商品监控调度器已停止")
    
    def _run_scheduler(self):
        """调度器主循环"""
        while self.running:
            try:
                start_time = time.time()
                logger.info("开始执行监控任务检查")
                
                # 获取需要检查的任务
                tasks_to_check = self._get_tasks_to_check()
                
                if tasks_to_check:
                    logger.info(f"找到 {len(tasks_to_check)} 个需要检查的任务")
                    
                    # 并发执行检查
                    self._execute_monitoring_tasks(tasks_to_check)
                else:
                    logger.info("当前没有需要检查的任务")
                
                # 计算执行时间
                execution_time = time.time() - start_time
                logger.info(f"本轮检查完成，耗时 {execution_time:.2f} 秒")
                
                # 等待下次检查
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"调度器执行出错: {str(e)}")
                time.sleep(60)  # 出错时等待1分钟再重试
    
    def _get_tasks_to_check(self) -> List[MonitoringTask]:
        """获取需要检查的任务"""
        try:
            active_tasks = db_manager.get_active_tasks()
            tasks_to_check = []
            
            current_time = datetime.now()
            
            for task in active_tasks:
                # 如果任务从未检查过，或者距离上次检查超过了间隔时间
                if (task.last_check is None or 
                    current_time - task.last_check >= timedelta(seconds=self.check_interval)):
                    tasks_to_check.append(task)
            
            return tasks_to_check
            
        except Exception as e:
            logger.error(f"获取监控任务失败: {str(e)}")
            return []
    
    def _execute_monitoring_tasks(self, tasks: List[MonitoringTask]):
        """并发执行监控任务"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self._check_single_task, task): task 
                for task in tasks
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    logger.info(f"任务 {task.id} ({task.keyword}) 检查完成")
                except Exception as e:
                    logger.error(f"任务 {task.id} ({task.keyword}) 检查失败: {str(e)}")
    
    def _check_single_task(self, task: MonitoringTask) -> Dict[str, Any]:
        """检查单个监控任务"""
        try:
            logger.info(f"开始检查任务: {task.keyword}")
            
            # 更新最后检查时间
            db_manager.update_task_last_check(task.id)
            
            # 获取该任务之前的商品检查记录，用于状态对比
            previous_checks = self._get_previous_product_checks(task.id)
            
            # 重新搜索和检查商品
            from .search_products import search_product_pages
            from .ai_filter import filter_relevant_products
            
            # 搜索商品页面
            search_results = search_product_pages(
                task.keyword, 
                os.getenv("SERPER_API_KEY"), 
                task.target_sites
            )
            
            if not search_results:
                logger.warning(f"任务 {task.id} 未找到搜索结果")
                return {"status": "no_results", "task_id": task.id}
            
            # AI过滤相关商品
            filtered_products = []
            for result in search_results[:5]:  # 限制检查前5个结果
                try:
                    is_relevant = filter_relevant_products(
                        result['url'], 
                        task.keyword, 
                        task.target_sites, 
                        os.getenv("OPENAI_API_KEY")
                    )
                    
                    if is_relevant:
                        filtered_products.append(result)
                        
                except Exception as e:
                    logger.error(f"AI过滤失败 {result['url']}: {str(e)}")
                    continue
                    
                time.sleep(1)  # 避免请求过快
            
            # 检查每个商品的库存状态
            status_changes = []
            for product in filtered_products:
                try:
                    # 检查当前库存状态
                    availability = check_product_availability(product['url'])
                    
                    # 记录检查结果到数据库
                    check_record = db_manager.create_product_check(
                        task_id=task.id,
                        product_url=product['url'],
                        product_title=product.get('title'),
                        is_available=availability.get('is_available', False),
                        availability_details=availability
                    )
                    
                    # 检查状态是否发生变化
                    previous_check = previous_checks.get(product['url'])
                    if previous_check:
                        # 从无库存变为有库存
                        if (not previous_check.is_available and 
                            availability.get('is_available', False)):
                            status_changes.append({
                                'type': 'stock_available',
                                'product': product,
                                'availability': availability
                            })
                            logger.info(f"发现库存变化: {product['title']} 现在有库存了")
                    else:
                        # 新发现的商品且有库存
                        if availability.get('is_available', False):
                            status_changes.append({
                                'type': 'new_product_available',
                                'product': product,
                                'availability': availability
                            })
                            logger.info(f"发现新商品有库存: {product['title']}")
                
                except Exception as e:
                    logger.error(f"检查商品失败 {product['url']}: {str(e)}")
                    continue
                    
                time.sleep(2)  # 避免被反爬虫
            
            # 发送邮件通知
            if status_changes and task.user_email:
                self._send_notifications(task, status_changes)
            
            return {
                "status": "success",
                "task_id": task.id,
                "products_checked": len(filtered_products),
                "status_changes": len(status_changes)
            }
            
        except Exception as e:
            logger.error(f"检查任务失败 {task.id}: {str(e)}")
            return {"status": "error", "task_id": task.id, "error": str(e)}
    
    def _get_previous_product_checks(self, task_id: int) -> Dict[str, Any]:
        """获取任务的上一次商品检查记录"""
        try:
            # 获取每个商品的最新检查记录
            session = db_manager.get_session()
            try:
                from sqlalchemy import func
                from .database import ProductCheck
                
                # 子查询：获取每个URL的最新检查时间
                latest_checks = session.query(
                    ProductCheck.product_url,
                    func.max(ProductCheck.check_time).label('latest_time')
                ).filter(
                    ProductCheck.task_id == task_id
                ).group_by(ProductCheck.product_url).subquery()
                
                # 主查询：获取最新的检查记录
                previous_checks = session.query(ProductCheck).join(
                    latest_checks,
                    (ProductCheck.product_url == latest_checks.c.product_url) &
                    (ProductCheck.check_time == latest_checks.c.latest_time)
                ).filter(ProductCheck.task_id == task_id).all()
                
                return {check.product_url: check for check in previous_checks}
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"获取历史检查记录失败: {str(e)}")
            return {}
    
    def _send_notifications(self, task: MonitoringTask, status_changes: List[Dict[str, Any]]):
        """发送通知邮件"""
        try:
            for change in status_changes:
                product_info = {
                    'title': change['product'].get('title', '商品页面'),
                    'url': change['product']['url'],
                    'availability': change['availability']
                }
                
                if change['type'] in ['stock_available', 'new_product_available']:
                    success = email_service.send_stock_alert(task.user_email, product_info)
                    if success:
                        logger.info(f"库存提醒邮件发送成功: {task.user_email}")
                    else:
                        logger.error(f"库存提醒邮件发送失败: {task.user_email}")
                        
        except Exception as e:
            logger.error(f"发送通知邮件失败: {str(e)}")

# 全局调度器实例
monitor_scheduler = MonitorScheduler()

# 导入必要的模块
import os