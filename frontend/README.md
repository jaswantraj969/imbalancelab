# frontend

Streamlit client for the ImbalanceLab API (milestone M8). It talks to the FastAPI service over
HTTP only (`api_client.py`, using `requests`) and never imports the `imbalancelab` package; a
test enforces this.

```bash
uvicorn imbalancelab.api.app:app            # terminal 1
IMBALANCELAB_API_URL=http://localhost:8000 streamlit run frontend/app.py   # terminal 2
```

Pages: upload + profile, configure + launch run, results + thresholds, final evaluation, report.
