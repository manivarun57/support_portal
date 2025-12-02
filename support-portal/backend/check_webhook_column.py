import sqlite3

conn = sqlite3.connect('support_portal.db')
cursor = conn.cursor()

# Check if slack_webhook_url column exists
cursor.execute('PRAGMA table_info(p1_incidents)')
columns = [col[1] for col in cursor.fetchall()]

print('Columns in p1_incidents table:')
for col in columns:
    print(f'  - {col}')

print()

if 'slack_webhook_url' in columns:
    print('✅ slack_webhook_url column exists')
    
    # Check recent incidents
    cursor.execute('SELECT incident_id, slack_webhook_url FROM p1_incidents ORDER BY created_at DESC LIMIT 3')
    rows = cursor.fetchall()
    
    print(f'\nRecent incidents:')
    for incident_id, webhook in rows:
        if webhook:
            print(f'  {incident_id}: {webhook[:50]}...')
        else:
            print(f'  {incident_id}: NULL (no webhook)')
else:
    print('❌ slack_webhook_url column MISSING!')
    print('   This is why Slack messages are not being sent')

conn.close()
