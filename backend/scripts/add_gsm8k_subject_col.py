#!/usr/bin/env python3
"""Append subject=math column to every data row of gsm8k_eval.csv (keep header intact)."""
import csv
from pathlib import Path

p = Path('/Users/macbookpro/Desktop/FYP/backend/data/evaluation/gsm8k_eval.csv')
with p.open(newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

assert rows and 'subject' in rows[0], "Header must already have a 'subject' column"
for r in rows:
    r.setdefault('subject', '')
    if not r['subject'].strip():
        r['subject'] = 'math'

fieldnames = list(rows[0].keys())
with p.open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f"Done: {len(rows)} rows, subject={rows[0]['subject']} confirmed")
