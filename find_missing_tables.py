import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== SEARCHING FOR TABLES 4-5, 4-7, 4-9, 4-11, etc. ===')
for i in range(1, 50):
    table_num = f'4-{i}'
    rows = cur.execute('SELECT logcode, table_number, title FROM tables WHERE table_number = ?', (table_num,)).fetchall()
    if rows:
        for row in rows:
            print(f'{row[1]} | {row[0]} | {row[2]}')
    else:
        # Check if any version references this table
        refs = cur.execute('SELECT logcode, version FROM versions WHERE table_number = ?', (table_num,)).fetchall()
        if refs:
            print(f'{table_num} | MISSING but referenced by version: {refs}')

print('\n=== ALL TABLES IN ORDER ===')
tables = cur.execute('SELECT logcode, table_number, title FROM tables ORDER BY CAST(substr(table_number, 3) AS INTEGER)').fetchall()
for row in tables:
    print(f'{row[1]} | {row[0]} | {row[2]}')

conn.close()
