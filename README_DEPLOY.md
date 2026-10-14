# Deployment Guide - Financial Engineer ERP

## Prerequisites
- Python 3.8+
- pip install flask sqlalchemy

## Installation
1. Clone the repository:
   git clone https://github.com/morabaya/Financial-Engineer-ERP-and-Accounting-System.git
2. Navigate to the folder:
   cd Financial-Engineer-ERP-and-Accounting-System
3. Install dependencies:
   python -m pip install -r requirements.txt
4. Set `INITIAL_ADMIN_PASSWORD` and (recommended) `FLASK_SECRET_KEY` in the process environment. `.env.example` lists supported names; the app does not load `.env` automatically.
5. Run locally:
   python main.py
6. Run the regression suite:
   python -m unittest discover -s tests -v

For an initial administrator, set `INITIAL_ADMIN_PASSWORD` before startup; the password is stored using Werkzeug's password hashing (there is no hard-coded default). Login is required for application pages and APIs. Set `FLASK_SECRET_KEY` to a long random value for persistent sessions. Production mode (`FLASK_ENV=production`) requires that key and disables Flask debug mode. Use HTTPS. Do not expose this as a production accounting service until role-based authorization and CSRF protection are fully implemented and security-reviewed.

The built-in assistant uses deterministic Arabic/English intent rules; money-moving AI commands now require a separate explicit confirmation. It is not connected to an external LLM; no AI API key is embedded in the repository. An LLM provider must be configured and independently security-tested before claiming free-form AI understanding.

## How to use
- Access the system via `http://localhost:5000`
- Use the Sidebar to navigate between modules.
- Use the AI Assistant (floating robot icon) to perform actions using natural language.
