# app/services/ghl_opportunity_service.py

import logging
import requests

from app.clients.ghl_client import update_opportunity, create_opportunity
from app.core.config import (
    GHL_API_KEY,
    GHL_LOCATION_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
)

logger = logging.getLogger("ghl_service")

GHL_BASE_URL = "https://services.leadconnectorhq.com"


# ===============================
# SEARCH (IGUAL PRESUPUESTO)
# ===============================
def find_opportunity(contact_id, opportunity_id):

    logger.info("========== GHL OPPORTUNITY SEARCH ==========")
    logger.info(f"Contact ID: {contact_id}")
    logger.info(f"NS Opportunity ID: {opportunity_id}")

    resp = requests.get(
        f"{GHL_BASE_URL}/opportunities/search",
        headers={
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Accept": "application/json",
            "Version": "2021-07-28"
        },
        params={
            "location_id": GHL_LOCATION_ID,
            "contact_id": contact_id
        }
    )

    if resp.status_code not in (200, 201):
        logger.error(f"GHL search error: {resp.text}")
        return None

    opportunities = resp.json().get("opportunities", [])

    logger.info(f"📦 Opportunities found: {len(opportunities)}")

    for opp in opportunities:

        logger.info("--------------------------------------")
        logger.info(f"Checking Opp ID: {opp.get('id')}")

        for cf in opp.get("customFields", []):

            value = (
                cf.get("fieldValue")
                or cf.get("fieldValueString")
                or cf.get("value")
            )

            logger.info(f"CF {cf.get('id')} = {value}")

            if (
                cf.get("id") == CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
                and str(value) == str(opportunity_id)
            ):
                logger.info("🎯 MATCH FOUND")
                return opp

    logger.warning("❌ No matching opportunity found")
    return None


# ===============================
# UPSERT (MISMA LÓGICA PRESUPUESTO)
# ===============================
def sync_opportunity(contact_id, opportunity_id, create_payload, update_payload_builder):

    logger.info("========== OPPORTUNITY SYNC NS → GHL ==========")
    logger.info(f"NS Opportunity ID: {opportunity_id}")

    matching = find_opportunity(contact_id, opportunity_id)

    # ===============================
    # CREATE
    # ===============================
    if not matching:

        logger.warning("⚠️ Not found → CREATE")

        resp = create_opportunity(create_payload)

        logger.info("========== CREATE RESPONSE ==========")
        logger.info(resp.text)

        return {"action": "created"}

    # ===============================
    # UPDATE
    # ===============================
    ghl_id = matching["id"]

    logger.info("========== EXISTING OPPORTUNITY ==========")
    logger.info(f"GHL ID: {ghl_id}")

    payload = update_payload_builder(matching)

    current_stage = matching.get("pipelineStageId")
    current_status = matching.get("status")

    if (
        current_stage == payload.get("pipelineStageId")
        and current_status == payload.get("status")
    ):
        logger.info("⏭ No changes (idempotent)")
        return {"status": "already_updated"}

    logger.info("========== FINAL UPDATE ==========")
    logger.info(f"Stage: {current_stage} → {payload.get('pipelineStageId')}")
    logger.info(f"Status: {current_status} → {payload.get('status')}")

    resp = update_opportunity(
        opportunity_id=ghl_id,
        payload=payload
    )

    return {"action": "updated"}