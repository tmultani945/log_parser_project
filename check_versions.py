import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== LOGCODES ===')
for row in cur.execute('SELECT logcode, name, section FROM logcodes').fetchall():
    print(f'{row[0]} | {row[1]} | {row[2]}')

print('\n=== VERSIONS FOR EACH LOGCODE ===')
for logcode in ['0X1C07', '0X1C08', '0X1C09']:
    print(f'\n{logcode}:')
    rows = cur.execute('SELECT version, table_number FROM versions WHERE logcode = ? ORDER BY CAST(version AS INTEGER)', (logcode,)).fetchall()
    if rows:
        for row in rows:
            print(f'  Version {row[0]} -> Table {row[1]}')
    else:
        print('  No versions found')

print('\n=== TABLES FOR EACH LOGCODE ===')
for logcode in ['0X1C07', '0X1C08', '0X1C09']:
    print(f'\n{logcode}:')
    for row in cur.execute('SELECT table_number, title FROM tables WHERE logcode = ? ORDER BY table_number', (logcode,)).fetchall():
        print(f'  {row[0]} - {row[1]}')

conn.close()
