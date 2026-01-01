import sqlite3
import time
import os
import sys
from datetime import datetime, timedelta

DB_PATH = "backend/w_intel.db"

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_pipeline_stats(conn):
    cursor = conn.cursor()
    # Get standard statuses
    statuses = [
        "DISCOVERED", "QUEUED", "CRAWLING", "CRAWLED_SUCCESS", "CRAWLED_FAIL",
        "ANALYZING", "ANALYSIS_SUCCESS", "ANALYSIS_FAIL", "COMPLETED", "BLOCKED"
    ]
    
    cursor.execute("SELECT status, COUNT(*) as count FROM pipeline_items GROUP BY status")
    rows = cursor.fetchall()
    current_counts = {row['status']: row['count'] for row in rows}
    
    # Fill in 0 for missing statuses
    stats = {s: current_counts.get(s, 0) for s in statuses}
    # Add any others found
    for s, c in current_counts.items():
        if s not in stats:
            stats[s] = c
            
    return stats

def get_recent_items(conn, limit=10):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fqdn, status, updated_at, priority
        FROM pipeline_items
        ORDER BY updated_at DESC LIMIT ?
    """, (limit,))
    return cursor.fetchall()

def get_recent_logs(conn, limit=5):
    cursor = conn.cursor()
    try:
        # Check if table exists first to avoid crashing if logs aren't set up yet
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pipeline_logs'")
        if not cursor.fetchone():
            return []
            
        cursor.execute("""
            SELECT l.stage, l.level, l.message, l.timestamp, i.fqdn 
            FROM pipeline_logs l
            LEFT JOIN pipeline_items i ON l.item_id = i.id
            ORDER BY l.id DESC LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    except Exception:
        return []

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {os.path.abspath(DB_PATH)}")
        return

    print("Starting Pipeline Monitor...")
    
    while True:
        conn = get_db_connection()
        if not conn:
            time.sleep(5)
            continue
            
        try:
            stats = get_pipeline_stats(conn)
            items = get_recent_items(conn)
            logs = get_recent_logs(conn)
            
            clear_screen()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"=== ARX Pipeline Monitor [{now_str}] ===")
            print("-" * 60)
            
            # 1. Overall Counts
            print("Status Summary:")
            total = sum(stats.values())
            
            # Print in 2 columns
            status_list = list(stats.items())
            mid = (len(status_list) + 1) // 2
            
            col1 = status_list[:mid]
            col2 = status_list[mid:]
            
            for i in range(len(col1)):
                s1, c1 = col1[i]
                line = f"  {s1:<18}: {c1:>4}"
                if i < len(col2):
                    s2, c2 = col2[i]
                    line += f"    |    {s2:<18}: {c2:>4}"
                print(line)
            
            print(f"\n  TOTAL ITEMS       : {total}")
            print("-" * 60)
            
            # 2. Recent Updates
            print("Recent Activity (Last 10 Updates):")
            print(f"{'Time':<20} | {'Status':<16} | {'FQDN'}")
            print("-" * 60)
            for item in items:
                ts = str(item['updated_at']) if item['updated_at'] else "N/A"
                # Truncate FQDN if too long
                fqdn = item['fqdn']
                if len(fqdn) > 40:
                    fqdn = fqdn[:37] + "..."
                
                print(f"{ts[:19]:<20} | {item['status']:<16} | {fqdn}")
            
            # 3. Recent Logs
            if logs:
                print("-" * 60)
                print("Latest System Logs:")
                for log in logs:
                    ts = str(log['timestamp']) if log['timestamp'] else "N/A"
                    fqdn = f" [{log['fqdn']}]" if log['fqdn'] else ""
                    msg = log['message'] or ""
                    # Truncate message
                    if len(msg) > 60:
                        msg = msg[:57] + "..."
                    print(f"[{ts[:19]}] {log['level']} {msg}{fqdn}")
            
            conn.close()
            print("\n(Ctrl+C to Quit)")
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\nExiting monitor...")
            if conn:
                conn.close()
            break
        except Exception as e:
            print(f"Error in monitor loop: {e}")
            if conn:
                conn.close()
            time.sleep(5)

if __name__ == "__main__":
    main()
