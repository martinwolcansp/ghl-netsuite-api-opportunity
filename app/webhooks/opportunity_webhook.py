# app/webhooks/opportunity_webhook.py

from fastapi import APIRouter, Request, HTTPException

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
    # EXTRACT DATA
    # ===============================
    contact_id = payload.get("ghl_contact_id")
    ns_id = payload.get("netsuite_opportunity_id")
    customer_name = payload.get("netsuite_customer_name")
    titulo = payload.get("titulo_oportunidad")
    unidad = map_unidad_comercial(payload.get("unidad_comercial"))

    # ===============================
    # VALIDATION (CRÍTICO)
    # ===============================
    if not contact_id:
        raise HTTPException(
            status_code=400,
            detail="Missing ghl_contact_id"
        )

    if not ns_id:
        raise HTTPException(
            status_code=400,
            detail="Missing netsuite_opportunity_id"
        )

    # ===============================
    # CREATE PAYLOAD
    # ===============================
    create_payload = build_create_payload(
        location_id=GHL_LOCATION_ID,
        pipeline_id=PIPELINE_ID,
        pipeline_stage_id=PIPELINE_STAGE_ID,
        contact_id=contact_id,
        customer_name=customer_name,
        netsuite_opportunity_id=ns_id,
        titulo_oportunidad=titulo,
        unidad_comercial=unidad,
        custom_field_ns_id=CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
    )

    # ===============================
    # UPSERT OPERATION
    # ===============================
    return sync_opportunity(
        contact_id=contact_id,
        opportunity_id=ns_id,  # 👈 normalizado (IMPORTANTE)
        create_payload=create_payload,
        update_payload_builder=lambda existing: build_update_payload(
            existing,
            customer_name,
            PIPELINE_STAGE_ID,
            titulo,
            unidad
        )
    )