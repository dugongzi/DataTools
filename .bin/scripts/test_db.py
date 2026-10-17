import os
import pymysql
from dotenv import load_dotenv

load_dotenv('../.env')

print(f"Connecting to MySQL...")
print(f"Host: 127.0.0.1")
print(f"Port: {os.getenv('MYSQL_PORT')}")
print(f"User: {os.getenv('MYSQL_USER')}")
print(f"Database: {os.getenv('MYSQL_DATABASE')}")

try:
    connection = pymysql.connect(
        host='127.0.0.1',
        port=int(os.getenv('MYSQL_PORT')),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        charset='utf8mb4'
    )
    print("✓ Connection successful!")
    
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
    
    connection.close()
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
