"""Expense Tracker — Flask + SQLite + Chart.js."""
import os
import sqlite3
from datetime import date

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get("EXPENSE_DB", os.path.join(BASE_DIR, "expenses.db"))

CATEGORIES = [
    "Food", "Transport", "Housing", "Utilities", "Entertainment",
    "Health", "Shopping", "Education", "Travel", "Other",
]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")


# --------------------------------------------------------------------------- DB
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            amount      REAL    NOT NULL CHECK (amount > 0),
            category    TEXT    NOT NULL,
            description TEXT    NOT NULL DEFAULT '',
            spent_on    TEXT    NOT NULL,          -- ISO date YYYY-MM-DD
            created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(spent_on)")
    db.commit()
    db.close()


# ---------------------------------------------------------------------- helpers
def current_month():
    return date.today().strftime("%Y-%m")


def selected_month():
    """Return the month filter from the query string ('' means all time)."""
    month = request.args.get("month", current_month())
    if month and (len(month) != 7 or month[4] != "-"):
        month = current_month()
    return month


def month_clause(month):
    if month:
        return "WHERE substr(spent_on, 1, 7) = ?", (month,)
    return "", ()


def parse_form(form):
    errors = []
    try:
        amount = round(float(form.get("amount", "")), 2)
        if amount <= 0:
            errors.append("Amount must be greater than zero.")
    except ValueError:
        amount = None
        errors.append("Amount must be a number.")

    category = form.get("category", "")
    if category not in CATEGORIES:
        errors.append("Please choose a valid category.")

    spent_on = form.get("spent_on", "")
    try:
        date.fromisoformat(spent_on)
    except ValueError:
        errors.append("Please provide a valid date.")

    description = form.get("description", "").strip()[:200]
    return {"amount": amount, "category": category, "spent_on": spent_on,
            "description": description}, errors


# ----------------------------------------------------------------------- routes
@app.route("/")
def index():
    month = selected_month()
    where, params = month_clause(month)
    db = get_db()

    expenses = db.execute(
        f"SELECT * FROM expenses {where} ORDER BY spent_on DESC, id DESC", params
    ).fetchall()

    total = sum(e["amount"] for e in expenses)
    top = db.execute(
        f"SELECT category, SUM(amount) AS total FROM expenses {where} "
        "GROUP BY category ORDER BY total DESC LIMIT 1", params
    ).fetchone()

    months = [r["m"] for r in db.execute(
        "SELECT DISTINCT substr(spent_on, 1, 7) AS m FROM expenses ORDER BY m DESC"
    )]
    if current_month() not in months:
        months.insert(0, current_month())

    return render_template(
        "index.html",
        expenses=expenses, total=total, count=len(expenses), top=top,
        month=month, months=months,
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        data, errors = parse_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("form.html", expense=data, categories=CATEGORIES, mode="Add")
        db = get_db()
        db.execute(
            "INSERT INTO expenses (amount, category, description, spent_on) VALUES (?, ?, ?, ?)",
            (data["amount"], data["category"], data["description"], data["spent_on"]),
        )
        db.commit()
        flash("Expense added.", "success")
        return redirect(url_for("index", month=data["spent_on"][:7]))

    blank = {"amount": "", "category": CATEGORIES[0], "description": "",
             "spent_on": date.today().isoformat()}
    return render_template("form.html", expense=blank, categories=CATEGORIES, mode="Add")


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit(expense_id):
    db = get_db()
    expense = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if expense is None:
        abort(404)

    if request.method == "POST":
        data, errors = parse_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("form.html", expense=data, categories=CATEGORIES, mode="Edit")
        db.execute(
            "UPDATE expenses SET amount=?, category=?, description=?, spent_on=? WHERE id=?",
            (data["amount"], data["category"], data["description"], data["spent_on"], expense_id),
        )
        db.commit()
        flash("Expense updated.", "success")
        return redirect(url_for("index", month=data["spent_on"][:7]))

    return render_template("form.html", expense=expense, categories=CATEGORIES, mode="Edit")


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id):
    db = get_db()
    db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()
    flash("Expense deleted.", "success")
    return redirect(request.referrer or url_for("index"))


# -------------------------------------------------------------------- chart API
@app.route("/api/summary")
def api_summary():
    month = selected_month()
    where, params = month_clause(month)
    db = get_db()

    by_category = db.execute(
        f"SELECT category, ROUND(SUM(amount), 2) AS total FROM expenses {where} "
        "GROUP BY category ORDER BY total DESC", params
    ).fetchall()

    by_day = db.execute(
        f"SELECT spent_on AS day, ROUND(SUM(amount), 2) AS total FROM expenses {where} "
        "GROUP BY spent_on ORDER BY spent_on", params
    ).fetchall()

    # Monthly trend over the last 12 months (independent of the filter)
    by_month = db.execute(
        "SELECT substr(spent_on, 1, 7) AS month, ROUND(SUM(amount), 2) AS total "
        "FROM expenses GROUP BY month ORDER BY month DESC LIMIT 12"
    ).fetchall()

    return jsonify({
        "by_category": {"labels": [r["category"] for r in by_category],
                        "data": [r["total"] for r in by_category]},
        "by_day": {"labels": [r["day"] for r in by_day],
                   "data": [r["total"] for r in by_day]},
        "by_month": {"labels": [r["month"] for r in reversed(by_month)],
                     "data": [r["total"] for r in reversed(by_month)]},
    })


init_db()

if __name__ == "__main__":
    app.run(debug=True)
