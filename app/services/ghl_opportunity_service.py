#services/ghl_opportunity_service.py
import logging

from app.services.ghl_client import (
    search_opportunities,
    create_opportunity,
    update_opportunity
)

from app.core.config import (
    GHL_LOCATION_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
)

logger = logging.getLogger("ghl_opportunity_service")


# ===============================
# FIND BY NETSUITE ID (MISMA LÓGICA QUE ESTIMATES)
# ===============================
def find_opportunity_by_ns_id(contact_id, netsuite_opportunity_id):

    resp = search_opportunities(GHL_LOCATION_ID, contact_id)

    if resp.status_code not in (200, 201):
        logger.error(f"GHL search error: {resp.text}")
        return None

    opportunities = resp.json().get("opportunities", [])

    for opp in opportunities:
        for cf in opp.get("customFields", []):
            value = cf.get("fieldValue") or cf.get("fieldValueString")

            if (
                cf.get("id") == CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
                and str(value) == str(netsuite_opportunity_id)
            ):
                return opp

    return None


# ===============================
# UPSERT
# ===============================
def upsert_opportunity(
    contact_id,
    netsuite_opportunity_id,
    create_payload,
    update_payload_builder
):

    logger.info("===== UPSERT OPPORTUNITY =====")

    existing = find_opportunity_by_ns_id(
        contact_id,
        netsuite_opportunity_id
    )

    # -------------------------
    # UPDATE
    # -------------------------
    if existing:
        ghl_id = existing["id"]
        logger.info(f"Updating opportunity: {ghl_id}")

        payload = update_payload_builder(existing)

        resp = update_opportunity(ghl_id, payload)

        logger.info(f"GHL UPDATE RESPONSE: {resp.status_code}")

        return {
            "action": "updated",
            "id": ghl_id,
            "status": resp.status_code
        }

    # -------------------------
    # CREATE
    # -------------------------
    else:
        logger.info("Creating opportunity")

        resp = create_opportunity(create_payload)

        logger.info(f"GHL CREATE RESPONSE: {resp.status_code}")

        return {
            "action": "created",
            "status": resp.status_code
        }