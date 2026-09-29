from datetime import datetime

from flask import Flask, jsonify, render_template, request

from config import Config
from db import (
    init_db,
    list_expenses,
    add_expense,
    update_expense,
    delete_expense,
    dashboard,
    add_history,
    list_history,
    delete_history,
)
from ai_service import parse_expense, insights, recommend


app = Flask(__name__)
app.config.from_object(Config)

# Create the database and tables automatically.
init_db(app.config["DATABASE_PATH"])


def error(message, status=400):
    return jsonify({"error": message}), status


def valid_amount(value):
    try:
        amount = float(value)
        return amount >= 0
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------
# FRONTEND
# ---------------------------------------------------------

@app.get("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "PocketSmart AI",
        "gemini_configured": bool(app.config["GEMINI_API_KEY"])
    })


# ---------------------------------------------------------
# EXPENSE APIs
# ---------------------------------------------------------

@app.get("/api/expenses")
def expenses():
    return jsonify(
        list_expenses(app.config["DATABASE_PATH"])
    )


@app.post("/api/expenses")
def create_expense():

    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    category = str(
        data.get("category", "Other")
    ).strip() or "Other"

    note = str(
        data.get("note", "")
    ).strip()

    spent_at = str(
        data.get("spent_at", "")
    ).strip()

    if not spent_at:
        spent_at = datetime.now().isoformat()

    if not title:
        return error("Title is required.")

    if not valid_amount(data.get("amount")):
        return error(
            "Amount must be a non-negative number."
        )

    row = add_expense(
        app.config["DATABASE_PATH"],
        title,
        float(data["amount"]),
        category,
        note,
        spent_at
    )

    return jsonify(row), 201


@app.put("/api/expenses/<int:expense_id>")
def edit_expense(expense_id):

    data = request.get_json(silent=True) or {}

    title = str(
        data.get("title", "")
    ).strip()

    category = str(
        data.get("category", "Other")
    ).strip() or "Other"

    note = str(
        data.get("note", "")
    ).strip()

    spent_at = str(
        data.get("spent_at", "")
    ).strip()

    if not spent_at:
        spent_at = datetime.now().isoformat()

    if not title:
        return error("Title is required.")

    if not valid_amount(data.get("amount")):
        return error(
            "Amount must be a non-negative number."
        )

    row = update_expense(
        app.config["DATABASE_PATH"],
        expense_id,
        title,
        float(data["amount"]),
        category,
        note,
        spent_at
    )

    if not row:
        return error(
            "Expense not found.",
            404
        )

    return jsonify(row)


@app.delete("/api/expenses/<int:expense_id>")
def remove_expense(expense_id):

    deleted = delete_expense(
        app.config["DATABASE_PATH"],
        expense_id
    )

    if not deleted:
        return error(
            "Expense not found.",
            404
        )

    return jsonify({
        "message": "Expense deleted."
    })


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.get("/api/dashboard")
def dashboard_api():

    return jsonify(
        dashboard(
            app.config["DATABASE_PATH"]
        )
    )


# ---------------------------------------------------------
# AI - EXPENSE PARSING
# ---------------------------------------------------------

@app.post("/api/ai/parse-expense")
def ai_parse():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return error(
            "Text is required."
        )

    try:

        result = parse_expense(text)

        history = add_history(
            app.config["DATABASE_PATH"],
            "parse-expense",
            text,
            str(result)
        )

        return jsonify({
            "result": result,
            "history_id": history["id"]
        })

    except Exception as exc:

        return error(
            f"AI parsing failed: {exc}",
            502
        )


# ---------------------------------------------------------
# AI - INSIGHTS
# ---------------------------------------------------------

@app.post("/api/ai/insights")
def ai_insights():

    try:

        summary = dashboard(
            app.config["DATABASE_PATH"]
        )

        result = insights(summary)

        history = add_history(
            app.config["DATABASE_PATH"],
            "insights",
            "dashboard",
            result
        )

        return jsonify({
            "result": result,
            "history_id": history["id"]
        })

    except Exception as exc:

        return error(
            f"Insight generation failed: {exc}",
            502
        )


# ---------------------------------------------------------
# AI - RECOMMENDATIONS
# ---------------------------------------------------------

@app.post("/api/ai/recommend")
def ai_recommend():

    data = request.get_json(silent=True) or {}

    try:
        budget = float(
            data.get("budget", 0)
        )
    except (TypeError, ValueError):

        return error(
            "Budget must be a number."
        )

    if budget < 0:
        return error(
            "Budget cannot be negative."
        )

    goal = str(
        data.get("goal", "")
    ).strip()

    preferences = str(
        data.get("preferences", "")
    ).strip()

    if not goal:
        return error(
            "Goal is required."
        )

    try:

        result = recommend(
            budget,
            goal,
            preferences
        )

        history = add_history(
            app.config["DATABASE_PATH"],
            "recommendation",
            f"budget={budget}; goal={goal}; preferences={preferences}",
            result
        )

        return jsonify({
            "result": result,
            "history_id": history["id"]
        })

    except Exception as exc:

        return error(
            f"Recommendation generation failed: {exc}",
            502
        )


# ---------------------------------------------------------
# AI HISTORY
# ---------------------------------------------------------

@app.get("/api/history")
def history():

    return jsonify(
        list_history(
            app.config["DATABASE_PATH"]
        )
    )


@app.post("/api/history")
def save_history():

    data = request.get_json(
        silent=True
    ) or {}

    action = str(
        data.get("action", "")
    ).strip()

    input_text = str(
        data.get("input_text", "")
    ).strip()

    output_text = str(
        data.get("output_text", "")
    ).strip()

    if not action or not input_text or not output_text:
        return error(
            "action, input_text and output_text are required."
        )

    return jsonify(
        add_history(
            app.config["DATABASE_PATH"],
            action,
            input_text,
            output_text
        )
    ), 201


@app.delete("/api/history/<int:history_id>")
def remove_history(history_id):

    deleted = delete_history(
        app.config["DATABASE_PATH"],
        history_id
    )

    if not deleted:
        return error(
            "History item not found.",
            404
        )

    return jsonify({
        "message": "History deleted."
    })


# ---------------------------------------------------------
# 404
# ---------------------------------------------------------

@app.errorhandler(404)
def not_found(_):

    if request.path.startswith("/api/"):
        return error(
            "API endpoint not found.",
            404
        )

    return render_template(
        "index.html"
    ), 404


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
