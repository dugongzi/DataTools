import pymysql

configs = [
    {'host': '127.0.0.1', 'user': 'root', 'password': 'root_password'},
    {'host': '127.0.0.1', 'user': 'datatools_user', 'password': 'datatools_password'},
    {'host': 'localhost', 'user': 'root', 'password': 'root_password'},
    {'host': 'localhost', 'user': 'datatools_user', 'password': 'datatools_password'},
]

for i, config in enumerate(configs, 1):
    print(f"\nTest {i}: {config['user']}@{config['host']}")
    try:
        conn = pymysql.connect(
            host=config['host'],
            port=3306,
            user=config['user'],
            password=config['password'],
            database='datatools_db',
            charset='utf8mb4'
        )
        print(f"  ✓ Success!")
        conn.close()
    except Exception as e:
        print(f"  ✗ Failed: {e}")
