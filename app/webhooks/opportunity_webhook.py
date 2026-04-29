# app/webhooks/opportunity_webhook.py

from fastapi import APIRouter, Request

from app.services.ghl_opportunity_service import sync_opportunity
from app.services.opportunity_mapper import (
    build_create_payload,
    build_update_payload,
    map_unidad_comercial
)

from app.core.config import (
    GHL_LOCATION_ID,
    PIPELINE_ID,
    PIPELINE_STAGE_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
)

router = APIRouter()


@router.post("/webhook/opportunity")
async def opportunity_webhook(request: Request):

    payload = await request.json()

    # ===============================
    # EXTRACT PAYLOAD
    # ===============================
    contact_id = payload.get("ghl_contact_id")
    opportunity_id = payload.get("netsuite_opportunity_id")
    customer_name = payload.get("netsuite_customer_name")
    titulo = payload.get("titulo_oportunidad")

    unidad = map_unidad_comercial(payload.get("unidad_comercial"))

    # ===============================
    # BASIC VALIDATION (EVITA 500 SILENCIOSOS)
    # ===============================
    if not contact_id or not opportunity_id:
        return {
            "status": "error",
            "message": "missing contact_id or netsuite_opportunity_id"
        }

    # ===============================
    # CREATE PAYLOAD
    # ===============================
    create_payload = build_create_payload(
        location_id=GHL_LOCATION_ID,
        pipeline_id=PIPELINE_ID,
        pipeline_stage_id=PIPELINE_STAGE_ID,
        contact_id=contact_id,
        customer_name=customer_name,
        netsuite_opportunity_id=opportunity_id,
        titulo_oportunidad=titulo,
        unidad_comercial=unidad,
        custom_field_ns_id=CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
    )

    # ===============================
    # UPSERT CALL (FIXED)
    # ===============================
    return sync_opportunity(
        contact_id=contact_id,
        opportunity_id=opportunity_id,  # 👈 FIX CRÍTICO (ANTES ERA ns_id mismatch)
        status=None,
        stage_id=PIPELINE_STAGE_ID,
        update_payload_builder=lambda existing: build_update_payload(
            existing,
            customer_name,
            PIPELINE_STAGE_ID,
            titulo,
            unidad
        )
    )