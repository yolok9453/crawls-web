import sqlite3
import os

db_path = os.path.join('data', 'crawler_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('正確的 daily_deals 結構檢查:')
cursor.execute('PRAGMA table_info(daily_deals)')
columns = cursor.fetchall()
for i, col in enumerate(columns):
    print(f'{i}: {col[1]} ({col[2]})')

print('\n檢查 daily_deals 實際資料:')
cursor.execute('SELECT * FROM daily_deals LIMIT 1')
sample = cursor.fetchone()
if sample:
    print('樣本資料:')
    for i, value in enumerate(sample):
        print(f'  位置 {i}: {value}')

print('\nPCHome特價商品範例:')
cursor.execute('SELECT * FROM daily_deals WHERE platform = ? LIMIT 3', ('pchome_onsale',))
pchome_deals = cursor.fetchall()
for deal in pchome_deals:
    print(f'ID: {deal[0]}, 平台: {deal[1]}, 商品: {deal[2][:50]}..., 價格: {deal[3]}')

# 檢查最近的一般商品資料
print('\n最近的 products 商品範例 (來自圖片中的平台):')
cursor.execute('SELECT * FROM products WHERE platform IN (?, ?) ORDER BY id DESC LIMIT 5', ('pchome', 'yahoo'))
recent_products = cursor.fetchall()
for product in recent_products:
    print(f'平台: {product[2]}, 商品: {product[3][:60]}..., 價格: NT${product[4]}')

conn.close()
