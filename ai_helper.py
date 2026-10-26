import requests


def generate_spending_insights(expenses, monthly_budget):
    """Ask the locally running Ollama model for grounded spending observations."""
    if not expenses:
        return "There are no expenses to analyze yet."

    total_spent = sum(float(item.get("amount", 0) or 0) for item in expenses)
    category_totals = {}
    for item in expenses:
        category = str(item.get("category", "Other"))
        category_totals[category] = category_totals.get(category, 0.0) + float(
            item.get("amount", 0) or 0
        )

    category_summary = "\n".join(
        f"- {category}: Rs. {amount:.2f}"
        for category, amount in sorted(
            category_totals.items(), key=lambda pair: pair[1], reverse=True
        )
    )
    expense_details = []
    for item in expenses:
        description = item.get("description") or "No description"
        expense_details.append(
            f"Date: {item.get('date', 'Unknown')}, "
            f"Category: {item.get('category', 'Other')}, "
            f"Amount: Rs. {float(item.get('amount', 0) or 0):.2f}, "
            f"Description: {description}"
        )

    budget_used = (total_spent / float(monthly_budget) * 100) if monthly_budget > 0 else 0
    prompt = f"""
You are PennyWise AI, a careful personal-finance assistant.

Analyze only the expense data below. Do not invent transactions, income, debts,
financial goals, or facts that were not provided. Do not shame the user or give
investment, tax, or legal advice.

Monthly budget: Rs. {float(monthly_budget):.2f}
Total spending in the supplied period: Rs. {total_spent:.2f}
Budget used: {budget_used:.1f}%
Category totals:
{category_summary}

Expense records:
{chr(10).join(expense_details)}

Write a concise response with these sections:
1. Spending summary (use the supplied totals).
2. Highest-spending category (use the category totals).
3. Budget status (state whether the supplied spending is below, near, or above budget).
4. Up to two patterns that are directly supported by the records; if there is too little data, say so.
5. Three practical, non-judgmental suggestions.

Use simple English. Be transparent when there is not enough data to draw a conclusion.
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        answer = result.get("response", "").strip()
        return answer or "The AI did not return a response."

    except requests.exceptions.ConnectionError:
        return "Could not connect to Ollama. Please make sure Ollama is running."
    except requests.exceptions.Timeout:
        return "The AI took too long to respond. Please try again."
    except requests.exceptions.RequestException as error:
        return f"Could not generate insights: {error}"
    except (ValueError, TypeError):
        return "The AI returned a response that could not be read. Please try again."
