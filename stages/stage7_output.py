"""
Stage 7: Output
Writes predictions to output files.
"""
import csv
import os

def write_output(decisions, data_dir='dataset'):
    """Stage 7: Write predictions to output.csv"""
    print("="*40)
    print("STAGE 7: Output Generation")
    print("="*40)
    
    fieldnames = ['message_id', 'action', 'message_type', 'reason', 'confidence', 'evidence_message_ids']
    
    rows = []
    for d in decisions:
        rows.append({
            'message_id': d['message_id'],
            'action': d['action'],
            'message_type': d['message_type'],
            'reason': '; '.join(d['reasons']),
            'confidence': f"{d['confidence']:.2f}",
            'evidence_message_ids': d['evidence_message_ids']
        })
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    # Write to dataset/output.csv
    out1 = os.path.join(data_dir, 'output.csv')
    # Write to root output.csv
    out2 = 'output.csv'
    
    for path in [out1, out2]:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    
    print(f"  Saved {len(rows)} predictions to {out1}")
    print(f"  Saved {len(rows)} predictions to {out2}")
    print()
