# Расчёт продаж по дням и артикулам

Python 3.10+, сторонние зависимости не нужны.

```bash
python calculate.py --input sales.csv --output daily_by_sku.csv
python -m unittest -v
```

В архив включена исходная выгрузка под именем sales.csv, но git её игнорирует.
Результат — daily_by_sku.csv с колонками sku, order_date, orders, revenue.
