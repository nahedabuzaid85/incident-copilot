import os
from typing import Optional

from dotenv import load_dotenv
from elasticsearch import Elasticsearch


load_dotenv()


_es_client: Optional[Elasticsearch] = None


def get_es() -> Elasticsearch:
    global _es_client
    if _es_client is not None:
        return _es_client

    url = os.getenv("ELASTICSEARCH_URL")
    api_key = os.getenv("ELASTICSEARCH_API_KEY")

    if not url or not api_key:
        raise RuntimeError(
            "ELASTICSEARCH_URL and ELASTICSEARCH_API_KEY must be set in the environment."
        )

    _es_client = Elasticsearch(
        url,
        api_key=api_key,
    )
    return _es_client


def logs_index_name() -> str:
    return os.getenv("INCIDENT_LOGS_INDEX", "incident-demo-logs")


def incidents_index_name() -> str:
    return os.getenv("INCIDENTS_INDEX", "incident-demo-incidents")

