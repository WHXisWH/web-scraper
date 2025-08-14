import requests
import urllib3
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
import re
import logging
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SiteSpecificDetector:
    """网站特定的检测规则"""
    
    @staticmethod
    def detect_amazon(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Amazon网站检测逻辑"""
        result = {
            'is_available': False,
            'price': None,
            'stock_status': 'unknown',
            'indicators': {}
        }
        
        # 库存检测
        availability_indicators = []
        
        # 查找"加入购物车"按钮
        add_to_cart = soup.find('input', {'id': 'add-to-cart-button'}) or soup.find('button', {'id': 'add-to-cart-button'})
        if add_to_cart and not add_to_cart.get('disabled'):
            availability_indicators.append('add_to_cart_enabled')
        
        # 查找库存状态文本
        availability_text = soup.find('div', {'id': 'availability'})
        if availability_text:
            text = availability_text.get_text().lower()
            if '在庫あり' in text or 'in stock' in text or 'available' in text:
                availability_indicators.append('stock_available_text')
            elif '在庫切れ' in text or 'out of stock' in text or 'unavailable' in text:
                availability_indicators.append('out_of_stock_text')
        
        # 查找价格信息
        price_elements = soup.find_all(['span', 'div'], class_=re.compile(r'.*price.*', re.I))
        for elem in price_elements:
            price_text = elem.get_text()
            # 匹配日元价格 ¥1,000 或 1,000円
            price_match = re.search(r'[¥￥][\d,]+|[\d,]+円', price_text)
            if price_match:
                price_str = re.sub(r'[¥￥円,]', '', price_match.group())
                try:
                    result['price'] = float(price_str)
                    availability_indicators.append('price_found')
                    break
                except ValueError:
                    continue
        
        # 综合判断
        result['indicators'] = availability_indicators
        result['is_available'] = (
            'add_to_cart_enabled' in availability_indicators and
            'out_of_stock_text' not in availability_indicators and
            len(availability_indicators) >= 2
        )
        
        if result['is_available']:
            result['stock_status'] = 'in_stock'
        elif 'out_of_stock_text' in availability_indicators:
            result['stock_status'] = 'out_of_stock'
        
        return result
    
    @staticmethod
    def detect_louisvuitton(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Louis Vuitton网站检测逻辑"""
        result = {
            'is_available': False,
            'price': None,
            'stock_status': 'unknown',
            'indicators': {}
        }
        
        availability_indicators = []
        
        # 查找添加到购物车按钮
        add_to_cart_buttons = soup.find_all(['button', 'a'], 
                                          text=re.compile(r'add to bag|カートに追加|加入购物车', re.I))
        if add_to_cart_buttons:
            for button in add_to_cart_buttons:
                if not button.get('disabled') and 'disabled' not in button.get('class', []):
                    availability_indicators.append('add_to_cart_enabled')
                    break
        
        # 查找库存状态
        availability_selectors = [
            '.availability', '.stock-status', '.product-availability',
            '[data-testid*="availability"]', '[class*="availability"]'
        ]
        for selector in availability_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().lower()
                if any(phrase in text for phrase in ['available', '在庫あり', '有库存']):
                    availability_indicators.append('stock_available_text')
                elif any(phrase in text for phrase in ['sold out', 'out of stock', '在庫切れ', '缺货']):
                    availability_indicators.append('out_of_stock_text')
        
        # 查找价格
        price_selectors = [
            '.price', '.product-price', '[class*="price"]', 
            '[data-testid*="price"]'
        ]
        for selector in price_selectors:
            elements = soup.select(selector)
            for elem in elements:
                price_text = elem.get_text()
                # 匹配多种货币格式
                price_match = re.search(r'[¥￥$€£][\d,]+|[\d,]+[円元]', price_text)
                if price_match:
                    price_str = re.sub(r'[¥￥$€£円元,]', '', price_match.group())
                    try:
                        result['price'] = float(price_str)
                        availability_indicators.append('price_found')
                        break
                    except ValueError:
                        continue
            if result['price']:
                break
        
        result['indicators'] = availability_indicators
        result['is_available'] = (
            'add_to_cart_enabled' in availability_indicators and
            'out_of_stock_text' not in availability_indicators
        )
        
        if result['is_available']:
            result['stock_status'] = 'in_stock'
        elif 'out_of_stock_text' in availability_indicators:
            result['stock_status'] = 'out_of_stock'
        
        return result
    
    @staticmethod
    def detect_rakuten(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """楽天网站检测逻辑"""
        result = {
            'is_available': False,
            'price': None,
            'stock_status': 'unknown',
            'indicators': {}
        }
        
        availability_indicators = []
        
        # 查找购买按钮
        buy_buttons = soup.find_all(['button', 'input', 'a'], 
                                  class_=re.compile(r'.*cart.*|.*buy.*|.*purchase.*', re.I))
        for button in buy_buttons:
            if not button.get('disabled'):
                availability_indicators.append('buy_button_enabled')
                break
        
        # 查找库存文本
        stock_elements = soup.find_all(text=re.compile(r'在庫|stock|库存', re.I))
        for text in stock_elements:
            if any(phrase in text.lower() for phrase in ['あり', 'available', '有']):
                availability_indicators.append('stock_available_text')
            elif any(phrase in text.lower() for phrase in ['なし', 'out', '无', '切れ']):
                availability_indicators.append('out_of_stock_text')
        
        # 查找价格
        price_elements = soup.find_all(['span', 'div'], class_=re.compile(r'.*price.*', re.I))
        for elem in price_elements:
            price_text = elem.get_text()
            price_match = re.search(r'[¥￥][\d,]+|[\d,]+円', price_text)
            if price_match:
                price_str = re.sub(r'[¥￥円,]', '', price_match.group())
                try:
                    result['price'] = float(price_str)
                    availability_indicators.append('price_found')
                    break
                except ValueError:
                    continue
        
        result['indicators'] = availability_indicators
        result['is_available'] = (
            'buy_button_enabled' in availability_indicators and
            'out_of_stock_text' not in availability_indicators and
            'price_found' in availability_indicators
        )
        
        if result['is_available']:
            result['stock_status'] = 'in_stock'
        elif 'out_of_stock_text' in availability_indicators:
            result['stock_status'] = 'out_of_stock'
        
        return result

def get_site_detector(url: str):
    """根据URL获取对应的网站检测器"""
    domain = urlparse(url).netloc.lower()
    
    if 'amazon' in domain:
        return SiteSpecificDetector.detect_amazon
    elif 'louisvuitton' in domain or 'lv' in domain:
        return SiteSpecificDetector.detect_louisvuitton
    elif 'rakuten' in domain:
        return SiteSpecificDetector.detect_rakuten
    else:
        return None

def check_product_availability(url: str, max_retries: int = 3) -> Dict[str, Any]:
    """检查商品可用性的主函数"""
    for attempt in range(max_retries):
        try:
            # 设置请求头，模拟真实浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # 添加网站特定的请求头
            domain = urlparse(url).netloc.lower()
            if 'amazon' in domain:
                headers['Accept-Language'] = 'ja,en;q=0.9'
            elif 'louisvuitton' in domain:
                headers['Cache-Control'] = 'no-cache'
            
            logger.info(f"检查商品库存: {url}")
            
            # 发送请求
            response = requests.get(
                url, 
                headers=headers, 
                timeout=15, 
                verify=False,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取网站特定检测器
            detector = get_site_detector(url)
            if detector:
                result = detector(soup, url)
            else:
                # 通用检测逻辑
                result = _generic_detection(soup, url)
            
            # 添加元数据
            result.update({
                'url': url,
                'check_time': time.time(),
                'status': 'success',
                'response_code': response.status_code,
                'attempt': attempt + 1
            })
            
            logger.info(f"商品检查完成: {url}, 状态: {result['stock_status']}, 可购买: {result['is_available']}")
            return result
            
        except requests.exceptions.Timeout:
            logger.warning(f"请求超时 (尝试 {attempt + 1}/{max_retries}): {url}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {url}, 错误: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
        except Exception as e:
            logger.error(f"商品检查出错: {url}, 错误: {str(e)}")
            break
    
    # 所有重试都失败了
    return {
        'url': url,
        'is_available': False,
        'price': None,
        'stock_status': 'check_failed',
        'status': 'error',
        'error': f'检查失败，已重试 {max_retries} 次',
        'check_time': time.time(),
        'indicators': {}
    }

def _generic_detection(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """通用商品检测逻辑"""
    result = {
        'is_available': False,
        'price': None,
        'stock_status': 'unknown',
        'indicators': {}
    }
    
    availability_indicators = []
    
    # 通用购买按钮检测
    buy_button_texts = [
        'add to cart', 'カートに入れる', 'カートに追加', '购买', '立即购买',
        'buy now', 'add to bag', 'add to basket'
    ]
    
    for text_pattern in buy_button_texts:
        buttons = soup.find_all(['button', 'input', 'a'], 
                               text=re.compile(text_pattern, re.I))
        if buttons:
            for button in buttons:
                if not button.get('disabled'):
                    availability_indicators.append('buy_button_found')
                    break
    
    # 通用缺货文本检测
    out_of_stock_patterns = [
        'out of stock', 'sold out', '在庫切れ', '在庫なし', 
        '缺货', '售完', 'unavailable', 'temporarily unavailable'
    ]
    
    page_text = soup.get_text().lower()
    for pattern in out_of_stock_patterns:
        if pattern.lower() in page_text:
            availability_indicators.append('out_of_stock_text')
            break
    
    # 通用价格检测
    price_patterns = [
        r'[¥￥]\s*[\d,]+',  # 日元
        r'[\d,]+\s*[円元]',  # 日元/人民币
        r'\$\s*[\d,]+\.?\d*',  # 美元
        r'€\s*[\d,]+\.?\d*',  # 欧元
        r'£\s*[\d,]+\.?\d*'   # 英镑
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, page_text)
        if matches:
            # 取第一个找到的价格
            price_str = re.sub(r'[¥￥$€£円元,\s]', '', matches[0])
            try:
                result['price'] = float(price_str)
                availability_indicators.append('price_found')
                break
            except ValueError:
                continue
    
    result['indicators'] = availability_indicators
    
    # 综合判断
    result['is_available'] = (
        'buy_button_found' in availability_indicators and
        'out_of_stock_text' not in availability_indicators and
        'price_found' in availability_indicators
    )
    
    if result['is_available']:
        result['stock_status'] = 'in_stock'
    elif 'out_of_stock_text' in availability_indicators:
        result['stock_status'] = 'out_of_stock'
    
    return result