import sqlite3
conn = sqlite3.connect('university.db')
cursor = conn.cursor()
with open('query_1.sql', 'r') as f:
    sql = f.read()
cursor.execute(sql)
print(cursor.fetchall())
conn.close()