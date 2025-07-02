@echo off
echo ==========================================
echo          每日促銷系統快速啟動
echo ==========================================
echo.

echo 1. 檢查系統狀態...
python status_check.py

echo.
echo 2. 啟動 Flask 網站...
echo 請等待 Flask 啟動完成後，開啟瀏覽器訪問以下網址：
echo.
echo   主頁: http://localhost:5000
echo   每日促銷: http://localhost:5000/daily-deals  
echo   API測試: http://localhost:5000/api_test.html
echo   圖片測試: http://localhost:5000/image_test.html
echo.
echo 正在啟動 Flask 應用...

python web_app.py
