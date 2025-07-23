# 🕷️ 爬蟲結果展示網站

一個功能完整的多平台電商爬蟲系統，具備Web界面、AI商品比較、即時監控等功能。

## ✨ 主要特色

### 🎯 多平台支援
- **PChome**: 一般商品 + 促銷商品
- **Yahoo購物**: 一般商品 + 搶購商品  
- **家樂福**: 線上購物商品
- **Routn**: 特色商品

### 🌐 現代化Web界面
- **響應式設計**: 支援桌面和行動裝置
- **即時執行**: 網頁端直接執行爬蟲
- **智能篩選**: 多維度商品篩選和排序
- **視覺化展示**: 卡片式和列表式檢視

### 🤖 AI智能比較
- **Gemini AI**: Google最新AI模型
- **智能分析**: 自動比較商品規格和價格
- **購買建議**: AI提供個人化推薦

## 🚀 快速開始

### 一鍵啟動 (推薦)
```bash
# Windows用戶
雙擊 start.bat

# 或命令列
python main.py
```

### 手動安裝
```bash
# 1. 安裝依賴
pip install -r config/requirements.txt

# 2. 啟動應用
python main.py
```

### 訪問網站
打開瀏覽器訪問: **http://localhost:5000**

## 📁 專案結構

```
crawls-web-master/
├── 📁 app/                     # Flask Web 應用
│   ├── web_app.py             # 主要 Web 應用程式
│   ├── static/                # 靜態資源 (CSS/JS)
│   └── templates/             # HTML 模板
├── 📁 core/                   # 核心功能模組
│   ├── crawler_manager.py    # 爬蟲管理器
│   ├── database.py           # 資料庫操作
│   ├── product_filter.py     # 商品篩選
│   └── services/             # 服務層
├── 📁 crawlers/              # 爬蟲實現
│   ├── crawler_pchome.py     # PChome 爬蟲
│   ├── crawler_yahoo.py      # Yahoo 購物爬蟲
│   └── ... (共6個爬蟲)
├── 📁 config/                # 配置檔案
├── 📁 data/                  # 資料庫檔案
├── 📁 crawl_data/           # 爬蟲結果資料
├── main.py                  # 主要入口點
└── start.bat               # Windows 啟動腳本
```

## 🌟 功能亮點

### 爬蟲管理
- **自動化載入**: 自動偵測和載入所有爬蟲模組
- **並行執行**: 多爬蟲同時執行，提升效率
- **錯誤處理**: 完善的異常處理機制
- **結果保存**: 自動保存為JSON格式

### Web界面功能
- **主控台**: 查看所有爬蟲結果和統計
- **爬蟲執行**: 即時執行爬蟲任務
- **每日促銷**: 專門的促銷商品頁面
- **商品詳情**: 詳細的商品資訊展示

### 數據處理
- **智能過濾**: 自動過濾重複和無效商品
- **價格分析**: 價格趨勢和統計分析
- **資料庫存儲**: SQLite 資料庫永久存儲
- **會話管理**: 爬取任務會話化管理
- **快取機制**: 提升查詢效能

## 🛠️ 技術架構

### 後端技術
- **Flask**: 輕量級Web框架
- **SQLite**: 嵌入式資料庫
- **Requests + BeautifulSoup**: 網頁爬取
- **Selenium**: 動態內容處理
- **Google Gemini API**: AI智能分析

### 前端技術
- **Bootstrap 5**: 響應式UI框架
- **JavaScript**: 前端互動邏輯
- **Font Awesome**: 圖標庫
- **AJAX**: 非同步資料載入

## 📱 使用說明

### 1. 執行爬蟲
1. 訪問 `/crawler` 頁面
2. 選擇要執行的平台
3. 輸入搜尋關鍵字
4. 設定商品數量和價格範圍
5. 點擊開始爬取

### 2. 查看結果
1. 在主頁面查看所有爬蟲結果
2. 使用篩選器按平台、時間篩選
3. 點擊查看詳情查看具體商品
4. 切換卡片/列表檢視模式

### 3. AI商品比較
1. 在商品詳情頁面選擇商品
2. 點擊AI比較功能
3. 查看AI分析結果和建議

### 4. 每日促銷
1. 訪問 `/daily-deals` 頁面
2. 查看最新促銷和搶購商品
3. 支援自動更新功能

## 📋 系統需求

- **作業系統**: Windows 10/11 (推薦)
- **Python**: 3.7 或更高版本
- **瀏覽器**: Chrome/Edge/Firefox
- **網路**: 穩定的網際網路連線

## 🔧 環境配置

### 安裝Chrome Driver
```bash
# 自動安裝 (推薦)
pip install webdriver-manager

# 手動下載
# 下載對應Chrome版本的ChromeDriver
# 放置在系統PATH中
```

### 設定AI功能 (可選)
```bash
# 1. 申請Google AI Studio API Key
# 2. 在config目錄建立.env檔案
# 3. 添加: GEMINI_API_KEY=your_api_key_here
```

## 🐛 常見問題

### Q: 爬蟲執行失敗
**A**: 檢查網路連線和目標網站可訪問性

### Q: Chrome Driver錯誤  
**A**: 確保Chrome瀏覽器已安裝，或安裝webdriver-manager

### Q: AI功能無法使用
**A**: 確認已設定GEMINI_API_KEY環境變數

### Q: 頁面載入緩慢
**A**: 檢查網路連線，確保CDN資源正常載入

## 📄 授權條款

本專案採用 MIT 授權條款，詳見 LICENSE 檔案。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來改善專案！

---

**享受爬蟲的樂趣！** 🎉
