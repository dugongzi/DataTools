import pymysql

print("Testing new test user...")
try:
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='test',
        password='123456',
        database='datatools_db',
        charset='utf8mb4'
    )
    print("✓ Test user connected successfully!")
    conn.close()
except Exception as e:
    print(f"✗ Failed: {e}")
