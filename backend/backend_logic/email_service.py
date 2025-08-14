import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # 从环境变量获取邮件配置
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.from_name = os.getenv("FROM_NAME", "商品监控系统")
        
        if not self.email_user or not self.email_password:
            logger.warning("邮件服务未配置：缺少 EMAIL_USER 或 EMAIL_PASSWORD")
    
    def is_configured(self) -> bool:
        """检查邮件服务是否已配置"""
        return bool(self.email_user and self.email_password)
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """发送邮件"""
        if not self.is_configured():
            logger.error("邮件服务未配置，无法发送邮件")
            return False
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.email_user}>"
            msg['To'] = to_email
            
            # 添加纯文本内容
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            # 添加HTML内容
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False
    
    def send_stock_alert(self, to_email: str, product_info: Dict[str, Any]) -> bool:
        """发送库存提醒邮件"""
        subject = "🛍️ 商品有库存了！"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: #000; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; }}
                .product-info {{ background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                .status-available {{ color: #28a745; font-weight: bold; }}
                .buy-button {{ display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; background: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛍️ 商品监控提醒</h1>
                </div>
                <div class="content">
                    <h2>您监控的商品现在有库存了！</h2>
                    
                    <div class="product-info">
                        <h3>{product_info.get('title', '商品页面')}</h3>
                        <p><strong>网站：</strong>{self._get_site_name(product_info.get('url', ''))}</p>
                        <p><strong>状态：</strong><span class="status-available">🟢 有库存</span></p>
                        {f"<p><strong>价格：</strong>¥{product_info.get('price', 'N/A')}</p>" if product_info.get('price') else ""}
                        <p><strong>检查时间：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <a href="{product_info.get('url', '')}" class="buy-button">立即查看商品</a>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        💡 提示：商品库存可能随时变化，建议尽快查看
                    </p>
                </div>
                <div class="footer">
                    <p>此邮件由商品监控系统自动发送</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
🛍️ 商品监控提醒

您监控的商品现在有库存了！

商品：{product_info.get('title', '商品页面')}
网站：{self._get_site_name(product_info.get('url', ''))}
状态：🟢 有库存
{f"价格：¥{product_info.get('price')}" if product_info.get('price') else ""}
检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

查看商品：{product_info.get('url', '')}

💡 提示：商品库存可能随时变化，建议尽快查看
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_price_alert(self, to_email: str, product_info: Dict[str, Any]) -> bool:
        """发送价格变化提醒邮件"""
        subject = "💰 商品价格变化提醒"
        
        old_price = product_info.get('old_price', 0)
        new_price = product_info.get('new_price', 0)
        price_change = new_price - old_price
        change_percent = (price_change / old_price * 100) if old_price > 0 else 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: #000; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; }}
                .product-info {{ background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                .price-down {{ color: #28a745; }}
                .price-up {{ color: #dc3545; }}
                .buy-button {{ display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; background: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💰 价格变化提醒</h1>
                </div>
                <div class="content">
                    <h2>您监控的商品价格发生了变化</h2>
                    
                    <div class="product-info">
                        <h3>{product_info.get('title', '商品页面')}</h3>
                        <p><strong>网站：</strong>{self._get_site_name(product_info.get('url', ''))}</p>
                        <p><strong>原价：</strong>¥{old_price}</p>
                        <p><strong>现价：</strong>¥{new_price}</p>
                        <p><strong>变化：</strong>
                            <span class="{'price-down' if price_change < 0 else 'price-up'}">
                                {'+' if price_change > 0 else ''}¥{price_change:.2f} ({change_percent:+.1f}%)
                            </span>
                        </p>
                        <p><strong>检查时间：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <a href="{product_info.get('url', '')}" class="buy-button">查看商品详情</a>
                </div>
                <div class="footer">
                    <p>此邮件由商品监控系统自动发送</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_daily_summary(self, to_email: str, summary_data: Dict[str, Any]) -> bool:
        """发送每日监控汇总邮件"""
        subject = "📊 每日监控汇总"
        
        total_tasks = summary_data.get('total_tasks', 0)
        available_products = summary_data.get('available_products', 0)
        price_changes = summary_data.get('price_changes', 0)
        new_products = summary_data.get('new_products', 0)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: #000; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; }}
                .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .stat-item {{ background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .stat-label {{ color: #666; margin-top: 5px; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; background: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 每日监控汇总</h1>
                    <p>{datetime.now().strftime('%Y年%m月%d日')}</p>
                </div>
                <div class="content">
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-number">{total_tasks}</div>
                            <div class="stat-label">监控任务</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{available_products}</div>
                            <div class="stat-label">有库存商品</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{price_changes}</div>
                            <div class="stat-label">价格变化</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{new_products}</div>
                            <div class="stat-label">新发现商品</div>
                        </div>
                    </div>
                    
                    <p style="color: #666; text-align: center; margin-top: 30px;">
                        持续为您监控心仪的商品 🛍️
                    </p>
                </div>
                <div class="footer">
                    <p>此邮件由商品监控系统自动发送</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def _get_site_name(self, url: str) -> str:
        """根据URL获取网站名称"""
        if 'amazon' in url.lower():
            return 'Amazon'
        elif 'louisvuitton' in url.lower():
            return 'Louis Vuitton'
        elif 'rakuten' in url.lower():
            return '楽天'
        else:
            return '未知网站'

# 全局邮件服务实例
email_service = EmailService()