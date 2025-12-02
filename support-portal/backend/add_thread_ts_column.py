"""
Add slack_thread_ts column to p1_incidents table
This stores the Slack thread timestamp for WhatsApp-like conversation threading
"""
import sqlite3

conn = sqlite3.connect('support_portal.db')
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(p1_incidents)")
columns = [col[1] for col in cursor.fetchall()]

if 'slack_thread_ts' not in columns:
    print("Adding slack_thread_ts column...")
    cursor.execute("""
        ALTER TABLE p1_incidents 
        ADD COLUMN slack_thread_ts TEXT
    """)
    conn.commit()
    print("✅ Column added successfully")
else:
    print("✅ Column already exists")

conn.close()
print("Migration complete!")
