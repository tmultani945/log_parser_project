import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== CHECKING TABLE 4-20 ===')
table_20 = cur.execute('SELECT logcode, table_number, title FROM tables WHERE table_number = ?', ('4-20',)).fetchall()
if table_20:
    for row in table_20:
        print(f'Found: {row[1]} | Logcode: {row[0]} | Title: {row[2]}')
else:
    print('Table 4-20 NOT FOUND in database')

print('\n=== DEPENDENCIES FOR TABLE 4-18 ===')
deps_18 = cur.execute('SELECT dep_table_number FROM table_deps WHERE logcode = ? AND table_number = ?', ('0X1C07', '4-18')).fetchall()
print(f'Table 4-18 depends on: {[d[0] for d in deps_18]}')

print('\n=== DEPENDENCIES FOR TABLE 4-19 ===')
deps_19 = cur.execute('SELECT dep_table_number FROM table_deps WHERE logcode = ? AND table_number = ?', ('0X1C07', '4-19')).fetchall()
print(f'Table 4-19 depends on: {[d[0] for d in deps_19]}')

print('\n=== ALL TABLES FOR 0X1C07 WITH "4-1" OR "4-2" PREFIX ===')
tables = cur.execute('SELECT table_number, title FROM tables WHERE logcode = ? AND (table_number LIKE "4-1%" OR table_number LIKE "4-2%") ORDER BY table_number', ('0X1C07',)).fetchall()
for t in tables:
    print(f'{t[0]} - {t[1]}')

conn.close()
