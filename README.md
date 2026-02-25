Incident Co‑Pilot – Elasticsearch Agent Builder Hackathon
=========================================================

This project is an **incident response co‑pilot** built for the **Elasticsearch Agent Builder Hackathon**.

It showcases a **multi‑step agent** that:

- Understands a natural‑language incident request (for example: “Investigate latency spike on checkout between 09:00–10:00 UTC”).
- Uses **Elasticsearch Search + ES|QL tools** to pull relevant logs/metrics for a time range and service.
- Analyzes patterns (error spikes, outlier services, endpoints) with an LLM.
- Calls a **`create_incident` action tool** backed by a small FastAPI service to open an incident record containing:
  - Title and short summary.
  - Suspected root cause.
  - Impacted services / endpoints.
  - Suggested remediation steps.
  - Time window and key metrics.

The goal for the demo is to show **how many manual steps are removed** versus traditional dashboards and ad‑hoc queries.

---

Quick architecture
------------------

- **Elastic Agent Builder**
  - Custom **Incident Co‑Pilot agent** with:
    - System prompt: “You are an SRE incident co‑pilot…”
    - Access to:
      - Built‑in **Search** tools over a `logs-*` index.
      - Built‑in **ES|QL** tool for aggregations over the same index.
      - Custom HTTP tool **`create_incident`** that calls the FastAPI backend.
  - Used via **Agent Chat in Kibana** for the live demo.

- **Elasticsearch indexes**
  - `logs-incident-demo`
    - Synthetic application logs with:
      - `@timestamp` (date)
      - `service` (keyword)
      - `endpoint` (keyword)
      - `level` (keyword: INFO/WARN/ERROR)
      - `trace_id` (keyword)
      - `message` (text)
      - `latency_ms` (float)
      - `region` (keyword, optional)
  - `incidents-incident-demo`
    - Incident records created by the agent:
      - `created_at`, `title`, `summary`, `root_cause`, `impact`, `services`, `remediation`, `time_window`, `raw_context_ids` (list of related log IDs).

- **FastAPI backend (Python)**
  - Exposes:
    - `POST /incidents` – create a new incident document in `incidents-incident-demo`.
    - `GET /incidents/{id}` – fetch a created incident (for debugging/demo).
  - Used by the Agent Builder custom HTTP tool as the backing implementation for `create_incident`.

---

Local project structure
-----------------------

Planned structure under `d:\\elastic`:

- `README.md` – this file; high‑level description + setup.
- `requirements.txt` – Python dependencies.
- `app/main.py` – FastAPI app with `/health` and `/incidents` endpoints.
- `app/es_client.py` – helper to talk to your Elastic deployment using an API key.
- `scripts/generate_sample_logs.py` – generate synthetic logs and bulk index into `logs-incident-demo`.
- `scripts/show_sample_queries.py` – example ES|QL / search queries used by the agent (helpful for docs/demo).

---

Setup checklist (high level)
----------------------------

1. **Elastic deployment + Agent Builder**
   - Create an Elasticsearch Serverless project or Elastic Cloud deployment.
   - Enable **Agent Builder** and note:
     - Elasticsearch endpoint URL.
     - Kibana/Agent Builder URL.
     - API key with permissions to read/write the `logs-incident-demo` and `incidents-incident-demo` indexes.

2. **Local Python environment**
   - From `d:\\elastic`:

     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     pip install -r requirements.txt
     ```

3. **Configure environment variables**
   - Create a `.env` file (not committed) with:

     ```bash
     ELASTICSEARCH_URL=https://<your-elastic-endpoint>
     ELASTICSEARCH_API_KEY=<your-base64-api-key>
     INCIDENT_LOGS_INDEX=logs-incident-demo
     INCIDENTS_INDEX=incidents-incident-demo
     ```

4. **Generate and index sample logs**
   - Run:

     ```bash
     python scripts/generate_sample_logs.py
     ```

   - This will:
     - Create the `logs-incident-demo` index with a simple mapping (if needed).
     - Index synthetic logs for 2–3 services (`checkout`, `payments`, `inventory`) with a clear “incident window” you can search later.

5. **Run the FastAPI backend**
   - Start the API:

     ```bash
     uvicorn app.main:app --reload --port 8000
     ```

   - You should see:
     - `GET /health` → `{ "status": "ok" }`
     - `POST /incidents` → creates a document in `incidents-incident-demo`.

6. **Configure Agent Builder agent and tools (in Kibana UI)**
   - Create a **custom HTTP tool**:
     - Name: `create_incident`
     - Description: “Create an incident record summarizing an investigation result.”
     - Method/URL: `POST http://localhost:8000/incidents`
     - Request body schema: fields for `title`, `summary`, `root_cause`, `impact`, `services`, `remediation`, `time_window`, `raw_context_ids`.
   - Create a **custom agent**:
     - Instructions: Describe that it is an SRE co‑pilot that:
       - Uses ES|QL for time‑bounded aggregations over `logs-incident-demo`.
       - Uses Search to fetch detailed example logs.
       - Calls `create_incident` once it has a clear incident hypothesis and wants to take action.
     - Add tools:
       - Built‑in Search / ES|QL tools for the logs index.
       - Custom `create_incident` HTTP tool.

7. **Demo flow for the video**
   - In Agent Chat:
     1. Ask: “Investigate error spike on `checkout` between 2025‑10‑10T09:00 and 2025‑10‑10T10:00 UTC.”
     2. Show the agent:
        - Calls ES|QL to get error counts/latency by service + endpoint.
        - Calls Search to pull a few representative log lines.
        - Explains suspected root cause and impact.
     3. Ask it to **open an incident**.
        - It calls `create_incident`, then replies with the incident ID and summary.
     4. Optionally hit `GET /incidents/{id}` in your FastAPI app to prove the record exists.

---

Devpost submission notes (outline)
----------------------------------

- **Problem**: On‑call engineers lose time manually digging through dashboards and logs to understand incidents and then create tickets.
- **Solution**: An Agent Builder–powered incident co‑pilot that:
  - Investigates via ES|QL + Search over logs.
  - Produces a structured root‑cause summary.
  - Automatically opens an incident record with full context.
- **Elastic features used**:
  - Agent Builder custom agent + tools (Search, ES|QL, custom HTTP tool).
  - Elasticsearch for logs + incident storage.
  - Optional: Workflows (if you later wire incidents into an Elastic Workflow step).
- **Impact / Wow factor**:
  - Compresses many manual steps (dashboards, multiple queries, copy‑pasting into tickets) into a single chat interaction.
  - Demonstrates safe, explainable action‑taking by agents.

