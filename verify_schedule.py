#!/usr/bin/env python3
"""
驗證新的GitHub Actions執行時間
"""

from datetime import datetime, timezone, timedelta

def verify_schedule():
    """驗證新的執行排程"""
    print("🕒 新的GitHub Actions執行排程")
    print("=" * 50)
    
    # 新的執行時間 (UTC)
    utc_hours = [0, 2, 7, 13]
    
    print("📅 執行時間對照表:")
    print("UTC時間    →  台灣時間")
    print("-" * 25)
    
    for utc_hour in utc_hours:
        # 台灣時間 = UTC + 8
        taiwan_hour = (utc_hour + 8) % 24
        day_suffix = " (+1天)" if utc_hour + 8 >= 24 else ""
        
        print(f"{utc_hour:02d}:00 UTC  →  {taiwan_hour:02d}:00 台灣{day_suffix}")
    
    print("\n⏰ 執行頻率: 每天4次")
    print("🔄 間隔時間: 不固定 (2小時, 5小時, 6小時, 11小時)")
    
    # 計算下次執行時間
    now_utc = datetime.now(timezone.utc)
    now_taiwan = now_utc.astimezone(timezone(timedelta(hours=8)))
    
    print(f"\n📍 當前時間:")
    print(f"UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"台灣: {now_taiwan.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 找出下次執行時間
    current_hour = now_utc.hour
    next_hours = [h for h in utc_hours if h > current_hour]
    
    if next_hours:
        next_utc_hour = next_hours[0]
        next_run_utc = now_utc.replace(hour=next_utc_hour, minute=0, second=0, microsecond=0)
    else:
        # 下一天的第一個時段
        next_utc_hour = utc_hours[0]
        next_run_utc = (now_utc + timedelta(days=1)).replace(hour=next_utc_hour, minute=0, second=0, microsecond=0)
    
    next_run_taiwan = next_run_utc.astimezone(timezone(timedelta(hours=8)))
    time_until = next_run_utc - now_utc
    
    print(f"\n🔔 下次執行:")
    print(f"UTC: {next_run_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"台灣: {next_run_taiwan.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"剩餘: {str(time_until).split('.')[0]}")

def show_cron_syntax():
    """顯示cron語法說明"""
    print(f"\n📝 Cron語法:")
    print(f"'0 0,2,7,13 * * *'")
    print(f"│ │       │ │ │")
    print(f"│ │       │ │ └── 星期 (0-7, 0和7都是週日)")
    print(f"│ │       │ └──── 月份 (1-12)")
    print(f"│ │       └────── 日期 (1-31)")  
    print(f"│ └──────────────── 小時 (0-23) - 在0,2,7,13點執行")
    print(f"└────────────────── 分鐘 (0-59) - 在0分執行")

if __name__ == "__main__":
    verify_schedule()
    show_cron_syntax()
    
    print(f"\n💡 提示:")
    print(f"- 修改後需要提交並推送到GitHub才會生效")
    print(f"- 可以手動觸發測試工作流程是否正常")
    print(f"- 在GitHub Actions頁面可以看到下次排程執行時間")
