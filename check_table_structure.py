import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== TABLE 4-2 DETAILS (Versions table) ===\n')
for row in cur.execute("SELECT title, raw_caption FROM tables WHERE table_number = '4-2' LIMIT 1").fetchall():
    print(f"Title: {row[0]}")
    print(f"Caption: {row[1]}")

print('\n=== ROWS FROM TABLE 4-2 ===\n')
print("Name | Type Name | Cnt | Off | Len | Description")
print("-" * 80)
for row in cur.execute("SELECT name, type_name, cnt, off, len, description FROM table_rows WHERE table_number = '4-2'").fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")

print('\n\n=== TABLE 4-3 DETAILS (Unknown Versions table) ===\n')
for row in cur.execute("SELECT title, raw_caption FROM tables WHERE table_number = '4-3' LIMIT 1").fetchall():
    print(f"Title: {row[0]}")
    print(f"Caption: {row[1]}")

print('\n=== ROWS FROM TABLE 4-3 ===\n')
print("Name | Type Name | Cnt | Off | Len | Description")
print("-" * 80)
for row in cur.execute("SELECT name, type_name, cnt, off, len, description FROM table_rows WHERE table_number = '4-3'").fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")

conn.close()
