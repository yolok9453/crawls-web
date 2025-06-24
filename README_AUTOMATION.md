# GitHub Actions 自動化設置

## 功能說明

本專案使用 GitHub Actions 實現每日促銷資料的自動更新功能，包含：
- **PChome OnSale**: 每日促銷商品
- **Yahoo 秒殺**: 時時樂限時商品

### 自動化流程

1. **定時執行**: 每 6 小時自動執行一次（UTC 時間 0, 6, 12, 18 點）
2. **爬蟲執行**: 同時執行 PChome OnSale 和 Yahoo 秒殺爬蟲
3. **結果更新**: 將新的促銷資料提交到 GitHub 倉庫
4. **網站更新**: 前端自動顯示最新的促銷資料

### 檔案結構

```
.github/
  workflows/
    update-daily-deals.yml           # GitHub Actions 工作流程
crawl_data/
  crawler_results_pchome_onsale.json    # PChome 促銷結果（固定檔名）
  crawler_results_yahoo_rushbuy.json    # Yahoo 秒殺結果（固定檔名）
```

### 手動觸發

除了定時執行外，您也可以手動觸發更新：

1. 進入 GitHub 倉庫的 "Actions" 頁面
2. 選擇 "Auto Update Daily Deals (PChome + Yahoo)" 工作流程
3. 點擊 "Run workflow" 按鈕

### 監控和日誌

- 可以在 GitHub Actions 頁面查看每次執行的詳細日誌
- 執行日誌會記錄爬取的商品數量和執行狀態
- 如果執行失敗，會在 Actions 頁面顯示錯誤訊息

### 時區說明

- GitHub Actions 使用 UTC 時間
- 每 6 小時執行對應台灣時間：
  - UTC 00:00 → 台灣時間 08:00
  - UTC 06:00 → 台灣時間 14:00
  - UTC 12:00 → 台灣時間 20:00
  - UTC 18:00 → 台灣時間 02:00

### 注意事項

1. **權限設置**: 確保 GitHub Actions 有權限提交代碼到倉庫
2. **依賴管理**: 所有必要的 Python 套件都已列在 `requirements.txt` 中
3. **瀏覽器環境**: GitHub Actions 會自動安裝 Chrome 和 ChromeDriver
4. **檔案管理**: 舊的促銷資料檔案會被自動清理，只保留最新結果

### 疑難排解

如果自動化執行失敗：

1. 檢查 GitHub Actions 的執行日誌
2. 確認網站是否有變更結構
3. 檢查爬蟲程式碼是否需要更新
4. 確認 GitHub 倉庫的權限設置

### 本地測試

您可以在本地測試自動化腳本：

```bash
python run_pchome_onsale.py
```

這會執行相同的爬蟲邏輯，但不會自動提交到 GitHub。
