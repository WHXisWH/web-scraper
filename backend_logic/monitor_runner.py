import os
import time
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from .search_products import search_product_pages
from .product_checker import check_product_availability
from .ai_filter import filter_relevant_products
from .database import db_manager
from .email_service import email_service

logger = logging.getLogger(__name__)

def run_product_monitoring(
    keyword: str,
    target_sites: List[str] = ["amazon.co.jp", "louisvuitton.com"],
    notification_email: Optional[str] = None,
    task_id: Optional[int] = None
) -> Dict[str, Any]:
    """执行商品监控的主函数"""
    
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    
    if not OPENAI_API_KEY or not SERPER_API_KEY:
        raise RuntimeError("需要设置 OPENAI_API_KEY 和 SERPER_API_KEY")

    logger.info(f"开始监控商品: {keyword}")
    
    try:
        # 1. 搜索商品页面
        search_results = search_product_pages(keyword, SERPER_API_KEY, target_sites)
        logger.info(f"找到 {len(search_results)} 个搜索结果")
        
        if not search_results:
            return {
                "status": "error",
                "message": "未找到相关商品页面",
                "keyword": keyword,
                "results": []
            }
        
        # 2. AI过滤相关商品
        filtered_products = []
        for i, result in enumerate(search_results[:10]):  # 限制处理前10个结果
            logger.info(f"AI检查 ({i+1}/{min(10, len(search_results))}): {result['url']}")
            
            try:
                is_relevant = filter_relevant_products(
                    url=result['url'],
                    keyword=keyword,
                    target_sites=target_sites,
                    openai_key=OPENAI_API_KEY
                )
                
                if is_relevant:
                    logger.info(f"相关商品: {result['title']}")
                    filtered_products.append(result)
                else:
                    logger.info(f"不相关: {result['title']}")
            except Exception as e:
                logger.error(f"AI过滤失败 {result['url']}: {str(e)}")
                continue
            
            time.sleep(1)  # 避免请求过快
        
        if not filtered_products:
            return {
                "status": "error",
                "message": "未找到相关的商品页面",
                "keyword": keyword,
                "results": []
            }
        
        # 3. 检查商品可用性
        availability_results = []
        for product in filtered_products:
            logger.info(f"检查库存: {product['url']}")
            
            try:
                availability = check_product_availability(product['url'])
                
                result_item = {
                    "title": product['title'],
                    "url": product['url'],
                    "availability": availability,
                    "timestamp": time.time()
                }
                availability_results.append(result_item)
                
                # 如果提供了task_id，记录到数据库
                if task_id:
                    try:
                        db_manager.create_product_check(
                            task_id=task_id,
                            product_url=product['url'],
                            product_title=product['title'],
                            is_available=availability.get('is_available', False),
                            price=availability.get('price'),
                            availability_details=availability
                        )
                    except Exception as e:
                        logger.error(f"保存检查记录失败: {str(e)}")
                
                # 如果商品有库存且提供了邮箱，发送通知
                if (availability.get('is_available', False) and 
                    notification_email and 
                    email_service.is_configured()):
                    try:
                        product_info = {
                            'title': product['title'],
                            'url': product['url'],
                            'price': availability.get('price'),
                            'availability': availability
                        }
                        success = email_service.send_stock_alert(notification_email, product_info)
                        if success:
                            logger.info(f"库存通知邮件发送成功: {notification_email}")
                        else:
                            logger.error(f"库存通知邮件发送失败: {notification_email}")
                    except Exception as e:
                        logger.error(f"发送邮件通知失败: {str(e)}")
                
            except Exception as e:
                logger.error(f"商品检查失败 {product['url']}: {str(e)}")
                availability_results.append({
                    "title": product['title'],
                    "url": product['url'],
                    "availability": {
                        "is_available": False,
                        "status": "error",
                        "error": str(e)
                    },
                    "timestamp": time.time()
                })
            
            time.sleep(1.5)  # 避免被反爬虫
        
        # 4. 生成监控报告
        available_count = sum(
            1 for r in availability_results 
            if r['availability'].get('is_available', False)
        )
        
        # 如果提供了task_id，更新最后检查时间
        if task_id:
            try:
                db_manager.update_task_last_check(task_id)
            except Exception as e:
                logger.error(f"更新任务检查时间失败: {str(e)}")
        
        summary_message = f"找到 {len(availability_results)} 个相关商品"
        if available_count > 0:
            summary_message += f"，{available_count} 个有库存"
        else:
            summary_message += "，暂无库存"
        
        logger.info(f"监控完成: {summary_message}")
        
        return {
            "status": "success",
            "keyword": keyword,
            "summary": summary_message,
            "results": availability_results,
            "notification_email": notification_email,
            "task_id": task_id,
            "timestamp": time.time(),
            "stats": {
                "total_searched": len(search_results),
                "ai_filtered": len(filtered_products),
                "checked": len(availability_results),
                "available": available_count
            }
        }
        
    except Exception as e:
        logger.error(f"监控执行失败: {str(e)}")
        return {
            "status": "error",
            "message": f"监控执行失败: {str(e)}",
            "keyword": keyword,
            "results": [],
            "timestamp": time.time()
        }