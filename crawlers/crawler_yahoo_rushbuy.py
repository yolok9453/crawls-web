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
from webdriver_manager.chrome import ChromeDriverManager
import brotli
import traceback

def get_cookies_and_token() -> tuple:
    """使用 Selenium 獲取必要的 cookies 和 token"""
    print("正在啟動瀏覽器...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
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
                        "platform": "Yahoo秒殺時時樂"
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
    
    

def run(max_products: int = 100) -> List[Dict]:
    """執行爬蟲"""
    products = []
    
    try:
        print("正在啟動瀏覽器...")
        driver = setup_driver()
        
        try:
            print("正在訪問 Yahoo 秒殺時時樂頁面...")
            driver.get("https://tw.buy.yahoo.com/rushbuy")
            
            # 等待頁面加載
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 從頁面直接提取商品
            products = get_products_from_page(driver)
            
            # 如果沒有找到商品，輸出更多調試資訊
            if not products:
                print("\n沒有找到商品，正在收集更多資訊...")
                print("頁面標題:", driver.title)
                print("頁面 URL:", driver.current_url)
                print("頁面原始碼片段:", driver.page_source[:500])
                
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        print("錯誤詳情:", traceback.format_exc())
    
    return products[:max_products]

def main(output_file: str = None, max_products: int = 100) -> None:
    """主函數"""
    print("開始爬取Yahoo秒殺時時樂商品:")
    products = run(max_products)
    
    if not products:
        print("未找到任何商品")
        return
        
    output_data = {
        "total_products": len(products),
        "products": products,
        "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if not output_file:
        os.makedirs("./crawl_data", exist_ok=True)
        # 使用時間戳格式，與其他爬蟲保持一致
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"./crawl_data/crawler_results_yahoo_rushbuy_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"結果已保存至 {output_file}")

if __name__ == "__main__":
    main(max_products=100)
