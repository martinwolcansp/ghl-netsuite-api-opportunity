# app/services/ghl_opportunity_service.py

import logging
import requests

from app.clients.ghl_client import update_opportunity
from app.core.config import (
    GHL_API_KEY,
    GHL_LOCATION_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
)

logger = logging.getLogger("ghl_service")

GHL_BASE_URL = "https://services.leadconnectorhq.com"


# ===============================
# SEARCH OPPORTUNITY (ESTILO PRESUPUESTO)
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

    matching = None

    for opp in opportunities:

        logger.info("--------------------------------------")
        logger.info(f"Checking Opportunity ID: {opp.get('id')}")
        logger.info(f"Name: {opp.get('name')}")

        custom_fields = opp.get("customFields", [])

        logger.info(f"🧩 Custom fields: {len(custom_fields)}")

        for cf in custom_fields:

            value = cf.get("fieldValue") or cf.get("fieldValueString")

            logger.info(f"CF {cf.get('id')} = {value}")

            if (
                cf.get("id") == CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
                and str(value) == str(opportunity_id)
            ):
                matching = opp
                logger.info("🎯 MATCH FOUND IN CUSTOM FIELD")
                break

        if matching:
            break

    if not matching:
        logger.warning("❌ Opportunity not found in GHL")
        return None

    logger.info(f"✅ MATCH SELECTED: {matching.get('id')}")
    return matching


# ===============================
# SYNC (MODEL PRESUPUESTO)
# ===============================
def sync_opportunity(
    contact_id,
    opportunity_id,
    monto,
    status,
    stage_id,
    update_payload_builder
):

    logger.info("========== OPPORTUNITY SYNC NS → GHL ==========")
    logger.info(f"NS Opportunity ID: {opportunity_id}")
    logger.info(f"Monto: {monto}")
    logger.info(f"Status: {status}")
    logger.info(f"Stage ID: {stage_id}")

    matching = find_opportunity(contact_id, opportunity_id)

    if not matching:
        logger.warning("❌ No matching opportunity found")
        return {"error": "not_found"}

    ghl_id = matching["id"]

    # ===============================
    # IDEMPOTENCY CHECK (ESTILO PRESUPUESTO)
    # ===============================
    current_stage = matching.get("pipelineStageId")
    current_status = matching.get("status")
    current_value = matching.get("monetaryValue")

    logger.info("========== IDEMPOTENCY CHECK ==========")
    logger.info(f"Current stage: {current_stage}")
    logger.info(f"Current status: {current_status}")
    logger.info(f"Current value: {current_value}")

    already = (
        str(current_value) == str(monto)
        and current_stage == stage_id
        and current_status == status
    )

    if already:
        logger.info("⏭ No changes detected (idempotent)")
        return {"status": "already_updated"}

    # ===============================
    # UPDATE
    # ===============================
    logger.info("========== FINAL UPDATE ==========")
    logger.info(f"Updating Opportunity ID: {ghl_id}")
    logger.info(f"→ stage={stage_id}")
    logger.info(f"→ status={status}")
    logger.info(f"→ value={monto}")

    payload = update_payload_builder(matching)

    resp = update_opportunity(
        opportunity_id=ghl_id,
        monetary_value=monto,
        status=status,
        pipeline_stage_id=stage_id,
        custom_fields=payload.get("customFields", [])
    )

    logger.info(f"GHL RESPONSE STATUS: {resp.status_code}")
    logger.info(f"GHL RESPONSE BODY: {resp.text}")

    return {
        "action": "updated",
        "id": ghl_id,
        "status": resp.status_code
    }