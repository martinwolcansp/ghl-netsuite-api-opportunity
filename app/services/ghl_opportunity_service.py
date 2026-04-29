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
# SEARCH OPPORTUNITY BY NS CUSTOM FIELD
# ===============================
def find_opportunity(contact_id, opportunity_id):

    logger.info("========== GHL OPPORTUNITY SEARCH ==========")
    logger.info(f"Contact ID: {contact_id}")
    logger.info(f"NS Opportunity ID (target): {opportunity_id}")
    logger.info(f"CF ID used: {CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID}")

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

    logger.info(f"📦 Opportunities found (contact search): {len(opportunities)}")

    for opp in opportunities:

        logger.info("--------------------------------------")
        logger.info(f"Checking Opportunity ID: {opp.get('id')}")
        logger.info(f"Name: {opp.get('name')}")

        custom_fields = opp.get("customFields", [])

        for cf in custom_fields:

            cf_id = cf.get("id")

            # soporta múltiples formatos de GHL
            value = (
                cf.get("fieldValue")
                or cf.get("fieldValueString")
                or cf.get("value")
                or cf.get("field_value")
            )

            logger.info(f"CF {cf_id} = {value}")

            if (
                cf_id == CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
                and str(value) == str(opportunity_id)
            ):
                logger.info("🎯 MATCH FOUND BY NS ID")
                return opp

    logger.warning("❌ No matching opportunity found in contact scope")
    return None


# ===============================
# UPSERT OPPORTUNITY
# ===============================
def sync_opportunity(
    contact_id,
    opportunity_id=None,
    netsuite_opportunity_id=None,
    create_payload=None,
    update_payload_builder=None
):

    if opportunity_id is None:
        opportunity_id = netsuite_opportunity_id

    logger.info("========== OPPORTUNITY SYNC NS → GHL ==========")
    logger.info(f"NS Opportunity ID: {opportunity_id}")

    # ===============================
    # SEARCH
    # ===============================
    matching = find_opportunity(contact_id, opportunity_id)

    # ===============================
    # CREATE
    # ===============================
    if not matching:
        logger.warning("⚠️ No existing opportunity → CREATE")

        resp = create_opportunity(create_payload)

        logger.info("========== GHL CREATE RESPONSE ==========")
        logger.info(f"STATUS: {resp.status_code}")
        logger.info(f"BODY: {resp.text}")

        return {
            "action": "created",
            "status": resp.status_code
        }

    # ===============================
    # UPDATE
    # ===============================
    ghl_id = matching["id"]

    logger.info("========== EXISTING OPPORTUNITY ==========")
    logger.info(f"GHL ID: {ghl_id}")

    payload = update_payload_builder(matching) if update_payload_builder else {}

    current_stage = matching.get("pipelineStageId")
    new_stage = payload.get("pipelineStageId")

    current_status = matching.get("status")
    new_status = payload.get("status")

    if current_stage == new_stage and current_status == new_status:
        logger.info("⏭ IDENTITY MATCH → NO UPDATE REQUIRED")
        return {"status": "already_updated"}

    logger.info("========== FINAL UPDATE ==========")
    logger.info(f"Stage: {current_stage} → {new_stage}")
    logger.info(f"Status: {current_status} → {new_status}")

    resp = update_opportunity(
        opportunity_id=ghl_id,
        pipeline_stage_id=new_stage,
        status=new_status,
        custom_fields=payload.get("customFields", [])
    )

    logger.info("========== GHL UPDATE RESPONSE ==========")
    logger.info(f"STATUS: {resp.status_code}")
    logger.info(f"BODY: {resp.text}")

    return {
        "action": "updated",
        "id": ghl_id,
        "status": resp.status_code
    }


# backward compatibility
upsert_opportunity = sync_opportunity