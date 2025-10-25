import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== ALL TABLES FOR EACH LOGCODE ===\n')
for row in cur.execute('SELECT logcode, table_number, title FROM tables ORDER BY logcode, table_number').fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

print('\n=== TABLES ENDING WITH _Versions ===\n')
for row in cur.execute("SELECT logcode, table_number, title FROM tables WHERE title LIKE '%_Versions'").fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

print('\n=== SAMPLE ROWS FROM VERSIONS TABLE ===\n')
for row in cur.execute("SELECT * FROM table_rows WHERE table_number LIKE '%-1' LIMIT 20").fetchall():
    print(row)

conn.close()
