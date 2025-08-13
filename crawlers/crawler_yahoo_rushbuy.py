import os
import requests
import json
import time
from typing import List, Dict
import uuid
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import brotli
import traceback
import logging

def get_cookies_and_token() -> tuple:
    """使用 Selenium 獲取必要的 cookies 和 token"""
    print("正在啟動瀏覽器...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 使用環境變數或系統預設的 ChromeDriver 路徑
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
    if chromedriver_path and os.path.exists(chromedriver_path):
        driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    else:
        # 嘗試系統預設路徑
        driver = webdriver.Chrome(options=options)
    
    try:
        print("正在訪問 Yahoo 秒殺時時樂頁面...")
        driver.get("https://tw.buy.yahoo.com/rushbuy")
        
        # 等待頁面加載
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 獲取所有 cookies
        cookies = driver.get_cookies()
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        
        # 獲取頁面原始碼
        page_source = driver.page_source
        
        # 獲取 localStorage 中的 token
        local_storage = driver.execute_script("return window.localStorage;")
        
        print("已獲取頁面資料，正在分析...")
        
        return cookie_string, page_source, local_storage
        
    finally:
        driver.quit()

def get_headers(cookie_string: str, local_storage: dict) -> Dict:
    """生成請求標頭"""
    return {
        "accept": "application/json",
        "accept-encoding": "br",
        "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://tw.buy.yahoo.com",
        "referer": "https://tw.buy.yahoo.com/rushbuy",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "cookie": cookie_string,
        # 添加可能需要的認證頭
        "x-yahoo-token": local_storage.get("yahooToken", ""),
        "authorization": f"Bearer {local_storage.get('accessToken', '')}"
    }

def get_products_from_page(driver) -> List[Dict]:
    """從頁面 DOM 中直接提取商品資訊"""
    products = []
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # 找到所有商品區塊
        product_elements = driver.find_elements(By.CSS_SELECTOR, 'li[class*="RushbuyItem"]')
        print(f"共找到 {len(product_elements)} 個商品區塊")
        for element in product_elements:
            try:
                # 商品連結
                a_tag = element.find_element(By.TAG_NAME, "a")
                item_url = a_tag.get_attribute("href")
                # 商品圖片
                try:
                    img_tag = element.find_element(By.TAG_NAME, "img")
                    image_url = img_tag.get_attribute("src")
                except:
                    image_url = ""
                # 商品標題
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, '[class*="Title"], [class*="name"], h3, h4')
                    title = title_elem.text.strip()
                except:
                    title = element.text.strip()
                # 商品價格
                try:
                    price_elem = element.find_element(By.CSS_SELECTOR, '[class*="price"]')
                    import re
                    price_text = price_elem.text
                    if 'X' in price_text.upper():
                        continue  # 跳過價格有 X 的商品（未開賣或不明價格）
                    price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                    price = int(price_match.group().replace(',', '')) if price_match else 0
                except:
                    price = 0
                if title and item_url:
                    products.append({
                        "title": title,
                        "price": price,
                        "image_url": image_url,
                        "url": item_url,
                        "platform": "yahoo_rushbuy"
                    })
            except Exception as e:
                print(f"商品解析失敗: {e}")
                continue
        print(f"成功提取到 {len(products)} 個商品")
    except Exception as e:
        print(f"從頁面提取商品時發生錯誤: {str(e)}")
        print("錯誤詳情:", traceback.format_exc())
    return products

def setup_driver():
    """設置 Chrome WebDriver，包含錯誤處理和備用方案"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    
    
    
    # 方法2: 使用系統路徑中的 chromedriver
    try:
        print("嘗試使用系統路徑中的 ChromeDriver...")
        driver = webdriver.Chrome(options=options)
        print("✅ 系統 ChromeDriver 設置成功")
        return driver
    except Exception as e:
        print(f"⚠️ 系統 ChromeDriver 失敗: {e}")
    
    

def scroll_to_load_products(driver):
    """自動滾動頁面以載入所有商品"""
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    except Exception as e:
        logging.warning(f"滾動頁面時發生錯誤: {e}")

def run(keyword=None, max_products=100, min_price=0, max_price=999999, save_json=True):
    """統一介面，支援多參數，並自動存檔"""
    products = []
    try:
        logging.info("正在啟動瀏覽器...")
        driver = setup_driver()
        try:
            logging.info("正在訪問 Yahoo 秒殺時時樂頁面...")
            driver.get("https://tw.buy.yahoo.com/rushbuy")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            scroll_to_load_products(driver)
            products = get_products_from_page(driver)
            # 過濾價格範圍
            products = [p for p in products if min_price <= p.get('price', 0) <= max_price]
            if not products:
                logging.warning("未找到任何商品")
        finally:
            driver.quit()
    except Exception as e:
        logging.error(f"發生錯誤: {str(e)}")
        logging.error(traceback.format_exc())
    products = products[:max_products]
    if save_json and products:
        save_to_json(products, keyword="yahoo_rushbuy")
    return products

def save_to_json(products, keyword="yahoo_rushbuy"):
    """將商品資料保存到 JSON 文件"""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "crawl_data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawler_results_{keyword}.json"
        file_path = os.path.join(data_dir, filename)
        
        data_to_save = {
            "platform": "yahoo_rushbuy",
            "keyword": keyword,
            "total_products": len(products),
            "products": products,
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        logging.info(f"成功保存 {len(products)} 個商品到: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"保存 JSON 文件時發生錯誤: {e}")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    products = run(max_products=100, save_json=True)
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
