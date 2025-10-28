import sys
sys.path.insert(0, 'src')
from datastore import LogcodeDatastore

db = LogcodeDatastore('data/parsed_logcodes.db')

print('=== Logcode 0X1C1A (Section 4.9) ===')
tables = db.conn.execute('SELECT table_number FROM tables WHERE logcode = ?', ('0X1C1A',)).fetchall()
print(f'Tables: {[t[0] for t in tables]}')

print('\n=== Logcode 0X1C2C (Section 4.10) ===')
tables = db.conn.execute('SELECT table_number FROM tables WHERE logcode = ?', ('0X1C2C',)).fetchall()
print(f'Tables: {[t[0] for t in tables] if tables else "None"}')

print('\n=== All Section 4 logcodes (4.9 through 4.12) ===')
logcodes = db.conn.execute('''
    SELECT logcode, section, name
    FROM logcodes
    WHERE section LIKE '4.%'
    ORDER BY CAST(SUBSTR(section, INSTR(section, '.') + 1) AS INTEGER)
''').fetchall()

for lc in logcodes:
    if lc[1] in ['4.9', '4.10', '4.11', '4.12']:
        print(f'\n{lc[0]} - Section {lc[1]} - {lc[2]}')
        tables = db.conn.execute('SELECT table_number FROM tables WHERE logcode = ? ORDER BY table_number', (lc[0],)).fetchall()
        print(f'  Tables: {[t[0] for t in tables] if tables else "None"}')

print('\n=== Checking if tables 4-164 to 4-167 exist in database ===')
for tnum in ['4-164', '4-165', '4-166', '4-167']:
    result = db.conn.execute('SELECT logcode, title FROM tables WHERE table_number = ?', (tnum,)).fetchone()
    if result:
        print(f'Table {tnum}: Assigned to {result[0]} - Title: {result[1]}')
    else:
        print(f'Table {tnum}: NOT FOUND in database')

db.close()
