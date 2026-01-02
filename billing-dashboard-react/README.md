# Billing Dashboard (React)

This folder contains an optional React dashboard UI.

Current backend reality:
- The primary working UI is Streamlit (`streamlit_app.py`).
- A Flask API (`app.py`) exists for webhook-style integrations and can also be used as an API surface for a frontend.

## Run locally

Prereqs: Node.js 18+

```powershell
cd billing-dashboard-react
npm install
npm run dev
```

## Connecting to the backend

If this frontend is wired to call an API, ensure the Flask server is running (and configured) on the expected host/port.
See the repo root `README.md` for the current recommended run path and environment configuration.
