import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== ALL DEPENDENCIES FOR 0X1C07 ===')
deps = cur.execute('SELECT table_number, dep_table_number FROM table_deps WHERE logcode = ? ORDER BY table_number', ('0X1C07',)).fetchall()
for dep in deps:
    print(f'Table {dep[0]} depends on Table {dep[1]}')

print('\n=== CHECKING IF TABLE 4-7 EXISTS ===')
table_7 = cur.execute('SELECT table_number, title FROM tables WHERE logcode = ? AND table_number = ?', ('0X1C07', '4-7')).fetchone()
if table_7:
    print(f'Found: {table_7[0]} - {table_7[1]}')
else:
    print('Table 4-7 not found in database')

print('\n=== CHECKING IF TABLE 4-5 EXISTS ===')
table_5 = cur.execute('SELECT table_number, title FROM tables WHERE logcode = ? AND table_number = ?', ('0X1C07', '4-5')).fetchone()
if table_5:
    print(f'Found: {table_5[0]} - {table_5[1]}')
else:
    print('Table 4-5 not found in database')

print('\n=== SIMULATION: Get tables for version 2 ===')
# Get main table for version 2
version_2_table = cur.execute('SELECT table_number FROM versions WHERE logcode = ? AND version = ?', ('0X1C07', '2')).fetchone()
print(f'Version 2 maps to: {version_2_table[0]}')

# Get dependencies
deps_for_v2 = cur.execute('SELECT dep_table_number FROM table_deps WHERE logcode = ? AND table_number = ?', ('0X1C07', version_2_table[0])).fetchall()
print(f'Dependencies: {[d[0] for d in deps_for_v2]}')

conn.close()
