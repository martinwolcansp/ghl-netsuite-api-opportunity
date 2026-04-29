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

    contact_id = payload.get("ghl_contact_id")
    ns_id = payload.get("netsuite_opportunity_id")

    if not contact_id or not ns_id:
        raise HTTPException(status_code=400, detail="Missing data")

    unidad = map_unidad_comercial(payload.get("unidad_comercial"))

    create_payload = build_create_payload(
        location_id=GHL_LOCATION_ID,
        pipeline_id=PIPELINE_ID,
        pipeline_stage_id=PIPELINE_STAGE_ID,
        contact_id=contact_id,
        customer_name=payload.get("netsuite_customer_name"),
        netsuite_opportunity_id=ns_id,
        titulo_oportunidad=payload.get("titulo_oportunidad"),
        unidad_comercial=unidad,
        custom_field_ns_id=CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
    )

    return sync_opportunity(
        contact_id=contact_id,
        opportunity_id=ns_id,
        create_payload=create_payload,
        update_payload_builder=lambda existing: build_update_payload(
            existing,
            payload.get("netsuite_customer_name"),
            PIPELINE_STAGE_ID,
            payload.get("titulo_oportunidad"),
            unidad
        )
    )