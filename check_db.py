import sqlite3
import os

# 連接到資料庫
db_path = os.path.join('data', 'crawler_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('=== 資料庫結構 ===')
print('\n1. crawl_sessions 表結構:')
cursor.execute('PRAGMA table_info(crawl_sessions)')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

print('\n2. products 表結構:')
cursor.execute('PRAGMA table_info(products)')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

print('\n3. daily_deals 表結構:')
cursor.execute('PRAGMA table_info(daily_deals)')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

print('\n=== 資料內容範例 ===')
print('\n最新的 products 資料 (前3筆):')
cursor.execute('SELECT * FROM products ORDER BY id DESC LIMIT 3')
products = cursor.fetchall()
if products:
    for product in products:
        print(f'ID: {product[0]}')
        print(f'  session_id: {product[1]}')
        print(f'  platform: {product[2]}')
        print(f'  title: {product[3][:80]}...')
        print(f'  price: {product[4]}')
        print(f'  url: {product[5][:80]}...')
        print(f'  image_url: {product[6][:80] if product[6] else None}...')
        print(f'  is_filtered_out: {product[7]}')
        print('---')
else:
    print('沒有找到 products 資料')

print('\n最新的 daily_deals 資料 (前3筆):')
cursor.execute('SELECT * FROM daily_deals ORDER BY id DESC LIMIT 3')
deals = cursor.fetchall()
if deals:
    for deal in deals:
        print(f'ID: {deal[0]}')
        print(f'  platform: {deal[1]}')
        print(f'  title: {deal[2][:80]}...')
        print(f'  price: {deal[3]}')
        print(f'  original_price: {deal[4]}')
        print(f'  discount_percent: {deal[5]}')
        print(f'  url: {deal[6][:80] if deal[6] else None}...')
        print(f'  image_url: {deal[7][:80] if deal[7] else None}...')
        print(f'  crawl_time: {deal[8]}')
        print('---')
else:
    print('沒有找到 daily_deals 資料')

print('\n資料數量統計:')
cursor.execute('SELECT COUNT(*) FROM products')
product_count = cursor.fetchone()[0]
print(f'products 表中共有 {product_count} 筆資料')

cursor.execute('SELECT COUNT(*) FROM daily_deals')
deals_count = cursor.fetchone()[0]
print(f'daily_deals 表中共有 {deals_count} 筆資料')

cursor.execute('SELECT COUNT(*) FROM crawl_sessions')
sessions_count = cursor.fetchone()[0]
print(f'crawl_sessions 表中共有 {sessions_count} 筆資料')

# 查看各平台的資料分布
print('\n平台資料分布:')
cursor.execute('SELECT platform, COUNT(*) FROM products GROUP BY platform')
platform_stats = cursor.fetchall()
for platform, count in platform_stats:
    print(f'  {platform}: {count} 筆商品')

cursor.execute('SELECT platform, COUNT(*) FROM daily_deals GROUP BY platform')
deals_platform_stats = cursor.fetchall()
print('\ndaily_deals 平台分布:')
for platform, count in deals_platform_stats:
    print(f'  {platform}: {count} 筆特價商品')

conn.close()
