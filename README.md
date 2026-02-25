# Incident Co-Pilot – Elasticsearch Agent Builder Hackathon

This project is an **incident response co-pilot** built for the **Elasticsearch Agent Builder Hackathon**.

It showcases a **multi-step agent** that:

- Understands a natural-language incident request (e.g. “Investigate latency spike on checkout between 09:00–10:00 UTC”).
- Uses **Elasticsearch Search + ES|QL tools** to pull relevant logs and metrics for a time range and service.
- Analyzes patterns (error spikes, outlier services, endpoints) with an LLM.
- Can call a **`create_incident`** tool backed by a FastAPI service to open an incident record with title, summary, root cause, impact, services, remediation, and time window.

The goal is to show how many manual steps are removed compared to traditional dashboards and ad-hoc queries.

---

## Architecture

- **Elastic Agent Builder**
  - Custom **Incident Co-Pilot** agent with SRE co-pilot instructions.
  - Tools: built-in **Search** and **ES|QL** over the logs index, plus custom HTTP tool **`create_incident`** that calls the FastAPI backend.
  - Used via **Agent Chat** in Kibana.

- **Elasticsearch**
  - **`incident-demo-logs`** – Synthetic application logs: `@timestamp`, `service`, `endpoint`, `level`, `trace_id`, `message`, `latency_ms`, `region`.
  - **`incident-demo-incidents`** – Incident records created by the agent: `created_at`, `title`, `summary`, `root_cause`, `impact`, `services`, `remediation`, `time_window`, `raw_context_ids`.

- **FastAPI backend (Python)**
  - `GET /` – API info and endpoint list.
  - `GET /health` – Health check.
  - `POST /incidents` – Create an incident document in `incident-demo-incidents`.
  - `GET /incidents/{id}` – Fetch an incident by ID.

---

## Project structure

- `README.md` – This file.
- `requirements.txt` – Python dependencies.
- `run.ps1` – Run the API from project root (sets `PYTHONPATH`, starts uvicorn).
- `app/main.py` – FastAPI app and incident endpoints.
- `app/es_client.py` – Elasticsearch client and index names.
- `scripts/generate_sample_logs.py` – Generate synthetic logs and index into `incident-demo-logs`.

---

## Setup

1. **Elastic deployment**
   - Create an Elasticsearch Serverless project (or Elastic Cloud deployment).
   - Enable Agent Builder. Note: Elasticsearch endpoint URL, Kibana URL, and an API key with read/write access to your indices.

2. **Local environment**
   - From the project root:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     pip install -r requirements.txt
     ```

3. **Environment variables**
   - Create a `.env` file (do not commit it) with:
     ```bash
     ELASTICSEARCH_URL=https://<your-elastic-endpoint>
     ELASTICSEARCH_API_KEY=<your-base64-api-key>
     INCIDENT_LOGS_INDEX=incident-demo-logs
     INCIDENTS_INDEX=incident-demo-incidents
     ```

4. **Generate sample logs**
   - From project root (with `PYTHONPATH` set, or use `run.ps1`’s directory):
     ```bash
     python scripts/generate_sample_logs.py
     ```
   - This creates `incident-demo-logs` and indexes synthetic logs for `checkout`, `payments`, and `inventory` with an incident window for demo.

5. **Run the API**
   - From project root:
     ```bash
     .\run.ps1
     ```
   - Or:
     ```bash
     $env:PYTHONPATH = "<project-root-path>"
     uvicorn app.main:app --reload --port 8000
     ```
   - Then: `GET http://localhost:8000/health` → `{"status":"ok"}`.

6. **Agent Builder (Kibana)**
   - Create a custom HTTP tool `create_incident`: `POST http://localhost:8000/incidents` with body fields: `title`, `summary`, `root_cause`, `impact`, `services`, `remediation`, `time_window`, `raw_context_ids`.
   - Create a custom agent (Incident Co-Pilot) with instructions to use ES|QL and Search on `incident-demo-logs` and to call `create_incident` when opening an incident. Attach the Search, ES|QL, and `create_incident` tools.

---

## Demo flow

1. In Agent Chat, ask e.g.: “Investigate errors and latency spikes on the checkout service in the incident-demo-logs index over the past 3 hours.”
2. The agent uses ES|QL and Search, then returns a summary with root cause, impact, and recommendations.
3. Ask it to create an incident; it calls `create_incident` and returns the incident ID and summary.
4. You can verify with `GET http://localhost:8000/incidents/{id}`.
