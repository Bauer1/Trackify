# Expense Tracker

A small expense tracker built with **Flask**, **SQLite** and **Chart.js**.

## Features
- Add, edit and delete expenses (amount, category, date, description)
- Filter by month or view all time
- Summary cards: total spent, number of transactions, top category
- Charts: spending by category (doughnut), daily spending (bar), 12‑month trend (line)
- JSON endpoint `GET /api/summary?month=YYYY-MM` that powers the charts

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000
```

The SQLite database (`expenses.db`) is created automatically on first run.
Override its location with `EXPENSE_DB=/path/to/file.db`.

Optionally load demo data: `python seed.py`
