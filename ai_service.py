import json
import re

from typing import Any

from config import Config


try:

    from google import genai

    from google.genai import types

except ImportError:

    genai = None

    types = None


CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Education",
    "Bills",
    "Entertainment",
    "Health",
    "Travel",
    "Other"
]


# =========================================================
# GEMINI CLIENT
# =========================================================

def _client():

    if (
        not Config.GEMINI_API_KEY
        or genai is None
    ):
        return None

    return genai.Client(
        api_key=Config.GEMINI_API_KEY
    )


# =========================================================
# JSON EXTRACTION
# =========================================================

def _extract_json(
    text: str
) -> dict[str, Any]:

    text = text.strip()

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        match = re.search(
            r"\{.*\}",
            text,
            flags=re.S
        )

        if match:

            return json.loads(
                match.group(0)
            )

        raise


# =========================================================
# LOCAL FALLBACK EXPENSE PARSER
# =========================================================

def _fallback_parse(text):

    amount_match = re.search(
        r"(?:₹|rs\.?|inr)?\s*"
        r"([0-9]+(?:\.[0-9]+)?)",
        text,
        re.I
    )

    amount = (
        float(amount_match.group(1))
        if amount_match
        else 0
    )

    cleaned = re.sub(
        r"(?:₹|rs\.?|inr)?\s*"
        r"[0-9]+(?:\.[0-9]+)?",
        "",
        text,
        flags=re.I
    ).strip(" -")

    low = text.lower()

    category = "Other"

    if any(
        x in low
        for x in [
            "coffee",
            "tea",
            "food",
            "lunch",
            "dinner",
            "restaurant",
            "snack"
        ]
    ):

        category = "Food"

    elif any(
        x in low
        for x in [
            "bus",
            "train",
            "uber",
            "ola",
            "metro",
            "auto",
            "fuel"
        ]
    ):

        category = "Transport"

    elif any(
        x in low
        for x in [
            "book",
            "course",
            "college",
            "class",
            "exam"
        ]
    ):

        category = "Education"

    elif any(
        x in low
        for x in [
            "movie",
            "game",
            "concert"
        ]
    ):

        category = "Entertainment"

    elif any(
        x in low
        for x in [
            "shirt",
            "dress",
            "shoe",
            "shopping"
        ]
    ):

        category = "Shopping"

    elif any(
        x in low
        for x in [
            "rent",
            "electricity",
            "internet",
            "recharge"
        ]
    ):

        category = "Bills"

    return {
        "title":
            cleaned
            or "Expense",

        "amount":
            amount,

        "category":
            category,

        "note":
            "Parsed locally because Gemini is not configured."
    }


# =========================================================
# AI EXPENSE PARSER
# =========================================================

def parse_expense(text):

    client = _client()

    # No API key -> local fallback
    if not client:

        return _fallback_parse(
            text
        )

    prompt = f"""

You are PocketSmart's expense parser.

Convert the user's natural-language
expense into JSON only.

Allowed categories:

{", ".join(CATEGORIES)}

Return exactly:

{{
    "title": "short title",
    "amount": 0,
    "category": "Food",
    "note": "optional note"
}}

User text:

{text}

"""

    response = client.models.generate_content(

        model=Config.GEMINI_MODEL,

        contents=prompt,

        config=types.GenerateContentConfig(

            response_mime_type="application/json",

            max_output_tokens=300
        )
    )

    data = _extract_json(
        response.text
    )

    data["amount"] = float(
        data.get(
            "amount",
            0
        )
    )

    category = data.get(
        "category"
    )

    if category not in CATEGORIES:

        category = "Other"

    data["category"] = category

    data["title"] = str(
        data.get(
            "title",
            "Expense"
        )
    ).strip()

    data["note"] = str(
        data.get(
            "note",
            ""
        )
    ).strip()

    return data


# =========================================================
# LOCAL FALLBACK INSIGHTS
# =========================================================

def _fallback_insights(summary):

    total = float(
        summary.get(
            "total",
            0
        )
    )

    categories = summary.get(
        "categories",
        []
    )

    if not categories:

        return (
            "Add a few expenses and "
            "I can generate spending insights."
        )

    top = categories[0]

    return (
        f"You have recorded "
        f"₹{total:.2f} in spending. "

        f"Your largest category is "
        f"{top['category']} at "
        f"₹{float(top['total']):.2f}. "

        "Consider setting a simple weekly "
        "limit for your largest category "
        "and reviewing your recent "
        "transactions before making "
        "new purchases."
    )


# =========================================================
# AI INSIGHTS
# =========================================================

def insights(summary):

    client = _client()

    if not client:

        return _fallback_insights(
            summary
        )

    prompt = f"""

You are PocketSmart,
a practical personal budgeting assistant.

Analyze this spending summary:

{json.dumps(
    summary,
    ensure_ascii=False
)}

Give concise,
general informational guidance
in 4-6 bullet points.

Do not claim certainty about
the user's financial situation.

"""

    response = client.models.generate_content(

        model=Config.GEMINI_MODEL,

        contents=prompt,

        config=types.GenerateContentConfig(
            max_output_tokens=700
        )
    )

    return response.text.strip()


# =========================================================
# AI RECOMMENDATIONS
# =========================================================

def recommend(
    budget,
    goal,
    preferences
):

    client = _client()

    if not client:

        return (
            f"Budget: ₹{budget:.2f}. "
            f"Goal: {goal}. "
            f"Preference: "
            f"{preferences or 'not specified'}. "

            "Start by listing 3 options "
            "under budget, compare total "
            "cost and usefulness, and keep "
            "a small buffer rather than "
            "spending the entire budget."
        )

    prompt = f"""

You are PocketSmart,
a general recommendation assistant.

Budget:

₹{budget}

Goal:

{goal}

Preferences:

{preferences or "none"}

Suggest 3-5 options or ideas
that fit the stated budget.

For each option include:

1. Name or idea
2. Short reason
3. Approximate budget allocation

Do not invent exact live prices,
availability, brands, or guarantees.

This is general informational guidance,
not financial advice.

"""

    response = client.models.generate_content(

        model=Config.GEMINI_MODEL,

        contents=prompt,

        config=types.GenerateContentConfig(
            max_output_tokens=900
        )
    )

    return response.text.strip()
