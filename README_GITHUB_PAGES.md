# GitHub Actions + GitHub Pages 自動化部署指南

## 🎯 目標
使用 GitHub Actions 自動執行爬蟲，並透過 GitHub Pages 提供資料 API 服務

## 📋 完整配置步驟

### 1. GitHub Repository 設置

1. **將您的專案推送到 GitHub：**
   ```bash
   git init
   git add .
   git commit -m "初始化爬蟲自動化專案"
   git branch -M main
   git remote add origin https://github.com/您的用戶名/crawls-web.git
   git push -u origin main
   ```

2. **啟用 GitHub Actions：**
   - 到您的 GitHub repository
   - 點擊 "Actions" 選項卡
   - GitHub 會自動偵測 `.github/workflows/auto-crawler.yml`

3. **設置 GitHub Pages：**
   - 到 repository 的 "Settings" > "Pages"
   - Source 選擇 "GitHub Actions"
   - 或選擇 "Deploy from a branch" > "main" > "/docs"

### 2. 檔案結構檢查

確保您有以下檔案：

```
crawls-web/
├── .github/
│   └── workflows/
│       └── auto-crawler.yml          # GitHub Actions 工作流程
├── docs/                            # GitHub Pages 根目錄
│   ├── index.html                   # 主頁
│   └── data/                        # API 資料目錄
│       ├── daily_deals.json         # 每日促銷
│       ├── stats.json               # 統計資料
│       ├── crawler_status.json      # 爬蟲狀態
│       ├── yahoo_products.json      # Yahoo 商品
│       ├── pchome_products.json     # PChome 商品
│       ├── routn_products.json      # 露天商品
│       ├── carrefour_products.json  # 家樂福商品
│       └── backups/                 # JSON 備份
├── crawlers/                        # 爬蟲腳本目錄
├── crawler_manager.py               # 爬蟲管理器
├── crawler_database.py              # 資料庫管理
├── generate_github_pages.py         # GitHub Pages 資料生成器
├── github_actions_crawler.py        # GitHub Actions 專用爬蟲
└── requirements.txt                 # Python 依賴
```

### 3. 自動化排程

您的 GitHub Actions 將：

- **每天 3 次自動執行：**
  - 早上 8:00 (UTC 00:00)
  - 下午 2:00 (UTC 06:00)  
  - 晚上 8:00 (UTC 12:00)

- **手動觸發：**
  - 到 GitHub "Actions" 選項卡
  - 點擊 "自動化爬蟲與部署"
  - 點擊 "Run workflow"

### 4. 執行流程

每次自動執行會：

1. **環境設置：**
   - 安裝 Python 3.9
   - 安裝 Chrome 瀏覽器與 ChromeDriver
   - 安裝 Python 依賴

2. **爬蟲執行：**
   - 執行每日促銷爬蟲 (Yahoo 秒殺、PChome 促銷)
   - 執行一般爬蟲 (Yahoo、PChome、露天、家樂福)
   - 資料自動儲存到 SQLite 與 JSON

3. **資料處理：**
   - 從 SQLite 匯出最新資料
   - 生成 GitHub Pages JSON API
   - 複製 JSON 備份檔案

4. **部署更新：**
   - 提交更新的資料檔案
   - 自動部署到 GitHub Pages

### 5. API 端點

部署後，您的 GitHub Pages 將提供以下 API：

```
https://您的用戶名.github.io/crawls-web/
├── data/daily_deals.json           # 每日促銷商品
├── data/stats.json                 # 整體統計
├── data/crawler_status.json        # 爬蟲執行狀態
├── data/yahoo_products.json        # Yahoo 商品
├── data/pchome_products.json       # PChome 商品
├── data/routn_products.json        # 露天商品
├── data/carrefour_products.json    # 家樂福商品
└── data/backups/                   # 歷史資料備份
```

### 6. 資料格式

每個 JSON API 都包含：

```json
{
  "update_time": "2025-06-25T16:30:00",
  "total_products": 50,
  "platform": "yahoo",
  "products": [
    {
      "title": "商品標題",
      "price": "$1,200",
      "price_numeric": 1200,
      "platform": "yahoo",
      "image_url": "圖片網址",
      "product_url": "商品網址",
      "crawl_time": "2025-06-25T16:30:00"
    }
  ]
}
```

### 7. 監控與除錯

1. **查看執行狀態：**
   - GitHub "Actions" 選項卡
   - 點擊最新的工作流程執行

2. **查看執行日誌：**
   - 點擊具體的工作步驟
   - 查看詳細的執行輸出

3. **GitHub Pages 狀態：**
   - "Settings" > "Pages"
   - 查看部署狀態與錯誤

### 8. 自訂配置

您可以透過修改以下檔案來自訂：

- **`.github/workflows/auto-crawler.yml`** - 修改執行時間、參數
- **`github_actions_crawler.py`** - 調整爬蟲執行邏輯
- **`generate_github_pages.py`** - 自訂 API 資料格式
- **`docs/index.html`** - 修改前端顯示

### 9. 成本與限制

- **GitHub Actions：** 每月 2000 分鐘免費額度
- **GitHub Pages：** 完全免費，1GB 儲存空間
- **頻率限制：** 建議不超過每小時 1 次執行

### 10. 故障排除

**常見問題：**

1. **爬蟲執行失敗：**
   - 檢查網站是否變更結構
   - 確認 ChromeDriver 版本相容性

2. **GitHub Pages 未更新：**
   - 檢查 `docs/` 目錄是否有新檔案
   - 確認 Git 提交是否成功

3. **API 資料為空：**
   - 檢查 SQLite 資料庫是否有資料
   - 確認爬蟲是否成功執行

### 11. 下一步

成功部署後，您可以：

- 設置 Discord/Slack 通知
- 添加更多爬蟲平台
- 實現資料分析與趨勢監控
- 建立商品價格追蹤功能

---

## 🚀 立即開始

1. 確認所有檔案都在正確位置
2. 推送到 GitHub repository
3. 啟用 GitHub Actions 和 GitHub Pages
4. 等待第一次自動執行
5. 查看您的 GitHub Pages 網站！

您的自動化爬蟲系統將每天自動更新，提供最新的商品價格資料！
