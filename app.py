import calendar
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    create_table,
    add_expense,
    get_expenses,
    delete_expense,
    get_budget,
    set_budget,
)
from ai_helper import generate_spending_insights

st.set_page_config(page_title="PennyWise AI", page_icon="💰", layout="wide")
create_table()

CATEGORIES = [
    "Food", "Transport", "Shopping", "Entertainment",
    "Education", "Bills", "Health", "Other"
]

st.title("💰 PennyWise AI")
st.write("Track expenses, manage your budget, and understand your spending.")
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choose a page",
    ["Dashboard", "Add Expense", "Manage Expenses", "Budget Settings"],
)


def format_month(month_text):
    return pd.to_datetime(month_text + "-01").strftime("%B %Y")


def show_spending_alerts(all_expenses, month_df, selected_month, monthly_budget, total_expenses, budget_used):
    """Display budget alerts and category-spending changes where enough history exists."""
    st.subheader("🔔 Smart Spending Alerts")

    if monthly_budget <= 0:
        st.warning("Set a monthly budget greater than zero to enable budget alerts.")
    elif total_expenses > monthly_budget:
        st.error(
            f"Budget exceeded by ₹{total_expenses - monthly_budget:,.2f}. "
            "Review recent expenses before making additional purchases."
        )
    elif budget_used >= 80:
        st.warning(
            f"You have used {budget_used:.1f}% of your monthly budget. "
            f"Only ₹{monthly_budget - total_expenses:,.2f} remains."
        )
    else:
        st.success(
            f"You have used {budget_used:.1f}% of your monthly budget. "
            "Your spending is currently below the 80% warning level."
        )

    if month_df.empty or all_expenses.empty:
        st.info("Add more expenses to enable category-spending comparisons.")
        return

    selected_period = pd.Period(selected_month, freq="M")
    prior_periods = [selected_period - offset for offset in (1, 2, 3)]
    history = all_expenses.copy()
    history["period"] = history["date"].dt.to_period("M")

    # Compare against the previous three calendar months. Months without spending
    # in a category count as zero, so the comparison uses a consistent time window.
    previous_months_with_data = history[history["period"].isin(prior_periods)]
    if previous_months_with_data.empty:
        st.info("Category alerts will become more useful after you record expenses across more months.")
        return

    current_category_totals = month_df.groupby("category")["amount"].sum()
    historical_category_totals = (
        history[history["period"].isin(prior_periods)]
        .groupby(["period", "category"])["amount"]
        .sum()
    )

    alerts_found = 0
    for category, current_amount in current_category_totals.items():
        previous_amounts = [
            float(historical_category_totals.get((period, category), 0.0))
            for period in prior_periods
        ]
        average_previous = sum(previous_amounts) / len(prior_periods)

        # Avoid comparing against zero; a new category has no reliable baseline.
        if average_previous > 0 and current_amount >= average_previous * 1.5:
            increase = ((current_amount - average_previous) / average_previous) * 100
            st.warning(
                f"**{category}:** ₹{current_amount:,.2f} this month, "
                f"about {increase:.0f}% above the previous three-month average "
                f"of ₹{average_previous:,.2f} per month."
            )
            alerts_found += 1

    if alerts_found == 0:
        st.info(
            "No category has reached 1.5× its previous three-month average. "
            "This comparison is informational and may be limited by sparse history."
        )


