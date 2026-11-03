"""Aggregate unique orders by SKU and day using only the standard library."""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ['order_id', 'order_date', 'sku', 'quantity', 'price', 'status']


def aggregate(path):
    seen, totals = {}, {}
    with open(path, encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != FIELDS:
            raise ValueError(f'Expected columns: {FIELDS}')
        for line, raw in enumerate(reader, 2):
            try:
                if None in raw or any(value is None for value in raw.values()):
                    raise ValueError('Wrong number of columns')
                row = {key: value.strip() for key, value in raw.items()}
                row['status'] = row['status'].lower()
                if row['status'] == 'canceled':
                    row['status'] = 'cancelled'
                order_id, sku = row['order_id'], row['sku']
                if not order_id or not sku:
                    raise ValueError('Missing order_id or sku')
                day = date.fromisoformat(row['order_date']).isoformat()
                if day != row['order_date']:
                    raise ValueError('Date must be YYYY-MM-DD')
                if row['status'] not in {'delivered', 'cancelled'}:
                    raise ValueError('Unknown status')
                quantity = int(row['quantity']) if row['quantity'] else None
                if quantity is not None and quantity <= 0:
                    raise ValueError('Quantity must be positive')
                price = Decimal(row['price'])
                if not price.is_finite() or price < 0 or price != price.quantize(Decimal('0.01')):
                    raise ValueError('Price must be non-negative with at most two decimals')
                if row['status'] == 'delivered' and quantity is None:
                    raise ValueError('Delivered order has no quantity')
                record = (sku, day, quantity, price, row['status'])
                if order_id in seen:
                    if seen[order_id] != record:
                        raise ValueError(f'Conflicting records for order {order_id}')
                    continue
                seen[order_id] = record
                key = (sku, day)
                orders, revenue = totals.get(key, (0, Decimal('0')))
                if row['status'] == 'delivered':
                    revenue += quantity * price
                totals[key] = (orders + 1, revenue)
            except (ValueError, InvalidOperation) as exc:
                raise ValueError(f'CSV line {line}: {exc}') from exc
    return [(sku, day, orders, f'{revenue:.2f}')
            for (sku, day), (orders, revenue) in sorted(totals.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default='sales.csv', type=Path)
    parser.add_argument('--output', default='daily_by_sku.csv', type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error('Input and output paths must differ')
    rows = aggregate(args.input)  # Validate the entire input before opening output.
    with open(args.output, 'w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target)
        writer.writerow(['sku', 'order_date', 'orders', 'revenue'])
        writer.writerows(rows)
    print(f'Saved {len(rows)} groups to {args.output}')


if __name__ == '__main__':
    main()
