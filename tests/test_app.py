import tempfile

from pathlib import Path

import pytest

from app import app

from db import init_db


@pytest.fixture()
def client():

    with tempfile.TemporaryDirectory() as tmp:

        db_path = str(
            Path(tmp) / "test.db"
        )


        app.config.update(

            TESTING=True,

            DATABASE_PATH=db_path,

            GEMINI_API_KEY=""

        )


        init_db(
            db_path
        )


        with app.test_client() as client:

            yield client


# =========================================================
# HEALTH TEST
# =========================================================

def test_health(client):

    response = client.get(
        "/api/health"
    )


    assert response.status_code == 200


    data = response.get_json()


    assert data["status"] == "ok"


# =========================================================
# CREATE EXPENSE TEST
# =========================================================

def test_create_and_list_expense(
    client
):

    response = client.post(

        "/api/expenses",

        json={

            "title":
                "Coffee",

            "amount":
                120,

            "category":
                "Food",

            "note":
                "Test"

        }

    )


    assert response.status_code == 201


    data = response.get_json()


    assert data["title"] == "Coffee"


    response = client.get(
        "/api/expenses"
    )


    assert response.status_code == 200


    expenses =
        response.get_json()


    assert len(expenses) == 1


# =========================================================
# AI PARSER FALLBACK TEST
# =========================================================

def test_parse_without_gemini(
    client
):

    response = client.post(

        "/api/ai/parse-expense",

        json={

            "text":
                "coffee 120"

        }

    )


    assert response.status_code == 200


    result =
        response.get_json()["result"]


    assert result["amount"] == 120


    assert result["category"] == "Food"


# =========================================================
# DASHBOARD TEST
# =========================================================

def test_dashboard(client):

    client.post(

        "/api/expenses",

        json={

            "title":
                "Bus",

            "amount":
                40,

            "category":
                "Transport"

        }

    )


    response =
        client.get(
            "/api/dashboard"
        )


    data =
        response.get_json()


    assert data["total"] == 40


    assert data["count"] == 1
