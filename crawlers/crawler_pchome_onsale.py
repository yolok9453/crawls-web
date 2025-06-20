from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import re
import json
import os
from datetime import datetime

class PChomeOnsaleCrawler:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.base_url = "https://24h.pchome.com.tw"
        self.onsale_url = "https://24h.pchome.com.tw/onsale/"
        
    def setup_driver(self):
        """設置 Chrome WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            # 方法1: 使用 webdriver-manager 自動管理 ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logging.info("使用 webdriver-manager 成功設置 WebDriver")
            except Exception as wdm_error:
                logging.warning(f"webdriver-manager 失敗: {wdm_error}")
                
                # 方法2: 嘗試使用系統路徑中的 chromedriver
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    logging.info("使用系統路徑中的 ChromeDriver 成功設置 WebDriver")
                except Exception as system_error:
                    logging.warning(f"系統 ChromeDriver 失敗: {system_error}")
                    
                    # 方法3: 嘗試指定常見的 ChromeDriver 路徑
                    common_paths = [
                        "chromedriver.exe",
                        "C:\\chromedriver\\chromedriver.exe",
                        "C:\\Program Files\\Google\\Chrome\\Application\\chromedriver.exe"
                    ]
                    
                    for path in common_paths:
                        try:
                            if os.path.exists(path):
                                service = Service(path)
                                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                                logging.info(f"使用路徑 {path} 成功設置 WebDriver")
                                break
                        except Exception:
                            continue
                    
                    if not self.driver:
                        raise Exception("所有 ChromeDriver 設置方法都失敗")
            
            self.driver.implicitly_wait(10)
            return True
            
        except Exception as e:
            logging.error(f"WebDriver 設置失敗: {e}")
            logging.error("請確保已安裝 Chrome 瀏覽器，或下載 ChromeDriver 並放置在系統路徑中")
            return False
    
    def crawl_onsale_products(self, max_products=None):
        """爬取 PChome 線上購物特價商品頁面"""
        if not self.setup_driver():
            return []
        
        try:
            logging.info(f"正在訪問 PChome 特價頁面: {self.onsale_url}")
            self.driver.get(self.onsale_url)
            
            # 等待頁面載入
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(5)  # 額外等待確保商品載入完成
            except TimeoutException:
                logging.warning("頁面載入超時")
                return []
            
            # 滾動頁面以確保所有商品都載入
            self.scroll_to_load_products()
            
            # 爬取頁面上的所有商品
            products = self.extract_products_from_page()
            
            if max_products and len(products) > max_products:
                products = products[:max_products]
            
            logging.info(f"成功爬取到 {len(products)} 個商品")
            return products
            
        except Exception as e:
            logging.error(f"爬取商品時發生錯誤: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    def scroll_to_load_products(self):
        """滾動頁面以載入更多商品，並確保圖片都載入完成"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 首先滾動到底部載入所有商品
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # 增加等待時間確保載入完成
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                last_height = new_height
            
            # 滾動回頂部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # 慢速滾動一遍，確保所有圖片都觸發載入
            logging.info("正在慢速滾動以載入所有圖片...")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            
            current_position = 0
            while current_position < total_height:
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(1)  # 給圖片載入時間
                current_position += viewport_height // 2  # 每次滾動半個視窗高度
            
            # 最後滾動回頂部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
        except Exception as e:
            logging.warning(f"滾動頁面時發生錯誤: {e}")
    
    def extract_products_from_page(self):
        """從頁面提取商品資訊"""
        products = []
        
        try:            # 找到商品容器
            product_containers = []
            container_selectors = [".c-prodInfoV2", "[data-gtm-item-id]"]
            
            for selector in container_selectors:
                try:
                    containers = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if containers:
                        product_containers = containers
                        logging.info(f"成功找到 {len(containers)} 個容器，使用選擇器: {selector}")
                        break
                except TimeoutException:
                    continue
            
            if not product_containers:
                logging.error("無法找到任何商品容器")
                return []
            
            # 處理找到的商品容器
            for i, container in enumerate(product_containers):
                try:
                    product_data = self.extract_single_product(container)
                    if product_data:
                        products.append(product_data)
                except Exception as e:
                    logging.warning(f"提取第 {i+1} 個商品資訊時發生錯誤: {e}")
                    continue
            
        except Exception as e:
            logging.error(f"提取商品資訊時發生錯誤: {e}")
        
        return products
      
    def extract_single_product(self, container):
        """從商品容器中提取單個商品的詳細資訊"""
        try:
            # 商品標題
            title = self.get_text_by_selectors(container, [".c-prodInfoV2__title"])
            
            # 商品價格
            price = self.get_text_by_selectors(container, [".c-prodInfoV2__priceValue"])
            
            # 商品圖片 - 處理懶加載問題
            image_url = self.get_image_url(container)
            
            # 商品連結
            link = self.get_attribute_by_selectors(container, ["a[href]"], "href")
            
            # 確保連結是完整的URL
            if link and not link.startswith('http'):
                if link.startswith('/'):
                    link = self.base_url + link
                else:
                    link = self.base_url + '/' + link
            
            # 只有當商品標題存在時才返回資料
            if title:
                return {
                    'title': title.strip(),
                    'price': price if price else "價格未提供",
                    'image_url': image_url if image_url else "",
                    'url': link if link else "",
                    'platform': 'pchome_onsale'
                }
        
        except Exception as e:
            logging.warning(f"提取商品詳細資訊時發生錯誤: {e}")
        
        return None
    
    def get_text_by_selectors(self, container, selectors):
        """嘗試多個選擇器來獲取文本"""
        for selector in selectors:
            try:
                element = container.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue
        return None
    
    def get_attribute_by_selectors(self, container, selectors, attribute):
        """嘗試多個選擇器來獲取屬性"""
        for selector in selectors:
            try:
                element = container.find_element(By.CSS_SELECTOR, selector)
                attr_value = element.get_attribute(attribute)
                if attr_value:
                    return attr_value
            except NoSuchElementException:
                continue
        return None
    
    def get_image_url(self, container):
        """獲取商品圖片URL，處理懶加載問題"""
        try:
            img_element = container.find_element(By.CSS_SELECTOR, ".c-prodInfoV2__img img")
            
            # 嘗試獲取多種可能的圖片屬性
            image_url = None
            
            # 1. 檢查 data-src 屬性（懶加載常用）
            image_url = img_element.get_attribute("data-src")
            if image_url and not image_url.endswith("mobile_loading.svg"):
                return image_url
            
            # 2. 檢查 data-original 屬性
            image_url = img_element.get_attribute("data-original")
            if image_url and not image_url.endswith("mobile_loading.svg"):
                return image_url
            
            # 3. 檢查 src 屬性
            image_url = img_element.get_attribute("src")
            if image_url and not image_url.endswith("mobile_loading.svg"):
                return image_url
              # 5. 嘗試從父元素的 style 屬性中獲取背景圖片
            parent_element = img_element.find_element(By.XPATH, "..")
            style = parent_element.get_attribute("style")
            if style and "background-image" in style:
                match = re.search(r'background-image:\s*url\(["\']?([^"\']*)["\']?\)', style)
                if match:
                    return match.group(1)
            
            return image_url if image_url else ""
            
        except Exception as e:
            logging.warning(f"獲取圖片URL時發生錯誤: {e}")
            return ""

