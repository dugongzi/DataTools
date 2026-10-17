import pymysql

print("Testing connection to datatools database...")
try:
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='datatools_user',
        password='datatools_password',
        database='datatools',
        charset='utf8mb4'
    )
    print("✓ Connected successfully!")
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    conn.close()
except Exception as e:
    print(f"✗ Failed: {e}")