if page == "Dashboard":
    st.header("📊 Expense Dashboard")
    raw_df = get_expenses()
    monthly_budget = get_budget()
    current_month = date.today().strftime("%Y-%m")

    if not raw_df.empty:
        raw_df["date"] = pd.to_datetime(raw_df["date"], errors="coerce")
        raw_df["amount"] = pd.to_numeric(raw_df["amount"], errors="coerce")
        raw_df = raw_df.dropna(subset=["date", "amount"])

    available_months = sorted(
        raw_df["date"].dt.strftime("%Y-%m").unique().tolist() if not raw_df.empty else [],
        reverse=True,
    )
    if current_month not in available_months:
        available_months.insert(0, current_month)

    selected_month = st.selectbox(
        "Select month",
        available_months,
        format_func=format_month,
    )

    if raw_df.empty:
        month_df = pd.DataFrame(columns=["id", "amount", "category", "date", "description"])
    else:
        month_df = raw_df[raw_df["date"].dt.strftime("%Y-%m") == selected_month].copy()

    total_expenses = float(month_df["amount"].sum()) if not month_df.empty else 0.0
    remaining_budget = monthly_budget - total_expenses
    budget_used = total_expenses / monthly_budget * 100 if monthly_budget > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monthly Expenses", f"₹{total_expenses:,.2f}")
    col2.metric("Monthly Budget", f"₹{monthly_budget:,.2f}")
    col3.metric("Budget Remaining", f"₹{remaining_budget:,.2f}")
    col4.metric("Budget Used", f"{budget_used:.1f}%")
    st.progress(min(max(budget_used / 100, 0.0), 1.0))

    show_spending_alerts(
        raw_df, month_df, selected_month, monthly_budget, total_expenses, budget_used
    )

    # Month-end forecast is shown only for the current month.
    if selected_month == current_month:
        st.subheader("🔮 Month-End Spending Estimate")
        today = date.today()
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        elapsed_days = max(today.day, 1)
        forecast = total_expenses / elapsed_days * days_in_month
        st.metric("Estimated total by month-end", f"₹{forecast:,.2f}")
        if monthly_budget > 0:
            difference = forecast - monthly_budget
            if difference > 0:
                st.warning(
                    f"At the current average pace, spending may exceed your budget "
                    f"by about ₹{difference:,.2f}."
                )
            else:
                st.info(
                    f"At the current average pace, spending may finish about "
                    f"₹{abs(difference):,.2f} under budget."
                )
        st.caption(
            "Estimate = spending so far ÷ calendar days elapsed × days in this month. "
            "It assumes the current average pace continues; actual spending may differ."
        )

    if month_df.empty:
        st.info("No expenses recorded for this month. Add an expense to get started.")
    else:
        st.subheader("🔎 Filter Expenses")
        categories_in_month = sorted(month_df["category"].dropna().unique().tolist())
        selected_category = st.selectbox(
            "Choose category", ["All Categories"] + categories_in_month
        )

        if selected_category == "All Categories":
            filtered_df = month_df.copy()
        else:
            filtered_df = month_df[month_df["category"] == selected_category].copy()

        st.subheader("🧾 Expense Records")
        display_df = filtered_df.copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv_data = filtered_df.copy()
        csv_data["date"] = csv_data["date"].dt.strftime("%Y-%m-%d")
        st.download_button(
            "⬇️ Export selected month's expenses (CSV)",
            data=csv_data.to_csv(index=False).encode("utf-8"),
            file_name=f"pennywise_expenses_{selected_month}.csv",
            mime="text/csv",
        )

        if not filtered_df.empty:
            category_totals = filtered_df.groupby("category")["amount"].sum().reset_index()
            left, right = st.columns(2)

            with left:
                st.subheader("🥧 Spending Distribution")
                pie_fig = px.pie(
                    category_totals,
                    names="category",
                    values="amount",
                    title="Expenses by Category",
                )
                st.plotly_chart(pie_fig, use_container_width=True)

            with right:
                st.subheader("📊 Category Comparison")
                bar_fig = px.bar(
                    category_totals,
                    x="category",
                    y="amount",
                    labels={"category": "Category", "amount": "Amount (₹)"},
                    title="Expenses by Category",
                    text_auto=".2f",
                )
                st.plotly_chart(bar_fig, use_container_width=True)

            st.subheader("📈 Daily Spending Trend")
            daily_totals = (
                filtered_df.groupby(filtered_df["date"].dt.strftime("%Y-%m-%d"))["amount"]
                .sum()
                .reset_index()
            )
            daily_totals.columns = ["Date", "Amount"]
            line_fig = px.line(
                daily_totals,
                x="Date",
                y="Amount",
                markers=True,
                title="Daily Expenses",
                labels={"Amount": "Amount (₹)"},
            )
            st.plotly_chart(line_fig, use_container_width=True)

            st.subheader("💡 Spending Insights")
            highest_category = category_totals.loc[category_totals["amount"].idxmax()]
            st.write(
                f"Your highest-spending category in the current filter is "
                f"**{highest_category['category']}**, with expenses of "
                f"**₹{highest_category['amount']:,.2f}**."
            )
            st.write(f"You recorded **{len(month_df)} expenses** in this month.")
            if total_expenses > 0:
                st.write(
                    f"Your average expense amount is **₹{month_df['amount'].mean():,.2f}**."
                )

        st.subheader("🤖 AI Spending Advisor")
        st.write(
            "Get data-based observations and practical suggestions from your local AI model."
        )
        if st.button("Generate AI Insights"):
            expenses_for_ai = []
            for _, row in month_df.iterrows():
                description = row.get("description", "No description")
                if pd.isna(description) or not str(description).strip():
                    description = "No description"
                expenses_for_ai.append(
                    {
                        "date": row["date"].strftime("%Y-%m-%d"),
                        "category": str(row["category"]),
                        "amount": float(row["amount"]),
                        "description": str(description),
                    }
                )
            with st.spinner("AI is analyzing your expenses..."):
                ai_result = generate_spending_insights(expenses_for_ai, monthly_budget)
            st.markdown(ai_result)

