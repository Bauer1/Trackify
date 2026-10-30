"""Populate the database with ~6 months of random demo expenses."""
import random
import sqlite3
from datetime import date, timedelta

from app import CATEGORIES, DATABASE, init_db

SAMPLES = {
    "Food": ["Groceries", "Lunch", "Coffee", "Dinner out"],
    "Transport": ["Taxi", "Fuel", "Metro card"],
    "Housing": ["Rent"],
    "Utilities": ["Electricity", "Internet", "Water"],
    "Entertainment": ["Cinema", "Streaming", "Concert"],
    "Health": ["Pharmacy", "Gym"],
    "Shopping": ["Clothes", "Electronics", "Books"],
    "Education": ["Online course"],
    "Travel": ["Hotel", "Flight"],
    "Other": ["Gift", "Misc"],
}

init_db()
db = sqlite3.connect(DATABASE)
today = date.today()
rows = []
for i in range(180):
    d = today - timedelta(days=i)
    for _ in range(random.randint(0, 3)):
        cat = random.choice(CATEGORIES)
        rows.append((round(random.uniform(3, 120), 2), cat, random.choice(SAMPLES[cat]), d.isoformat()))
    if d.day == 1:
        rows.append((900.0, "Housing", "Rent", d.isoformat()))

db.executemany("INSERT INTO expenses (amount, category, description, spent_on) VALUES (?, ?, ?, ?)", rows)
db.commit()
db.close()
print(f"Inserted {len(rows)} demo expenses into {DATABASE}")
