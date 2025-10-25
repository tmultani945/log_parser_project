import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== TABLE 4-1 INFO ===')
result = cur.execute('SELECT table_number, title, page_start, page_end FROM tables WHERE logcode = ? AND table_number = ?', ('0X1C07', '4-1')).fetchone()
print(f'Table: {result[0]}, Title: {result[1]}, Pages: {result[2]}-{result[3]}')

print('\n=== ALL ROWS OF TABLE 4-1 ===')
rows = cur.execute('SELECT row_index, name, type_name, off FROM table_rows WHERE logcode = ? AND table_number = ? ORDER BY row_index', ('0X1C07', '4-1')).fetchall()
for row in rows:
    print(f'Row {row[0]}: {row[1]} | {row[2]} | Off={row[3]}')

conn.close()
