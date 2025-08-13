import requests
import json
import time
import re
from typing import List, Dict
import uuid
from urllib.parse import quote
from datetime import datetime
import os

def get_headers() -> Dict:
    """生成模擬的請求頭"""
    return {
        "Accept": "application/json",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

def extract_price(price_text: str) -> int:
    """從價格文字中提取數字"""
    if not price_text:
        return 0
    # 使用正則表達式提取數字
    numbers = re.findall(r'[\d,]+', price_text.replace(',', ''))
    if numbers:
        try:
            return int(numbers[0])
        except:
            return 0
    return 0

def api_method(keyword: str, max_products: int, min_price: int, max_price: int) -> List[Dict]:
    """使用 API 方法爬取 PChome 商品"""
    print("🔄 使用 PChome API 方法...")
    
    products = []
    page = 1
    
    while len(products) < max_products:
        try:
            # 構建 API 請求
            url = "https://ecshweb.pchome.com.tw/search/v3.3/all/results"
            params = {
                "q": keyword,
                "page": page,
                "size": min(20, max_products - len(products)),
                "sort": "sale/dc"
            }
            
            print(f"   正在爬取第 {page} 頁...")
            
            response = requests.get(url, params=params, headers=get_headers(), timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 提取商品資訊
            if 'prods' in data:
                prods = data['prods']
                if not prods:
                    break
                
                page_products = []
                for prod in prods:
                    product_info = extract_product_info_api(prod)
                    if product_info:
                        # 價格過濾
                        price = product_info.get('price', 0)
                        if min_price <= price <= max_price:
                            page_products.append(product_info)
                
                print(f"   第 {page} 頁找到 {len(page_products)} 個商品")
                products.extend(page_products)
                
                if len(page_products) < 20:  # 如果少於 20 個，說明已經是最後一頁
                    break
                    
                page += 1
            else:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 請求失敗: {e}")
            break
        except Exception as e:
            print(f"❌ 解析 API 回應失敗: {e}")
            break
    
    # 去重複
    unique_products = []
    seen_urls = set()
    
    for product in products:
        if product.get('url') and product['url'] not in seen_urls:
            seen_urls.add(product['url'])
            unique_products.append(product)
    
    print(f"✅ API 方法成功獲取 {len(unique_products)} 個商品")
    return unique_products

def extract_product_info_api(prod_data: Dict) -> Dict:
    """從 API 回應中提取商品資訊"""
    try:
        # 提取基本資訊
        product_id = prod_data.get('Id', '')  # 注意是大寫的 Id
        title = prod_data.get('name', '')
        price = prod_data.get('price', 0)
        
        # 處理價格
        if isinstance(price, str):
            price = extract_price(price)
        
        # 構建 URL
        url = f"https://24h.pchome.com.tw/prod/{product_id}" if product_id else ""
        
        # 構建圖片 URL
        pic_b = prod_data.get('picB', '')
        image_url = f"https://cs-a.ecimg.tw{pic_b}" if pic_b else ""  # 移除 /items/ 前綴
        
        return {
            "title": title,
            "price": int(price) if price else 0,
            "image_url": image_url,
            "url": url,
            "platform": "PChome"
        }
        
    except Exception as e:
        return {}

def run(keyword: str, max_products: int = 100, min_price: int = 0, max_price: int = 999999) -> List[Dict]:
    """爬取PChome商品 - 純 API 方法
    
    Args:
        keyword (str): 搜索關鍵字
        max_products (int, optional): 最大商品數量限制. Defaults to 100.
        min_price (int): 最小價格過濾
        max_price (int): 最大價格過濾

    Returns:
        List[Dict]: 商品資訊列表
    """
    print(f"🔍 PChome 爬蟲啟動，搜尋關鍵字: {keyword}")
    
    # 使用純 API 方法
    products = api_method(keyword, max_products, min_price, max_price)
    
    print(f"✅ 總共獲取到 {len(products)} 個 PChome 商品")
    return products

def main(keyword: str, output_file: str = None, max_products: int = 100) -> None:
    """主函數：爬取PChome商品資訊並保存為JSON(測試用)"""
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
        output_file = f"./crawl_data/pchome_{keyword}_{uuid.uuid4().hex}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"結果已保存至 {output_file}")

if __name__ == "__main__":
    # 測試簡單關鍵字
    print("🔍 測試 PChome 爬蟲...")
    result = run("iPhone", max_products=5)
    print(f"✅ 獲得 {len(result)} 個商品")
    
    if result:
        print("📦 商品範例:")
        for i, product in enumerate(result[:2]):
            print(f"   {i+1}. {product['title'][:50]}... - ${product['price']}")
    
    # 保存測試結果
    with open("pchome_test.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"💾 結果已保存至 pchome_test.json")
