import requests
import urllib3
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def search_product_pages(keyword: str, serper_key: str, target_sites: List[str]) -> List[Dict]:
    """使用Serper API搜索商品页面"""
    site_queries = []
    for site in target_sites:
        site_queries.append(f"site:{site}")
    
    # 构建搜索查询
    site_filter = " OR ".join(site_queries)
    query = f"{keyword} ({site_filter})"
    
    logger.info(f"Serper查询: {query}")
    
    try:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
        payload = {"q": query, "gl": "jp", "hl": "ja", "num": 20}
        
        response = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        logger.info(f"Serper搜索完成: 找到 {len(results)} 个结果")
        return results
        
    except Exception as e:
        logger.error(f"Serper搜索错误: {e}")
        return []