from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .es_client import get_es, incidents_index_name


app = FastAPI(title="Incident Co-Pilot Backend")


@app.get("/")
def root():
    return {
        "app": "Incident Co-Pilot Backend",
        "docs": "/docs",
        "health": "/health",
        "create_incident": "POST /incidents",
        "get_incident": "GET /incidents/{id}",
    }


class IncidentCreate(BaseModel):
    title: str
    summary: str
    root_cause: str
    impact: str
    services: List[str] = Field(default_factory=list)
    remediation: str
    time_window: Optional[str] = None
    raw_context_ids: List[str] = Field(default_factory=list)


class IncidentResponse(IncidentCreate):
    id: str
    created_at: datetime


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/incidents", response_model=IncidentResponse)
def create_incident(incident: IncidentCreate):
    es = get_es()
    index = incidents_index_name()

    doc = incident.dict()
    doc["created_at"] = datetime.now(timezone.utc)

    result = es.index(index=index, document=doc)
    incident_id = result.get("_id")

    if not incident_id:
        raise HTTPException(status_code=500, detail="Failed to create incident")

    return IncidentResponse(id=incident_id, created_at=doc["created_at"], **incident.dict())


@app.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str):
    es = get_es()
    index = incidents_index_name()

    try:
        res = es.get(index=index, id=incident_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail="Incident not found") from exc

    source = res.get("_source") or {}

    return IncidentResponse(
        id=incident_id,
        created_at=source.get("created_at"),
        title=source.get("title", ""),
        summary=source.get("summary", ""),
        root_cause=source.get("root_cause", ""),
        impact=source.get("impact", ""),
        services=source.get("services", []),
        remediation=source.get("remediation", ""),
        time_window=source.get("time_window"),
        raw_context_ids=source.get("raw_context_ids", []),
    )

