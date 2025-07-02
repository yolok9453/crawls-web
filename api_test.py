#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
詳細 API 測試
"""

import json
from web_app import app

def test_daily_deals_api():
    with app.test_client() as client:
        response = client.get('/api/daily-deals')
        data = response.get_json()
        
        print("=== API 完整回應 ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        print("\n=== 分析結果 ===")
        print(f"狀態: {data.get('status')}")
        print(f"總促銷數: {data.get('total_deals')}")
        print(f"daily_deals 長度: {len(data.get('daily_deals', []))}")
        print(f"daily_deals 內容: {data.get('daily_deals')}")

if __name__ == "__main__":
    test_daily_deals_api()
