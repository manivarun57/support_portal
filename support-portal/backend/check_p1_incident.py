import sqlite3

conn = sqlite3.connect('support_portal.db')
cursor = conn.cursor()

# Get table structure
cursor.execute('PRAGMA table_info(p1_incidents)')
columns = [col[1] for col in cursor.fetchall()]
print('P1 Incidents table columns:')
print(columns)
print()

# Get most recent P1 incident
cursor.execute('SELECT * FROM p1_incidents ORDER BY created_at DESC LIMIT 1')
row = cursor.fetchone()

if row:
    print('Most recent P1 incident:')
    print('=' * 80)
    for col, val in zip(columns, row):
        print(f'{col}: {val}')
    print('=' * 80)
else:
    print('No P1 incidents found')

conn.close()
