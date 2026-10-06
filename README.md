# Shahpur Smart Job Finder

Smart job discovery and matching tool for **Logistics, Supply Chain, Aviation, Procurement and Operations** roles across Pakistan, GCC and Europe.

## Features
- Logistics, supply-chain and aviation focused keyword matching
- Priority locations: Lahore, Sheikhupura, Gujranwala and Sialkot
- Pakistan, GCC and Europe location preferences
- Match scoring and duplicate removal
- Remote-only filter
- Direct vacancy links
- CSV export
- Public job feeds requiring no API key in the initial version

## Current data sources
- Arbeitnow public job-board API
- Remote OK public JSON feed

Always verify the vacancy, employer and application destination before submitting personal information.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
This repository is structured for Streamlit Community Cloud. Use `app.py` as the entrypoint.
