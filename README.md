# Liquidity Intelligence Studio

This app is a Streamlit dashboard for liquidity risk analytics.

## Run locally

```bash
streamlit run app.py
```

## Deploy to Render

Use the following settings in Render:
- Root Directory: streamlit
- Build Command: pip install -r requirements.txt
- Start Command: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless true
