import sqlite3
import os

database_path = r'D:\Code\My_plugin\auto-forwarding-lottery\added.db'

# 检查文件是否存在
if not os.path.exists(database_path):
    raise FileNotFoundError(f"Database file not found at {database_path}")

# 尝试连接数据库
try:
    conn = sqlite3.connect(database_path)
    print("Database connection successful")
except sqlite3.OperationalError as e:
    print(f"OperationalError: {e}")
    
cursor = conn.cursor()
cursor.execute(''' create table if not exists events(
    time text,
    name text,
    content text
)''')

cursor.execute("select * from events")

to_delete = "Upspeed盛嘉成"
add = "2024-09-15"

cursor.execute("select * from events")
entries = cursor.fetchall()

for entry in entries:
    if entry[1] == to_delete:
        cursor.execute("delete from events where name = ?", (to_delete,))
        cursor.execute("insert into events values(?, ?, ?)", (add, entry[1], entry[2]))
        break

conn.commit()

cursor.close()
conn.close()