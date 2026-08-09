import os
import csv

def _read_csv(data_dir, filename):
    """Read CSV file and return list of dicts. Returns [] if file not found."""
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def load_all_data(data_dir="dataset"):
    """Stage 1: Load all datasets. Returns dict with all data."""
    # Print stage banner
    print("="*70)
    print("  STAGE 1: DATA INGESTION")
    print("="*70)
    
    data_store = {}
    files = {
        'messages': 'messages.csv',
        'users': 'users.csv',
        'groups': 'groups.csv',
        'group_members': 'group_members.csv',
        'user_business_history': 'user_business_history.csv',
        'message_history': 'message_history.csv',
        'message_events': 'message_events.csv',
        'images': 'images.csv',
        'voice_notes': 'voice_notes.csv',
        'daily_summary': 'daily_notification_summary.csv',
        'sample_messages': 'sample_messages.csv'
    }
    
    for key, filename in files.items():
        data_store[key] = _read_csv(data_dir, filename)
        count = len(data_store[key])
        # Print with padded dots like: Loading messages.csv .......... 110 rows ✓
        label = f"  Loading {filename} "
        dots = '.' * (45 - len(label))
        print(f"{label}{dots} {count} rows")
    
    data_store['data_dir'] = data_dir
    print(f"\n  Total datasets loaded: {len(files)}")
    print()
    return data_store
