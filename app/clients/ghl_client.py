# app/clients/ghl_client.py

import requests
from app.core.config import GHL_API_KEY

GHL_BASE_URL = "https://services.leadconnectorhq.com"


def ghl_headers():
    return {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }


def search_opportunities(location_id, contact_id):
    return requests.get(
        f"{GHL_BASE_URL}/opportunities/search",
        headers=ghl_headers(),
        params={
            "location_id": location_id,
            "contact_id": contact_id,
            "limit": 100
        },
        timeout=30
    )


def create_opportunity(payload):
    return requests.post(
        f"{GHL_BASE_URL}/opportunities/",
        headers=ghl_headers(),
        json=payload,
        timeout=30
    )


def update_opportunity(opportunity_id, payload):
    return requests.put(
        f"{GHL_BASE_URL}/opportunities/{opportunity_id}",
        headers=ghl_headers(),
        json=payload,
        timeout=30
    )