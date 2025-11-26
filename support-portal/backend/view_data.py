import sqlite3
import pandas as pd

def view_all_data():
    """Display all data in a readable format"""
    
    conn = sqlite3.connect('support_portal.db')
    
    print("🎫 TICKETS:")
    print("=" * 80)
    
    # Read tickets into a pandas DataFrame for better display
    try:
        df_tickets = pd.read_sql_query("SELECT * FROM tickets ORDER BY created_at DESC", conn)
        if not df_tickets.empty:
            # Display with better formatting
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', 50)
            print(df_tickets.to_string(index=False))
        else:
            print("No tickets found")
    except Exception as e:
        print(f"Error reading tickets: {e}")
    
    print("\n\n📎 FILES:")
    print("=" * 80)
    
    try:
        df_files = pd.read_sql_query("SELECT * FROM ticket_files", conn)
        if not df_files.empty:
            print(df_files.to_string(index=False))
        else:
            print("No files found")
    except Exception as e:
        print(f"Error reading files: {e}")
    
    print("\n\n💬 COMMENTS:")
    print("=" * 80)
    
    try:
        df_comments = pd.read_sql_query("SELECT * FROM comments", conn)
        if not df_comments.empty:
            print(df_comments.to_string(index=False))
        else:
            print("No comments found")
    except Exception as e:
        print(f"Error reading comments: {e}")
    
    conn.close()

if __name__ == "__main__":
    try:
        view_all_data()
    except ImportError:
        print("pandas not installed. Installing...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'pandas'])
        import pandas as pd
        view_all_data()