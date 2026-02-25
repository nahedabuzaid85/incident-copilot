import random
from datetime import datetime, timedelta, timezone
from typing import List

from elasticsearch import helpers

from app.es_client import get_es, logs_index_name


SERVICES = ["checkout", "payments", "inventory"]
ENDPOINTS = {
    "checkout": ["/checkout", "/checkout/confirm"],
    "payments": ["/payments/charge", "/payments/refund"],
    "inventory": ["/inventory/reserve", "/inventory/release"],
}
LEVELS = ["INFO", "WARN", "ERROR"]
REGIONS = ["eu-west-1", "us-east-1"]


def build_mapping():
    return {
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "service": {"type": "keyword"},
                "endpoint": {"type": "keyword"},
                "level": {"type": "keyword"},
                "trace_id": {"type": "keyword"},
                "message": {"type": "text"},
                "latency_ms": {"type": "float"},
                "region": {"type": "keyword"},
            }
        }
    }


def generate_logs(
    start: datetime, minutes: int = 120, baseline_per_minute: int = 20
) -> List[dict]:
    docs: List[dict] = []
    current = start

    incident_start = start + timedelta(minutes=30)
    incident_end = incident_start + timedelta(minutes=30)

    while current < start + timedelta(minutes=minutes):
        is_incident_window = incident_start <= current <= incident_end
        per_minute = baseline_per_minute * (3 if is_incident_window else 1)

        for _ in range(per_minute):
            service = random.choice(SERVICES)
            endpoint = random.choice(ENDPOINTS[service])
            region = random.choice(REGIONS)

            if is_incident_window and service == "checkout" and "confirm" in endpoint:
                level = "ERROR" if random.random() < 0.7 else "WARN"
                latency = random.uniform(800, 2000)
                message = "Timeout while calling payments-v2 from checkout"
            else:
                level = random.choices(LEVELS, weights=[0.8, 0.15, 0.05])[0]
                latency = random.uniform(50, 400)
                message = "Request completed successfully"

            docs.append(
                {
                    "@timestamp": current.isoformat(),
                    "service": service,
                    "endpoint": endpoint,
                    "level": level,
                    "trace_id": f"trace-{random.randint(1, 10_000)}",
                    "message": message,
                    "latency_ms": latency,
                    "region": region,
                }
            )

        current += timedelta(minutes=1)

    return docs


def main():
    es = get_es()
    index = logs_index_name()

    if es.indices.exists(index=index):
        es.indices.delete(index=index)

    es.indices.create(index=index, body=build_mapping())

    start_time = datetime.now(timezone.utc) - timedelta(hours=3)
    docs = generate_logs(start_time, minutes=120)

    print(f"Indexing {len(docs)} log documents into {index}...")

    actions = ({"_index": index, "_source": doc} for doc in docs)
    helpers.bulk(es, actions)

    print("Done.")


if __name__ == "__main__":
    main()

