import sqlite3

conn = sqlite3.connect('src/data/parsed_logcodes.db')
cur = conn.cursor()

print('=== ALL LOGCODES IN DATABASE ===')
logcodes = cur.execute('SELECT logcode, name, section FROM logcodes ORDER BY logcode').fetchall()
for lc in logcodes:
    print(f'{lc[0]} | Section {lc[2]} | {lc[1]}')

print('\n=== CHECKING DOCUMENT SOURCE ===')
docs = cur.execute('SELECT doc_id, source_path FROM documents').fetchall()
for doc in docs:
    print(f'Doc ID {doc[0]}: {doc[1]}')

print('\n=== LOGCODES PER DOCUMENT ===')
logcode_docs = cur.execute('SELECT logcode, name, doc_id FROM logcodes ORDER BY doc_id, logcode').fetchall()
for lc in logcode_docs:
    print(f'Doc {lc[2]}: {lc[0]} - {lc[1]}')

conn.close()
