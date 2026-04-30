import requests
import logging
from app.core.config import GHL_API_KEY

logger = logging.getLogger("ghl_client")

GHL_BASE_URL = "https://services.leadconnectorhq.com"


# ===============================
# COMMON HEADERS
# ===============================
def _headers():
    return {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }


# ===============================
# CREATE OPPORTUNITY
# ===============================
def create_opportunity(payload):

    logger.info("========== GHL CREATE REQUEST ==========")
    logger.info(f"Payload: {payload}")

    resp = requests.post(
        f"{GHL_BASE_URL}/opportunities/",
        headers=_headers(),
        json=payload
    )

    logger.info("========== GHL CREATE RESPONSE ==========")
    logger.info(f"STATUS: {resp.status_code}")
    logger.info(f"BODY: {resp.text}")

    if resp.status_code in (200, 201):
        logger.info("✅ SUCCESS create opportunity")
    else:
        logger.error("❌ ERROR creating opportunity")

    return resp


# ===============================
# UPDATE OPPORTUNITY (DESHABILITADO EN SERVICE)
# ===============================
def update_opportunity(opportunity_id, payload):

    logger.info("========== GHL UPDATE REQUEST ==========")
    logger.info(f"Opportunity ID: {opportunity_id}")
    logger.info(f"Payload: {payload}")

    resp = requests.put(
        f"{GHL_BASE_URL}/opportunities/{opportunity_id}",
        headers=_headers(),
        json=payload
    )

    logger.info("========== GHL UPDATE RESPONSE ==========")
    logger.info(f"STATUS: {resp.status_code}")
    logger.info(f"BODY: {resp.text}")

    if resp.status_code in (200, 201):
        logger.info(f"✅ SUCCESS update opp {opportunity_id}")
    else:
        logger.error(f"❌ ERROR updating opp {opportunity_id}")

    return resp