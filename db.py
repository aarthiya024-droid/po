import sqlite3

from pathlib import Path

from datetime import datetime, timezone


SCHEMA = """

CREATE TABLE IF NOT EXISTS expenses (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,

    amount REAL NOT NULL
        CHECK(amount >= 0),

    category TEXT NOT NULL,

    note TEXT DEFAULT '',

    spent_at TEXT NOT NULL,

    created_at TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS ai_history (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    action TEXT NOT NULL,

    input_text TEXT NOT NULL,

    output_text TEXT NOT NULL,

    created_at TEXT NOT NULL
);

"""


def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()


def get_connection(db_path):

    Path(db_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        db_path
    )

    connection.row_factory = sqlite3.Row

    return connection


def init_db(db_path):

    connection = get_connection(
        db_path
    )

    connection.executescript(
        SCHEMA
    )

    connection.commit()

    connection.close()


def rows_to_dict(rows):

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# EXPENSES
# =========================================================

def list_expenses(db_path):

    connection = get_connection(
        db_path
    )

    rows = connection.execute(
        """
        SELECT *
        FROM expenses
        ORDER BY spent_at DESC, id DESC
        """
    ).fetchall()

    connection.close()

    return rows_to_dict(rows)


def add_expense(
    db_path,
    title,
    amount,
    category,
    note="",
    spent_at=None
):

    connection = get_connection(
        db_path
    )

    now = utc_now()

    spent_at = (
        spent_at
        or now
    )

    cursor = connection.execute(
        """
        INSERT INTO expenses
        (
            title,
            amount,
            category,
            note,
            spent_at,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            amount,
            category,
            note,
            spent_at,
            now
        )
    )

    connection.commit()

    expense_id = cursor.lastrowid

    row = connection.execute(
        """
        SELECT *
        FROM expenses
        WHERE id = ?
        """,
        (expense_id,)
    ).fetchone()

    connection.close()

    return dict(row)


def update_expense(
    db_path,
    expense_id,
    title,
    amount,
    category,
    note,
    spent_at
):

    connection = get_connection(
        db_path
    )

    connection.execute(
        """
        UPDATE expenses
        SET
            title = ?,
            amount = ?,
            category = ?,
            note = ?,
            spent_at = ?
        WHERE id = ?
        """,
        (
            title,
            amount,
            category,
            note,
            spent_at,
            expense_id
        )
    )

    connection.commit()

    row = connection.execute(
        """
        SELECT *
        FROM expenses
        WHERE id = ?
        """,
        (expense_id,)
    ).fetchone()

    connection.close()

    if row:
        return dict(row)

    return None


def delete_expense(
    db_path,
    expense_id
):

    connection = get_connection(
        db_path
    )

    cursor = connection.execute(
        """
        DELETE FROM expenses
        WHERE id = ?
        """,
        (expense_id,)
    )

    connection.commit()

    deleted = cursor.rowcount > 0

    connection.close()

    return deleted


# =========================================================
# DASHBOARD
# =========================================================

def dashboard(db_path):

    connection = get_connection(
        db_path
    )

    total = connection.execute(
        """
        SELECT
            COALESCE(
                SUM(amount),
                0
            ) AS value
        FROM expenses
        """
    ).fetchone()["value"]

    count = connection.execute(
        """
        SELECT
            COUNT(*) AS value
        FROM expenses
        """
    ).fetchone()["value"]

    categories = connection.execute(
        """
        SELECT
            category,
            ROUND(
                SUM(amount),
                2
            ) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        """
    ).fetchall()

    recent = connection.execute(
        """
        SELECT *
        FROM expenses
        ORDER BY spent_at DESC, id DESC
        LIMIT 5
        """
    ).fetchall()

    connection.close()

    return {
        "total": round(
            float(total),
            2
        ),

        "count": int(count),

        "categories":
            rows_to_dict(categories),

        "recent":
            rows_to_dict(recent)
    }


# =========================================================
# AI HISTORY
# =========================================================

def add_history(
    db_path,
    action,
    input_text,
    output_text
):

    connection = get_connection(
        db_path
    )

    cursor = connection.execute(
        """
        INSERT INTO ai_history
        (
            action,
            input_text,
            output_text,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            action,
            input_text,
            output_text,
            utc_now()
        )
    )

    connection.commit()

    row = connection.execute(
        """
        SELECT *
        FROM ai_history
        WHERE id = ?
        """,
        (cursor.lastrowid,)
    ).fetchone()

    connection.close()

    return dict(row)


def list_history(db_path):

    connection = get_connection(
        db_path
    )

    rows = connection.execute(
        """
        SELECT *
        FROM ai_history
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return rows_to_dict(rows)


def delete_history(
    db_path,
    history_id
):

    connection = get_connection(
        db_path
    )

    cursor = connection.execute(
        """
        DELETE FROM ai_history
        WHERE id = ?
        """,
        (history_id,)
    )

    connection.commit()

    deleted = cursor.rowcount > 0

    connection.close()

    return deleted
