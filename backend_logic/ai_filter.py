import httpx
import urllib3
from openai import OpenAI
from typing import List
import logging

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def filter_relevant_products(url: str, keyword: str, target_sites: List[str], openai_key: str) -> bool:
    """使用AI判断商品页面是否相关"""
    # 快速过滤明显不相关的URL
    url_lower = url.lower()
    
    # 排除明显的非商品页面
    exclusion_patterns = [
        'help', 'support', 'contact', 'about', 'privacy', 'terms',
        'blog', 'news', 'press', 'careers', 'investor',
        'search', 'category', 'sitemap', 'login', 'register'
    ]
    
    if any(pattern in url_lower for pattern in exclusion_patterns):
        logger.info(f"快速过滤排除: {url}")
        return False
    
    # 检查是否为目标网站
    if not any(site.lower() in url_lower for site in target_sites):
        logger.info(f"非目标网站: {url}")
        return False
    
    # 使用AI判断是否为相关商品
    system_prompt = f"""
你是一个商品页面识别专家。请判断给定的URL是否为用户搜索的商品"{keyword}"的相关购买页面。

判断标准：
✅ 是商品页面：商品详情页、购买页面、产品展示页
✅ 与关键词相关：商品名称、品牌、型号匹配度高
✅ 可以购买：有价格、购买按钮、库存信息

❌ 不是商品页面：分类页面、搜索结果页、帮助页面、博客文章
❌ 不相关商品：完全不同的产品类别

请只回答"是"或"否"。
"""
    
    try:
        client = OpenAI(api_key=openai_key, http_client=httpx.Client(verify=False))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"关键词: {keyword}\nURL: {url}"}
            ],
            temperature=0,
            max_tokens=10
        )
        
        result = "是" in response.choices[0].message.content.strip()
        logger.info(f"AI过滤结果 {url}: {'相关' if result else '不相关'}")
        return result
        
    except Exception as e:
        logger.error(f"AI过滤错误 {url}: {e}")
        # 发生错误时采用保守策略，返回True继续处理
        return True