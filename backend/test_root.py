import pymysql

print("Testing root connection...")
try:
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3308,
        user='root',
        password='root_password',
        database='datatools',
        charset='utf8mb4'
    )
    print("✓ Root connected successfully!")
    conn.close()
except Exception as e:
    print(f"✗ Failed: {e}")
