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
4. Run locally:
   python main.py

For production, set `FLASK_ENV=production` and a long random `FLASK_SECRET_KEY` in the process environment. Production mode refuses to start without the secret and disables Flask debug mode. Do not expose this prototype publicly until authentication/authorization and CSRF protections are implemented.

The built-in assistant currently uses deterministic Arabic/English intent rules; it is not connected to an external LLM. No AI API key is embedded in the repository. An LLM provider must be configured before claiming free-form AI understanding.

## How to use
- Access the system via `http://localhost:5000`
- Use the Sidebar to navigate between modules.
- Use the AI Assistant (floating robot icon) to perform actions using natural language.
