import sqlite3

conn = sqlite3.connect('support_portal.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT incident_id, user_name, message_text, direction, created_at 
    FROM slack_messages 
    ORDER BY created_at DESC 
    LIMIT 10
''')

print('=' * 80)
print('SLACK MESSAGES STORED IN DATABASE')
print('=' * 80)
print()

rows = cursor.fetchall()
if rows:
    for i, row in enumerate(rows, 1):
        print(f'{i}. Incident: {row[0]}')
        print(f'   User: {row[1]}')
        print(f'   Message: {row[2]}')
        print(f'   Direction: {row[3]} (inbound=from Slack, outbound=to Slack)')
        print(f'   Time: {row[4]}')
        print('-' * 80)
    print(f'\nTotal messages: {len(rows)}')
else:
    print('No messages found in database')

conn.close()
