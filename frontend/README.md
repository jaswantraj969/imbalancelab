# frontend

Streamlit client for the ImbalanceLab API (milestone M8). It talks to the FastAPI service over
HTTP only (`api_client.py`, using `requests`) and never imports the `imbalancelab` package; a
test enforces this.

```bash
uvicorn imbalancelab.api.app:app --host 127.0.0.1 --port 8000   # terminal 1 (local only)
IMBALANCELAB_API_URL=http://127.0.0.1:8000 streamlit run frontend/app.py   # terminal 2
```

Pages: upload + profile, configure + launch run, results + thresholds, final evaluation, report.
