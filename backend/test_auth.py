import pymysql

print("Testing with auth_plugin_map...")
try:
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='root_password',
        database='datatools',
        charset='utf8mb4',
        auth_plugin_map={
            'caching_sha2_password': 'caching_sha2_password'
        }
    )
    print("✓ Connected successfully!")
    conn.close()
except Exception as e:
    print(f"✗ Failed: {e}")
