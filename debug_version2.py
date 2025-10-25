import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== VERSION 2 MAPPING ===')
result = cur.execute('SELECT version, table_number FROM versions WHERE logcode = ? AND version = ?', ('0X1C07', '2')).fetchone()
print(f'Version 2 maps to: {result[1]}')

print('\n=== TABLE 4-4 INFO ===')
result = cur.execute('SELECT table_number, title, page_start, page_end FROM tables WHERE logcode = ? AND table_number = ?', ('0X1C07', '4-4')).fetchone()
print(f'Table: {result[0]}, Title: {result[1]}, Pages: {result[2]}-{result[3]}')

print('\n=== FIRST 10 ROWS OF TABLE 4-4 ===')
rows = cur.execute('SELECT row_index, name, type_name, off FROM table_rows WHERE logcode = ? AND table_number = ? ORDER BY row_index LIMIT 10', ('0X1C07', '4-4')).fetchall()
for row in rows:
    print(f'Row {row[0]}: {row[1]} | {row[2]} | Off={row[3]}')

print('\n=== DEPENDENCIES FOR TABLE 4-4 ===')
deps = cur.execute('SELECT dep_table_number FROM table_deps WHERE logcode = ? AND table_number = ?', ('0X1C07', '4-4')).fetchall()
if deps:
    for dep in deps:
        print(f'  Depends on: {dep[0]}')
else:
    print('  No dependencies')

print('\n=== ALL TABLES FOR 0X1C07 ===')
tables = cur.execute('SELECT table_number, title FROM tables WHERE logcode = ? ORDER BY table_number', ('0X1C07',)).fetchall()
for tbl in tables:
    print(f'{tbl[0]} - {tbl[1]}')

conn.close()
