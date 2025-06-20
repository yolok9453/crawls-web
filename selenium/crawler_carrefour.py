from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging

class CarrefourCrawler:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.base_url = "https://online.carrefour.com.tw"
        
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
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            logging.error(f"WebDriver 設置失敗: {e}")
            return False
    
    def search_products(self, keyword, max_pages=10, target_count=None):
        """搜尋商品
        
        Args:
            keyword (str): 搜尋關鍵字
            max_pages (int): 最大爬取頁數（防止無限循環）
            target_count (int): 目標商品數量，達到後停止爬取
        """
        if not self.setup_driver():
            return []
        
        try:
            all_products = []
            products_per_page = 24  # Carrefour 每頁顯示24個商品
            
            for page in range(1, max_pages + 1):
                logging.info(f"正在爬取第 {page} 頁...")
                
                # 計算當前頁的 start 參數
                start = (page - 1) * products_per_page
                
                # 建構搜尋URL - 使用 start 參數來控制分頁
                if page == 1:
                    # 第一頁使用原始URL
                    search_url = f"{self.base_url}/zh/search/?q={keyword}"
                else:
                    # 後續頁面使用 start 參數
                    search_url = f"{self.base_url}/zh/search/?q={keyword}&&start={start}"
                
                logging.info(f"訪問URL: {search_url}")
                self.driver.get(search_url)
                
                # 等待頁面載入
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    time.sleep(3)  # 額外等待確保商品載入
                except TimeoutException:
                    logging.warning(f"第 {page} 頁載入超時")
                    break
                
                # 爬取當前頁面的商品
                products = self.extract_products_from_page()
                
                if not products:
                    logging.info(f"第 {page} 頁沒有找到商品，可能已到達最後一頁")
                    break
                
                all_products.extend(products)
                logging.info(f"本頁爬取到 {len(products)} 個商品，總計 {len(all_products)} 個商品")
                
                # 檢查是否達到目標數量
                if target_count and len(all_products) >= target_count:
                    logging.info(f"已達到目標數量 {target_count}，停止爬取")
                    return all_products[:target_count]  # 返回精確的數量
                
                # 檢查是否還有更多頁面
                if not self.has_more_pages():
                    logging.info("已到達最後一頁")
                    break
                
                time.sleep(2)  # 避免請求過於頻繁
            
            return all_products
            
        except Exception as e:
            logging.error(f"搜尋商品時發生錯誤: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    def extract_products_from_page(self):
        """從當前頁面提取商品資訊"""
        products = []
        
        try:            # 商品容器選擇器 - 按優先級排序
            container_selectors = [
                ".hot-recommend-item",     # 主要容器：完整的商品項目（已確認有效）
                "[data-pid]",              # 備用：有商品ID的元素
                "a.gtm-product-alink"      # 備用：直接使用商品連結作為容器
            ]
            
            product_containers = []
            successful_selector = None
            
            # 嘗試每個選擇器
            for selector in container_selectors:
                try:
                    logging.info(f"嘗試選擇器: {selector}")
                    containers = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if containers:
                        product_containers = containers
                        successful_selector = selector
                        logging.info(f"成功找到 {len(containers)} 個容器，使用選擇器: {selector}")
                        break
                except TimeoutException:
                    continue
            
            # 如果沒有找到任何容器，嘗試查找頁面上的所有連結
            if not product_containers:
                logging.warning("未找到商品容器，嘗試直接查找商品連結")
                try:
                    product_containers = self.driver.find_elements(By.CSS_SELECTOR, "a.gtm-product-alink")
                    if product_containers:
                        successful_selector = "a.gtm-product-alink"
                        logging.info(f"直接找到 {len(product_containers)} 個商品連結")
                except:
                    pass
            
            # 如果還是沒有找到，列出頁面上的一些元素供調試
            if not product_containers:
                logging.error("無法找到任何商品容器")
                # 列出頁面上可能的元素
                try:
                    all_divs = self.driver.find_elements(By.TAG_NAME, "div")[:10]
                    logging.info(f"頁面上前10個div元素的類別:")
                    for i, div in enumerate(all_divs):
                        class_name = div.get_attribute("class")
                        if class_name:
                            logging.info(f"  div {i+1}: class='{class_name}'")
                except:
                    pass
                return []
            
            # 處理找到的商品容器
            logging.info(f"開始處理 {len(product_containers)} 個商品容器...")
            
            for i, container in enumerate(product_containers):
                try:
                    product_data = self.extract_single_product(container)
                    if product_data:
                        products.append(product_data)
                except Exception as e:
                    logging.warning(f"提取單個商品資訊時發生錯誤: {e}")
                    continue
            
        except TimeoutException:
            logging.warning("等待商品載入超時")
        except Exception as e:
            logging.error(f"提取商品資訊時發生錯誤: {e}")
        
        return products
    
    def extract_single_product(self, container):
        """從商品容器中提取單個商品的詳細資訊"""
        try:            # 商品名稱和連結 - 根據提供的完整HTML標籤結構
            # <div class="desc-operation-wrapper"><div class="commodity-desc"><div><a href="/zh/apple/A260007873901.html" title="...">商品名稱</a></div></div>
            name_link_selectors = [
                ".commodity-desc a",       # 主要選擇器：商品描述容器中的連結
                ".commodity-desc div a",   # 更具體的路徑
                "a.gtm-product-alink",     # 備用：Carrefour 的商品連結類別
                "a[data-pid]",             # 有商品ID的連結
                "a[data-name]",            # 有商品名稱的連結
                "a[href*='/zh/']",         # 匹配包含 /zh/ 的連結
                "a[title]",                # 匹配有 title 屬性的連結
                "a"                        # 一般的連結標籤
            ]
            
            name = None
            link = None
            product_id = None
            brand = None
            
            # 嘗試從 <a> 標籤同時獲取商品名稱、連結和其他資訊
            for selector in name_link_selectors:
                try:
                    element = container.find_element(By.CSS_SELECTOR, selector)
                    
                    # 優先從 data-name 屬性獲取商品名稱
                    potential_name = element.get_attribute("data-name")
                    if not potential_name:
                        potential_name = element.text.strip()
                    
                    potential_link = element.get_attribute("href")
                    
                    # 檢查是否是有效的商品名稱
                    if potential_name and len(potential_name) > 5:
                        name = potential_name
                        link = potential_link
                        
                        # 獲取額外的商品資訊
                        product_id = element.get_attribute("data-pid")
                        brand = element.get_attribute("data-brand")
                        
                        break
                except NoSuchElementException:
                    continue
            
            # 商品價格 - 根據提供的HTML標籤: <div class="current-price"><em>$49,490</em><i></i></div>
            price_selectors = [
                ".current-price em",  # 主要選擇器：價格在 current-price 類別下的 em 標籤中
                ".current-price",     # 備用：整個 current-price div
                ".price em",          # 其他可能的價格格式
                ".product-price em",
                ".special-price em",
                ".price-value em",
                ".price",
                ".product-price"
            ]
            price = self.get_text_by_selectors(container, price_selectors, "商品價格")
            
            # 確保連結是完整的URL
            if link and not link.startswith('http'):
                link = self.base_url + link
            
            # 商品圖片 - 根據提供的HTML標籤: <img class="m_lazyload" src="..." alt="..." title="...">
            image_selectors = [
                ".box-img img.m_lazyload",  # 更具體的路徑：在 box-img 容器中的懶加載圖片
                "img.m_lazyload",           # 主要選擇器：Carrefour 的懶加載圖片
                "img[alt]",                 # 有 alt 屬性的圖片
                "img[title]",               # 有 title 屬性的圖片
                "img",                      # 一般的圖片標籤
                ".product-image img",       # 產品圖片容器中的圖片
                "[data-testid='product-image'] img"
            ]
            image_url = self.get_attribute_by_selectors(container, image_selectors, "src", "商品圖片")
            
            # 如果 src 沒有值，嘗試其他可能的圖片屬性
            if not image_url:
                image_url = self.get_attribute_by_selectors(container, image_selectors, "data-src", "商品圖片")
            if not image_url:
                image_url = self.get_attribute_by_selectors(container, image_selectors, "data-lazy-src", "商品圖片")
              # 只有當商品名稱存在時才返回資料
            if name:
                product_data = {
                    'title': name.strip(),
                    'price': self.clean_price(price) if price else "價格未提供",
                    'image_url': image_url if image_url else "",
                    'url': link if link else "",
                    'platform': 'carrefour'
                }
                
                # 加入額外的商品資訊（如果有的話）
                if product_id:
                    product_data['product_id'] = product_id
                if brand:
                    product_data['brand'] = brand
                
                return product_data
        
        except Exception as e:
            logging.warning(f"提取商品詳細資訊時發生錯誤: {e}")
        
        return None
    
    def get_text_by_selectors(self, container, selectors, field_name):
        """嘗試多個選擇器來獲取文本"""
        for selector in selectors:
            try:
                element = container.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue
        
        logging.warning(f"無法找到 {field_name}")
        return None
    
    def get_attribute_by_selectors(self, container, selectors, attribute, field_name):
        """嘗試多個選擇器來獲取屬性"""
        for selector in selectors:
            try:
                element = container.find_element(By.CSS_SELECTOR, selector)
                attr_value = element.get_attribute(attribute)
                if attr_value:
                    return attr_value
            except NoSuchElementException:
                continue
        
        logging.warning(f"無法找到 {field_name}")
        return None
    
    def clean_price(self, price_text):
        """清理價格文本"""
        if not price_text:
            return "價格未提供"
        
        # 移除多餘的空格和字符
        import re
        price_text = re.sub(r'[^\d.,NT$元]', '', price_text)
        return price_text.strip()
    
    def go_to_next_page(self):
        """翻到下一頁"""
        try:
            # 請根據實際的下一頁按鈕選擇器調整
            next_button_selectors = [
                "a[aria-label='下一頁']",
                ".pagination-next",
                ".next-page",
                "[data-testid='next-page']"
            ]
            
            for selector in next_button_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled():
                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(3)
                        return True
                except NoSuchElementException:
                    continue
            
            return False
        except Exception as e:
            logging.warning(f"翻頁時發生錯誤: {e}")
            return False
    
    def has_more_pages(self):
        """檢查是否還有更多頁面"""
        try:
            # 檢查分頁容器是否存在
            pagination = self.driver.find_element(By.ID, "pagination")
            
            # 查找下一頁按鈕
            next_buttons = pagination.find_elements(By.CSS_SELECTOR, "a[onclick*='p_page'] img[alt='next']")
            
            for next_img in next_buttons:
                try:
                    # 獲取包含圖片的連結
                    next_button = next_img.find_element(By.XPATH, "..")
                    # 檢查按鈕所在的 li 元素是否被禁用
                    li_element = next_button.find_element(By.XPATH, "..")
                    li_class = li_element.get_attribute("class") or ""
                    
                    if "disabled" not in li_class:
                        logging.info("找到可用的下一頁按鈕")
                        return True
                except NoSuchElementException:
                    continue
            
            logging.info("所有下一頁按鈕都已禁用")
            return False
            
        except NoSuchElementException:
            logging.warning("未找到分頁區域")
            return False
        except Exception as e:
            logging.warning(f"檢查分頁狀態時發生錯誤: {e}")
            return False

def crawl_carrefour(keyword, max_pages=10, headless=True, target_count=None):
    """
    爬取 Carrefour 商品資訊的主函數
    
    Args:
        keyword (str): 搜尋關鍵字
        max_pages (int): 最大爬取頁數（防止無限循環）
        headless (bool): 是否使用無頭模式
        target_count (int): 目標商品數量，達到後停止爬取
    
    Returns:
        list: 商品資訊列表
    """
    crawler = CarrefourCrawler(headless=headless)
    return crawler.search_products(keyword, max_pages, target_count)

def run(keyword, max_products=100, min_price=0, max_price=999999):
    """
    爬蟲管理器調用的統一介面函數
    
    Args:
        keyword (str): 搜尋關鍵字
        max_products (int): 最大商品數量
        min_price (int): 最低價格範圍
        max_price (int): 最高價格範圍
    
    Returns:
        list: 商品資訊列表
    """
    import re
    
    # 計算需要爬取的頁數（假設每頁約24個商品）
    max_pages = max(1, (max_products // 24) + 1)
    
    # 使用目標數量來精確控制爬取數量
    products = crawl_carrefour(keyword, max_pages=max_pages, headless=True, target_count=max_products)
    
    # 根據價格範圍過濾商品
    filtered_products = []
    for product in products:
        try:
            # 從價格字符串中提取數字
            price_str = product.get('price', '0')
            price_numbers = re.findall(r'\d+', price_str.replace(',', ''))
            if price_numbers:
                price = int(price_numbers[0])
                if min_price <= price <= max_price:
                    product['price'] = price  # 統一價格格式為數字
                    filtered_products.append(product)
        except (ValueError, TypeError):
            # 如果價格解析失敗，跳過價格過濾
            filtered_products.append(product)
    
    return filtered_products[:max_products]  # 確保不超過最大數量

if __name__ == "__main__":
    # 測試爬蟲
    keyword = "iPhone"
    products = crawl_carrefour(keyword, max_pages=5, headless=False, target_count=100)
    
    print(f"找到 {len(products)} 個商品:")
    for i, product in enumerate(products[:5], 1):
        print(f"{i}. {product['name']}")
        print(f"   價格: {product['price']}")
        print(f"   連結: {product['link']}")
        print(f"   圖片: {product['image_url']}")
        print()