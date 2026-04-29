# app/services/opportunity_mapper.py

def map_unidad_comercial(valor):
    mapping = {
        "1": "Hogar Seguro",
        "2": "Comercio Seguro",
        "3": "Obra Segura"
    }
    return mapping.get(str(valor), "Otro")


def build_create_payload(
    location_id,
    pipeline_id,
    pipeline_stage_id,
    contact_id,
    customer_name,
    netsuite_opportunity_id,
    titulo_oportunidad,
    unidad_comercial,
    custom_field_ns_id
):
    return {
        "locationId": location_id,
        "pipelineId": pipeline_id,
        "pipelineStageId": pipeline_stage_id,
        "contactId": contact_id,
        "name": customer_name,
        "status": "open",
        "customFields": [
            {
                "id": custom_field_ns_id,
                "field_value": str(netsuite_opportunity_id)
            },
            {
                "id": "titulo_oportunidad",
                "field_value": titulo_oportunidad
            },
            {
                "id": "unidad_comercial_ns",
                "field_value": unidad_comercial
            }
        ]
    }


def build_update_payload(
    existing,
    customer_name,
    pipeline_stage_id,
    titulo_oportunidad,
    unidad_comercial
):
    return {
        "name": customer_name,
        "pipelineStageId": pipeline_stage_id,
        "customFields": [
            {
                "id": "titulo_oportunidad",
                "field_value": titulo_oportunidad
            },
            {
                "id": "unidad_comercial_ns",
                "field_value": unidad_comercial
            }
        ]
    }