def crawl_pchome_onsale(max_products=None, headless=True, save_json=True):
    """
    爬取 PChome 線上購物特價商品的主函數
    
    Args:
        max_products (int): 最大商品數量，None 表示爬取所有商品
        headless (bool): 是否使用無頭模式
        save_json (bool): 是否保存到 JSON 文件
    
    Returns:
        list: 商品資訊列表
    """
    crawler = PChomeOnsaleCrawler(headless=headless)
    products = crawler.crawl_onsale_products(max_products)
    
    # 如果指定要保存 JSON 且有商品資料，則保存
    if save_json and products:
        json_file = save_to_json(products, "pchome_onsale")
        if json_file:
            logging.info(f"商品資料已保存到: {json_file}")
    
    return products

def run(keyword=None, max_products=100, min_price=0, max_price=999999, save_json=True):
    """
    爬蟲管理器調用的統一介面函數
    
    Args:
        keyword (str): 搜尋關鍵字（此爬蟲不使用，因為是固定頁面）
        max_products (int): 最大商品數量
        min_price (int): 最低價格範圍
        max_price (int): 最高價格範圍
        save_json (bool): 是否保存到 JSON 文件
    
    Returns:
        list: 商品資訊列表
    """
    # 爬取 PChome 特價頁面商品，不進行複雜的價格解析
    products = crawl_pchome_onsale(max_products=max_products, headless=True, save_json=save_json)
    return products[:max_products]  # 確保不超過最大數量

def save_to_json(products, keyword="pchome_onsale"):
    """
    將商品資料保存到 JSON 文件
    
    Args:
        products (list): 商品資料列表
        keyword (str): 關鍵字，用於文件命名
    
    Returns:
        str: 保存的文件路徑
    """
    try:
        # 確保 crawl_data 目錄存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "crawl_data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawler_results_{keyword}.json"
        file_path = os.path.join(data_dir, filename)
        
        # 準備要保存的資料
        data_to_save = {
            "timestamp": datetime.now().isoformat(),
            "platform": "pchome_onsale",
            "keyword": keyword,
            "total_products": len(products),
            "products": products
        }
        
        # 保存到 JSON 文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        logging.info(f"成功保存 {len(products)} 個商品到: {file_path}")
        return file_path
        
    except Exception as e:
        logging.error(f"保存 JSON 文件時發生錯誤: {e}")
        return None

if __name__ == "__main__":
    # 測試爬蟲
    logging.basicConfig(level=logging.INFO)
    
    # 爬取商品並保存到 JSON
    products = crawl_pchome_onsale(max_products=100, headless=False, save_json=True)
    
    print(f"找到 {len(products)} 個商品:")
    for i, product in enumerate(products[:5], 1):
        print(f"{i}. {product['title']}")
        print(f"   價格: {product['price']}")
        print(f"   連結: {product['url']}")
        print(f"   圖片: {product['image_url']}")
        print()
    
    if len(products) > 5:
        print(f"... 還有 {len(products) - 5} 個商品")
        print("完整資料已保存到 JSON 文件中")
