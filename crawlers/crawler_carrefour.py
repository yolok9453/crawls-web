import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
from typing import List, Dict
import os
import uuid

def get_headers() -> Dict:
    """生成模擬的請求頭"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

def run(keyword: str, max_products: int = 100, min_price: int = 0, max_price: int = 999999) -> List[Dict]:
    """
    爬取家樂福線上購物的商品資訊 (根據 2025 年版面更新，支援分頁)
    
    注意：本版本使用 requests + BeautifulSoup，輕量級且快速
    如果此版本因反爬蟲機制失效，可使用 selenium/crawler_carrefour_selenium.py 備用版本

    Args:
        keyword (str): 要搜尋的商品關鍵字
        max_products (int): 最大商品數量限制
        min_price (int): 最低價格篩選
        max_price (int): 最高價格篩選

    Returns:
        List[Dict]: 商品資訊列表
    """
    products = []
    page_start = 0
    headers = get_headers()
    
    print(f"開始爬取家樂福商品：'{keyword}'...")
    
    while len(products) < max_products:
        # 家樂福搜尋用的 URL，加上分頁參數
        url = f"https://online.carrefour.com.tw/zh/search/?q={keyword}&start={page_start}"
        
        try:
            print(f"正在爬取第 {page_start//20 + 1} 頁...")
            
            # 發送 GET 請求
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 找到所有包含商品資訊的 div 區塊
            product_list = soup.find_all('div', class_='hot-recommend-item line')

            if not product_list:
                print(f"第 {page_start//20 + 1} 頁找不到任何相關商品，停止爬取")
                break

            # 網站基底 URL，用於組合完整的商品連結
            base_url = "https://online.carrefour.com.tw"
            page_products = []

            # 遍歷每一個商品區塊並提取所需資訊
            for product in product_list:
                try:
                    # 提取商品標題和連結
                    desc_div = product.find('div', class_='commodity-desc')
                    link_tag = desc_div.find('a') if desc_div else None
                    
                    title = link_tag.text.strip() if link_tag else 'N/A'
                    relative_link = link_tag['href'] if link_tag else ''
                    full_link = base_url + relative_link if relative_link else 'N/A'

                    # 提取商品價格
                    price_tag = product.find('div', class_='current-price')
                    price_em = price_tag.find('em') if price_tag else None
                    price_text = price_em.text.strip() if price_em else 'N/A'
                    
                    # 嘗試提取價格數字
                    try:
                        price = int(''.join(filter(str.isdigit, price_text))) if price_text != 'N/A' else 0
                    except:
                        price = 0

                    # 價格篩選
                    if price < min_price or price > max_price:
                        continue

                    # 提取商品圖片 URL
                    img_tag = product.find('img', class_='m_lazyload')
                    img_url = img_tag.get('data-src', img_tag.get('src', 'N/A')) if img_tag else 'N/A'

                    # 將提取的資料存成一個 dictionary，格式與其他爬蟲一致
                    product_info = {
                        "title": title,
                        "price": price,
                        "image_url": img_url,
                        "url": full_link,
                        "platform": "Carrefour"
                    }
                    page_products.append(product_info)
                    
                except Exception as e:
                    print(f"解析單一商品時發生錯誤: {e}")
                    continue

            # 如果這一頁沒有找到商品，停止爬取
            if not page_products:
                print(f"第 {page_start//20 + 1} 頁沒有找到有效商品，停止爬取")
                break

            products.extend(page_products)
            print(f"第 {page_start//20 + 1} 頁獲取到 {len(page_products)} 個商品")

            # 檢查是否達到最大商品數量
            if len(products) >= max_products:
                break

            # 檢查這一頁商品數量是否少於預期，如果是則可能是最後一頁
            if len(page_products) < 20:
                print(f"第 {page_start//20 + 1} 頁僅有 {len(page_products)} 個商品，可能是最後一頁")
                break

            # 更新頁面起始位置
            page_start += 20
            
            # 延遲1-2秒，避免被網站阻擋
            time.sleep(random.uniform(1, 2))

        except requests.exceptions.RequestException as e:
            print(f"請求第 {page_start//20 + 1} 頁時發生錯誤: {e}")
            break
        except Exception as e:
            print(f"處理第 {page_start//20 + 1} 頁時發生未知錯誤: {e}")
            break

    # 限制返回的商品數量
    products = products[:max_products]
    print(f"總共獲取到 {len(products)} 個家樂福商品")
    return products

def main(keyword: str, output_file: str = None, max_products: int = 100) -> None:
    """主函數：爬取家樂福商品資訊並保存為JSON(測試用)"""
    print(f"開始爬取關鍵字: {keyword}")
    
    # 獲取商品詳情
    products = run(keyword, max_products)
    print(f"獲取到 {len(products)} 個商品")
    
    if not products:
        print("未找到任何商品")
        return
    
    # 整理輸出數據
    output_data = {
        "keyword": keyword,
        "total_products": len(products),
        "products": products,
        "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 保存為JSON文件
    if not output_file:
        os.makedirs("./crawl_data", exist_ok=True)
        output_file = f"./crawl_data/carrefour_{keyword}_{uuid.uuid4().hex}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"結果已保存至 {output_file}")

if __name__ == "__main__":
    # 計算程式使用時間
    start_time = time.time()
    main("冰淇淋", max_products=100)
    end_time = time.time()
    print(f"程式執行時間: {end_time - start_time:.2f} 秒")

    