elif page == "Add Expense":
    st.header("➕ Add a New Expense")
    with st.form("expense_form", clear_on_submit=True):
        amount = st.number_input(
            "Amount (₹)", min_value=0.0, step=10.0, format="%.2f"
        )
        category = st.selectbox("Category", CATEGORIES)
        expense_date = st.date_input(
            "Expense Date", value=date.today(), max_value=date.today()
        )
        description = st.text_input(
            "Description", placeholder="e.g. Lunch, bus ticket, books"
        )
        submitted = st.form_submit_button("Save Expense")
        if submitted:
            if amount <= 0:
                st.warning("Please enter an amount greater than zero.")
            else:
                add_expense(amount, category, expense_date, description.strip())
                st.success("Expense saved successfully!")

elif page == "Manage Expenses":
    st.header("🗂️ Manage Expenses")
    if st.session_state.get("reset_confirm_delete", False):
        st.session_state["confirm_delete"] = False
        st.session_state["reset_confirm_delete"] = False

    df = get_expenses()
    if df.empty:
        st.info("There are no expenses to manage yet.")
    else:
        st.subheader("⬇️ Export Your Expense History")
        export_df = df.copy()
        export_df["date"] = pd.to_datetime(export_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        st.download_button(
            "Download all expenses as CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="pennywise_all_expenses.csv",
            mime="text/csv",
        )

        st.write("Select an expense below if you want to delete it.")
        expense_options = {
            (
                f"ID {row['id']} | {row['date']} | {row['category']} | "
                f"₹{row['amount']:.2f} | {row['description'] or 'No description'}"
            ): int(row["id"])
            for _, row in df.iterrows()
        }
        selected_expense = st.selectbox("Choose an expense", list(expense_options.keys()))
        confirm_delete = st.checkbox(
            "I confirm that I want to delete this expense.", key="confirm_delete"
        )
        if st.button("🗑️ Delete Expense", type="primary"):
            if confirm_delete:
                delete_expense(expense_options[selected_expense])
                st.session_state["reset_confirm_delete"] = True
                st.success("Expense deleted successfully!")
                st.rerun()
            else:
                st.warning("Please confirm before deleting.")

elif page == "Budget Settings":
    st.header("⚙️ Budget Settings")
    current_budget = get_budget()
    st.write(f"Your current monthly budget is ₹{current_budget:,.2f}.")
    with st.form("budget_form"):
        new_budget = st.number_input(
            "Set monthly budget (₹)",
            min_value=1.0,
            value=float(current_budget),
            step=500.0,
            format="%.2f",
        )
        budget_submitted = st.form_submit_button("Save Budget")
        if budget_submitted:
            set_budget(new_budget)
            st.success(f"Monthly budget updated to ₹{new_budget:,.2f}.")
