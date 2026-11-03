"""Independent check of this supplied dataset using SQLite and integer kopecks."""
import csv
import sqlite3
from decimal import Decimal
from pathlib import Path


def verify(folder):
    with (folder / 'sales.csv').open(encoding='utf-8-sig', newline='') as source:
        rows = list(csv.DictReader(source))
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE sales (order_id TEXT, day TEXT, sku TEXT, qty INTEGER, kopecks INTEGER, status TEXT)')
    db.executemany('INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)', [
        (r['order_id'].strip(), r['order_date'].strip(), r['sku'].strip(),
         int(r['quantity']) if r['quantity'].strip() else None,
         int(Decimal(r['price']) * 100), r['status'].strip().lower().replace('canceled', 'cancelled'))
        for r in rows])
    # This independent check is scoped to the supplied file: duplicates are exact.
    expected = db.execute('''
        WITH unique_orders AS (SELECT DISTINCT * FROM sales)
        SELECT sku, day, COUNT(*),
               SUM(CASE WHEN status = 'delivered' THEN qty * kopecks ELSE 0 END)
        FROM unique_orders GROUP BY sku, day ORDER BY sku, day
    ''').fetchall()
    with (folder / 'daily_by_sku.csv').open(encoding='utf-8', newline='') as source:
        actual = [(r['sku'], r['order_date'], int(r['orders']),
                   int(Decimal(r['revenue']) * 100)) for r in csv.DictReader(source)]
    assert expected == actual, 'SQL and Python results differ'
    unique = {tuple(r.values()) for r in rows}
    print('Input rows:', len(rows))
    print('Unique orders:', len(unique))
    print('Groups checked:', len(actual))
    print('Orders total:', sum(r[2] for r in actual))
    print('Revenue:', Decimal(sum(r[3] for r in actual)) / 100)
    print('All result rows match independent SQLite aggregation')
    print('By SKU:')
    for row in db.execute('''WITH u AS (SELECT DISTINCT * FROM sales)
        SELECT sku, COUNT(*), SUM(CASE WHEN status='delivered' THEN qty*kopecks ELSE 0 END)/100
        FROM u GROUP BY sku ORDER BY sku'''):
        print(row)
    print('Unique statuses:', db.execute('SELECT status, COUNT(*) FROM (SELECT DISTINCT * FROM sales) GROUP BY status').fetchall())
    db.close()


if __name__ == '__main__':
    verify(Path(__file__).resolve().parent)
