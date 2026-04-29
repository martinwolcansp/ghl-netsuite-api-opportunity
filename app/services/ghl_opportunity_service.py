# app/services/ghl_opportunity_service.py

import logging

from app.clients.ghl_client import search_opportunities
from app.core.config import (
    GHL_LOCATION_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
)

logger = logging.getLogger("ghl_opportunity_service")


# ===============================
# FIND BY NETSUITE OPPORTUNITY ID (DEBUG VERSION)
# ===============================
def find_opportunity_by_ns_id(contact_id, netsuite_opportunity_id):

    logger.info("======================================")
    logger.info("🔍 OPPORTUNITY SEARCH (NETSUITE MATCH)")
    logger.info("======================================")
    logger.info(f"Contact ID: {contact_id}")
    logger.info(f"NS Opportunity ID (input): {netsuite_opportunity_id}")

    resp = search_opportunities(GHL_LOCATION_ID, contact_id)

    logger.info(f"📡 GHL response status: {resp.status_code}")

    if resp.status_code not in (200, 201):
        logger.error(f"❌ GHL API ERROR: {resp.text}")
        return None

    data = resp.json()
    opportunities = data.get("opportunities", [])

    logger.info(f"📦 Opportunities returned: {len(opportunities)}")

    if not opportunities:
        logger.warning("⚠️ No opportunities found for contact")
        return None

    # ===============================
    # LOOP THROUGH OPPORTUNITIES
    # ===============================
    for i, opp in enumerate(opportunities):

        opp_id = opp.get("id")
        opp_name = opp.get("name")

        logger.info("--------------------------------------")
        logger.info(f"📌 Opportunity #{i}")
        logger.info(f"ID: {opp_id}")
        logger.info(f"Name: {opp_name}")

        custom_fields = opp.get("customFields", [])

        logger.info(f"🧩 Custom fields count: {len(custom_fields)}")

        if not custom_fields:
            logger.warning("⚠️ No custom fields in this opportunity")
            continue

        matched_value = None

        # ===============================
        # LOOP CUSTOM FIELDS
        # ===============================
        for cf in custom_fields:

            cf_id = cf.get("id")

            value = (
                cf.get("fieldValue")
                or cf.get("fieldValueString")
                or cf.get("value")
            )

            logger.info(f"   - CF ID: {cf_id} | VALUE: {value}")

            if cf_id == CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID:
                matched_value = value
                logger.info(f"🎯 MATCHED CUSTOM FIELD → value: {value}")

        # ===============================
        # FINAL COMPARISON
        # ===============================
        if matched_value is not None:

            logger.info(f"🔎 Comparing:")
            logger.info(f"   - GHL value: {matched_value}")
            logger.info(f"   - NS value : {netsuite_opportunity_id}")

            if str(matched_value).strip() == str(netsuite_opportunity_id).strip():

                logger.info("✅ MATCH FOUND!")
                logger.info(f"👉 Returning opportunity ID: {opp_id}")

                return opp

            else:
                logger.info("❌ Value mismatch (same field, different value)")

        else:
            logger.info("❌ Custom field not found in this opportunity")

    logger.warning("🚨 NO MATCH FOUND FOR NETSUITE OPPORTUNITY ID")
    return None


# ===============================
# UPSERT OPPORTUNITY (LOGGED)
# ===============================
def upsert_opportunity(
    contact_id,
    netsuite_opportunity_id,
    create_payload,
    update_payload_builder
):

    logger.info("======================================")
    logger.info("🚀 OPPORTUNITY UPSERT START")
    logger.info("======================================")

    logger.info(f"Contact ID: {contact_id}")
    logger.info(f"NS Opportunity ID: {netsuite_opportunity_id}")

    existing = find_opportunity_by_ns_id(
        contact_id,
        netsuite_opportunity_id
    )

    # ===============================
    # UPDATE PATH
    # ===============================
    if existing:

        ghl_id = existing["id"]

        logger.info("======================================")
        logger.info("✏️ UPDATE PATH TRIGGERED")
        logger.info("======================================")
        logger.info(f"Existing GHL ID: {ghl_id}")

        payload = update_payload_builder(existing)

        logger.info("📤 Sending UPDATE request to GHL...")

        from app.clients.ghl_client import update_opportunity
        resp = update_opportunity(ghl_id, payload)

        logger.info(f"📡 Update response status: {resp.status_code}")
        logger.info(f"📡 Response body: {resp.text}")

        return {
            "action": "updated",
            "id": ghl_id,
            "status": resp.status_code
        }

    # ===============================
    # CREATE PATH
    # ===============================
    logger.info("======================================")
    logger.info("🆕 CREATE PATH TRIGGERED")
    logger.info("======================================")

    logger.warning("No matching opportunity found → creating new one")

    from app.clients.ghl_client import create_opportunity
    resp = create_opportunity(create_payload)

    logger.info(f"📡 Create response status: {resp.status_code}")
    logger.info(f"📡 Response body: {resp.text}")

    return {
        "action": "created",
        "status": resp.status_code
    }