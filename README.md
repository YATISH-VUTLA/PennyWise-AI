# 💰 PennyWise AI

**A smart personal expense tracker powered by local AI.**

PennyWise AI helps users record expenses, monitor monthly budgets, visualize spending patterns, and receive AI-generated spending insights using a locally running language model.

## ✨ Features

- **Expense Tracking:** Add, view, and manage expenses.
- **Budget Management:** Set and monitor a monthly budget.
- **Interactive Dashboard:** View expense summaries, category charts, and daily spending trends.
- **Smart Spending Alerts:** Receive warnings when budget usage reaches a threshold or exceeds the monthly budget.
- **Month-End Spending Estimate:** Estimate total spending based on recorded expenses.
- **Category Spending Alerts:** Identify potentially unusual category spending when sufficient historical data is available.
- **CSV Export:** Download expense records for further analysis.
- **Local AI Spending Advisor:** Generate spending observations and practical suggestions using Ollama and Qwen 2.5:3B.
- **SQLite Database:** Store expense records and budget settings locally.

## 🛠️ Technology Stack

- Python
- Streamlit
- Pandas
- Plotly
- SQLite
- Ollama
- Qwen 2.5:3B

## 📋 Prerequisites

Install Python, then install Ollama and download the model used by the application.

```bash
ollama pull qwen2.5:3b
```

## 🚀 Installation and Setup

1. Clone or download this repository.
2. Open a terminal in the project directory.
3. Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

4. Make sure Ollama is installed and the model is available:

```bash
ollama list
```

5. Start PennyWise AI:

```bash
python -m streamlit run app.py
```

6. Open the local URL shown in the terminal.

## 🗂️ Project Structure

```text
PennyWise/
├── app.py
├── ai_helper.py
├── database.py
├── requirements.txt
├── README.md
└── expenses.db        # Local database; do not publish personal records
```

## 🤖 How the AI Works

PennyWise AI sends expense information and the monthly budget to a locally running Ollama model. The model generates spending observations and practical suggestions based on the supplied information.

AI-generated advice may be inaccurate. Verify important financial calculations and decisions against the actual expense records.

## 🔒 Privacy

Expense records are stored in a local SQLite database. The AI integration is configured to use a local Ollama endpoint rather than a hosted AI API. Avoid publishing your database or other personal financial information.

## 🛣️ Future Improvements

- Automated tests and stronger validation of AI-generated insights.
- More advanced spending forecasts.
- Optional category-specific budgets.
- Improved accessibility and user experience.

## 📄 License

The project's open-source license will be specified in the `LICENSE` file.

## 👩‍💻 Contributing

Contributions, bug reports, and suggestions are welcome. Please open an issue or submit a pull request after the repository is published.
