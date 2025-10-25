import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== ALL ROWS IN TABLE 4-4 ===')
rows = cur.execute('''
    SELECT row_index, name, type_name, off
    FROM table_rows
    WHERE logcode = ? AND table_number = ?
    ORDER BY row_index
''', ('0X1C07', '4-4')).fetchall()

print(f'Total rows: {len(rows)}\n')
for row in rows:
    print(f'Row {row[0]:2d}: Off={row[3]:4s} | {row[1]} | {row[2]}')

print('\n=== GROUPED BY OFFSET ===')
rows_by_offset = {}
for row in rows:
    offset = row[3] if row[3] else 'NULL'
    if offset not in rows_by_offset:
        rows_by_offset[offset] = []
    rows_by_offset[offset].append(row)

for offset in sorted(rows_by_offset.keys(), key=lambda x: int(x) if x.isdigit() else 999999):
    if len(rows_by_offset[offset]) > 1:
        print(f'\nOffset {offset} has {len(rows_by_offset[offset])} rows:')
        for row in rows_by_offset[offset]:
            print(f'  Row {row[0]}: {row[1]} | {row[2]}')

conn.close()
