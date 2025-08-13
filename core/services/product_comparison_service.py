"""
商品比較服務模組
使用 Gemini AI 進行智能商品比較
"""

import json
import re


class ProductComparisonService:
    """商品比較服務類別"""
    
    def __init__(self, gemini_model=None):
        self.model = gemini_model
        self.similarity_threshold = 0.80
    
    def compare_products(self, target_product, candidate_products):
        """比較單個目標商品與候選商品"""
        if not self.model: 
            print("❌ AI 模型未初始化，使用備用比較方法")
            return self._fallback_comparison(target_product, candidate_products)
        
        max_candidates = 80
        if len(candidate_products) > max_candidates:
            print(f"候選商品數量 {len(candidate_products)} 超過限制，僅取前 {max_candidates} 個")
            candidate_products = candidate_products[:max_candidates]
        
        try:
            print(f"🤖 開始 AI 比較，目標商品: {target_product.get('title', '')[:50]}...")
            prompt = self._create_comparison_prompt(target_product, candidate_products)
            print(f"📝 提示詞長度: {len(prompt)} 字元")
            
            response = self.model.generate_content(prompt)
            response_text = response.text
            print(f"🤖 AI 原始回應長度: {len(response_text)} 字元")
            print(f"🤖 AI 原始回應內容:\n{response_text}")
            
            matches = self._parse_comparison_result(response_text)
            print(f"✅ 解析結果: {len(matches)} 個匹配項目")
            return matches
        except Exception as e:
            print(f"❌ AI 商品比較失敗: {e}，使用備用比較方法")
            import traceback
            traceback.print_exc()
            return self._fallback_comparison(target_product, candidate_products)
    
    def batch_compare_products(self, target_products, candidate_products):
        """批量比較多個目標商品與候選商品"""
        if not self.model: 
            print("❌ AI 模型未初始化，使用備用比較方法")
            return self._batch_fallback_comparison(target_products, candidate_products)
        
        max_candidates = 100  # 批量處理時稍微提高限制
        if len(candidate_products) > max_candidates:
            print(f"候選商品數量 {len(candidate_products)} 超過限制，僅取前 {max_candidates} 個")
            candidate_products = candidate_products[:max_candidates]
        
        try:
            print(f"🤖 開始批量 AI 比較，目標商品數: {len(target_products)}")
            prompt = self._create_batch_comparison_prompt(target_products, candidate_products)
            print(f"📝 批量提示詞長度: {len(prompt)} 字元")
            
            response = self.model.generate_content(prompt)
            response_text = response.text
            print(f"🤖 AI 批量回應長度: {len(response_text)} 字元")
            
            batch_results = self._parse_batch_comparison_result(response_text)
            print(f"✅ 批量解析結果: {len(batch_results)} 個目標商品的比較結果")
            return batch_results
        except Exception as e:
            print(f"❌ AI 批量比較失敗: {e}，使用備用比較方法")
            import traceback
            traceback.print_exc()
            return self._batch_fallback_comparison(target_products, candidate_products)

    def _create_comparison_prompt(self, target_product, candidate_products):
        """創建單個商品比較的提示詞"""
        target_title = target_product.get('title', '')
        target_platform = target_product.get('platform', '')
        target_price = target_product.get('price', 0)
        
        return f"""你是一個專業的商品比較分析師。請比較目標商品與候選商品，找出相同或相似的商品。

目標商品：{target_title} | {target_platform} | ${target_price}

候選商品列表：
{self._format_candidate_products(candidate_products)}

比較標準：
- 完全相同商品（同品牌同型號同規格） → 0.95-1.0
- 同品牌同型號但顏色/容量不同 → 0.85-0.94
- 同品牌同系列但規格不同 → 0.75-0.84
- 同類型商品同品牌 → 0.70-0.79
- 同類型商品不同品牌 → 0.60-0.69

⚠️ 重要指示：
1. 仔細比較商品名稱中的關鍵詞，如品牌、型號、功能
2. 如果是口罩，重點比較：醫療用/一般用、成人/兒童、數量、顏色
3. 如果是電子產品，重點比較：品牌、型號、功能、規格
4. 如果是日用品，重點比較：品牌、用途、規格、容量
5. 降低標準：即使不是完全相同，只要是同類商品就算相似
6. 必須找出至少3-5個相似商品，除非真的沒有任何相關商品

請回傳JSON格式結果：
{{"matches": [{{"index": 0, "similarity": 0.75, "reason": "同類型醫療口罩", "confidence": "中", "category": "部分相似"}}]}}

必須回傳至少1個匹配結果，除非候選商品完全無關。重要：請確保返回的index值在0到{len(candidate_products)-1}之間。"""

    def _create_batch_comparison_prompt(self, target_products, candidate_products):
        """創建批量比較的提示詞"""
        prompt = """你是一個專業的商品比較分析師。請一次性比較多個目標商品與候選商品清單，為每個目標商品找出最相似的候選商品。

目標商品清單：
"""
        for i, target in enumerate(target_products):
            prompt += f"\n目標商品{i+1}：{target.get('title', 'N/A')} | {target.get('platform', 'N/A')} | ${target.get('price', 0)}\n"
        
        prompt += "\n" + "="*50 + "\n候選商品清單：\n"
        for i, candidate in enumerate(candidate_products):
            prompt += f"{i}. {candidate.get('title', 'N/A')} | {candidate.get('platform', 'N/A')} | ${candidate.get('price', 0)}\n"
        
        prompt += f"""

比較標準：
- 完全相同商品（同品牌同型號同規格） → 0.95-1.0
- 同品牌同型號但顏色/容量不同 → 0.85-0.94
- 同品牌同系列但規格不同 → 0.75-0.84
- 同類型商品同品牌 → 0.70-0.79
- 同類型商品不同品牌 → 0.60-0.69

⚠️ 重要指示：
1. 仔細比較商品名稱中的關鍵詞，如品牌、型號、功能
2. 如果是口罩，重點比較：醫療用/一般用、成人/兒童、數量、顏色
3. 如果是電子產品，重點比較：品牌、型號、功能、規格
4. 如果是日用品，重點比較：品牌、用途、規格、容量
5. 降低標準：即使不是完全相同，只要是同類商品就算相似
6. 必須找出至少3-5個相似商品，除非真的沒有任何相關商品

請回傳JSON格式結果，包含每個目標商品的匹配結果：
{{
  "target_1": {{"matches": [{{"index": 0, "similarity": 0.85, "reason": "同品牌同型號", "confidence": "高", "category": "完全相似"}}]}},
  "target_2": {{"matches": [{{"index": 3, "similarity": 0.75, "reason": "同類型商品", "confidence": "中", "category": "部分相似"}}]}},
  ...
}}

必須為每個目標商品回傳至少1個匹配結果，除非候選商品完全無關。重要：請確保返回的index值在0到{len(candidate_products)-1}之間。"""
        return prompt

    def _format_candidate_products(self, products):
        """格式化候選商品列表"""
        formatted = []
        for i, product in enumerate(products):
            title = product.get('title', '') or product.get('name', '')
            platform = product.get('platform', '')
            price = product.get('price', 0)
            
            # 截取標題但保留重要信息
            if len(title) > 100:
                title = title[:100] + "..."
            
            product_info = f"{i}. {title} | {platform} | ${price}\n"
            formatted.append(product_info)
        return "".join(formatted)

    def _parse_comparison_result(self, response_text):
        """解析 AI 比較結果"""
        try:
            print(f"🔧 開始解析 AI 回應...")
            
            # 儲存完整回應到檔案以便調試
            with open('debug_ai_response.txt', 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"🔧 AI 完整回應已儲存到 debug_ai_response.txt")
            
            clean_text = response_text.strip().replace('```json', '').replace('```', '')
            print(f"🔧 清理後文本前200字元: {clean_text[:200]}")
            
            if not clean_text.startswith('{'):
                start_brace = clean_text.find('{')
                end_brace = clean_text.rfind('}')
                if start_brace != -1 and end_brace != -1:
                    clean_text = clean_text[start_brace:end_brace+1]
                    print(f"🔧 提取的 JSON 部分前200字元: {clean_text[:200]}")
                else:
                    print(f"❌ 無法找到 JSON 格式")
                    return []
                    
            result = json.loads(clean_text)
            matches = result.get('matches', [])
            print(f"✅ JSON 解析成功，找到 {len(matches)} 個匹配項目")
            for i, match in enumerate(matches):
                print(f"   {i+1}. 索引:{match.get('index')}, 相似度:{match.get('similarity')}")
            return matches
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失敗: {e}")
            print(f"❌ 嘗試解析的文本前500字元: {response_text[:500]}")
            
            # 嘗試修復常見的 JSON 格式問題
            try:
                # 移除可能的前綴文字
                if '{"matches":' in response_text:
                    start_idx = response_text.find('{"matches":')
                    end_idx = response_text.rfind('}')
                    if end_idx > start_idx:
                        fixed_json = response_text[start_idx:end_idx+1]
                        result = json.loads(fixed_json)
                        matches = result.get('matches', [])
                        print(f"✅ 修復後 JSON 解析成功，找到 {len(matches)} 個匹配項目")
                        return matches
            except Exception as fix_error:
                print(f"❌ JSON 修復嘗試失敗: {fix_error}")
            
            return []
        except Exception as e:
            print(f"❌ 其他解析錯誤: {e}")
            return []

    def _parse_batch_comparison_result(self, response_text):
        """解析批量比較結果"""
        batch_results = {}
        try:
            # 清理回應內容
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # 解析JSON
            data = json.loads(response_text)
            
            # 轉換為我們需要的格式
            for key, value in data.items():
                if key.startswith('target_'):
                    target_index = int(key.split('_')[1]) - 1  # 轉換為0-based index
                    matches = value.get('matches', [])
                    batch_results[target_index] = matches
                    
        except Exception as e:
            print(f"❌ 批量比較結果解析失敗: {e}")
            print(f"原始回應: {response_text}")
            batch_results = {}
        
        return batch_results

    def _batch_fallback_comparison(self, target_products, candidate_products):
        """批量備用比較方法"""
        batch_results = {}
        
        for i, target_product in enumerate(target_products):
            # 對每個目標商品使用原有的備用比較方法
            matches = self._fallback_comparison(target_product, candidate_products)
            batch_results[i] = matches
            
        return batch_results

    def _fallback_comparison(self, target_product, candidate_products):
        """
        備用商品比較方法，當 AI 不可用時使用
        基於關鍵字匹配來計算相似度
        """
        print("🔄 使用備用比較方法（基於關鍵字匹配）")
        
        target_title = target_product.get('title', '').lower()
        target_keywords = set(target_title.split())
        
        matches = []
        
        for i, candidate in enumerate(candidate_products):
            candidate_title = candidate.get('title', '').lower()
            candidate_keywords = set(candidate_title.split())
            
            # 計算關鍵字重疊度
            common_keywords = target_keywords.intersection(candidate_keywords)
            total_keywords = target_keywords.union(candidate_keywords)
            
            if total_keywords:
                similarity = len(common_keywords) / len(total_keywords)
                
                # 提高相似度計算的準確性
                # 如果包含主要關鍵字，增加相似度
                main_keywords = ['口罩', '醫療', '醫用', '成人', '防護', '平面', '立體',
                               'iPhone', 'iPad', 'AirPods', 'MacBook', 'Switch', 'PS5',
                               '筆電', '電腦', '耳機', '手機', '充電器', '滑鼠', '鍵盤']
                
                for keyword in main_keywords:
                    if keyword in target_title and keyword in candidate_title:
                        similarity += 0.15
                
                # 品牌匹配
                brands = ['永猷', 'CSD', '中衛', 'Motex', '摩戴舒', 'RST', 'Apple', 
                         'Samsung', 'Sony', 'Nintendo', 'ASUS', 'HP', 'Dell', 'Lenovo']
                for brand in brands:
                    if brand.lower() in target_title and brand.lower() in candidate_title:
                        similarity += 0.25
                
                # 型號匹配（數字和字母組合）
                target_models = re.findall(r'\b[A-Z0-9]+\b', target_title.upper())
                candidate_models = re.findall(r'\b[A-Z0-9]+\b', candidate_title.upper())
                
                common_models = set(target_models).intersection(set(candidate_models))
                if common_models:
                    similarity += 0.3
                
                # 確保相似度不超過 1.0
                similarity = min(similarity, 1.0)
                
                # 只保留相似度 >= 0.4 的商品
                if similarity >= 0.4:
                    matches.append({
                        'index': i,
                        'similarity': round(similarity, 2),
                        'reason': f'關鍵字匹配 {len(common_keywords)}/{len(total_keywords)}' + 
                                (f', 品牌匹配' if any(brand.lower() in target_title and brand.lower() in candidate_title for brand in brands) else '') +
                                (f', 型號匹配' if common_models else ''),
                        'confidence': '高' if similarity >= 0.7 else '中' if similarity >= 0.5 else '低',
                        'category': '高度相似' if similarity >= 0.8 else '部分相似'
                    })
        
        # 按相似度排序
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"🔄 備用比較方法找到 {len(matches)} 個匹配項目")
        return matches
