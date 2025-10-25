import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== TABLE 4-2 (VERSIONS TABLE) ===')
rows = cur.execute('SELECT row_index, name, type_name FROM table_rows WHERE logcode = ? AND table_number = ? ORDER BY row_index', ('0X1C07', '4-2')).fetchall()
print(f'Total rows: {len(rows)}\n')
for row in rows:
    print(f'Row {row[0]}: {row[1]} | {row[2]}')

conn.close()
