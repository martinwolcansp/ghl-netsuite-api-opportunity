# app/clients/ghl_client.py

import requests
import logging
from app.core.config import GHL_API_KEY, GHL_LOCATION_ID

logger = logging.getLogger("ghl_client")

GHL_BASE_URL = "https://services.leadconnectorhq.com"


# ===============================
# CREATE OPPORTUNITY
# ===============================
def create_opportunity(payload):

    logger.info("========== GHL CREATE REQUEST ==========")
    logger.info(payload)

    resp = requests.post(
        f"{GHL_BASE_URL}/opportunities/",
        headers={
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Version": "2021-07-28"
        },
        json=payload
    )

    return resp


# ===============================
# UPDATE OPPORTUNITY (UNIFICADO)
# ===============================
def update_opportunity(opportunity_id, payload):

    logger.info("========== GHL UPDATE REQUEST ==========")
    logger.info(f"Opportunity ID: {opportunity_id}")
    logger.info(f"Payload: {payload}")

    resp = requests.put(
        f"{GHL_BASE_URL}/opportunities/{opportunity_id}",
        headers={
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Version": "2021-07-28"
        },
        json=payload
    )

    logger.info(f"GHL RESPONSE STATUS: {resp.status_code}")
    logger.info(f"GHL RESPONSE BODY: {resp.text}")

    return resp