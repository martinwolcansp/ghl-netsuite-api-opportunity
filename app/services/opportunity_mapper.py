# app/services/opportunity_mapper.py

def map_unidad_comercial(valor):
    # Campo "Unidad comercial" de la oportunidad en NetSuite
    # (custbodycustbody_mw_sp_unidad_comercia). Hoy sólo se carga en
    # alarmas nuevas. No confundir con la unidad de negocio (class).
    mapping = {
        "1": "Hogar Seguro",
        "2": "Comercio Seguro",
        "3": "Obra Segura",
        "8": "Gubernamental"
    }
    return mapping.get(str(valor), "Otro")


# ===============================
# BUILD NAME (UNIFICADO)
# ===============================
def build_opportunity_name(customer_name, titulo):
    name = customer_name or ""

    if titulo:
        name = f"{name} - {titulo}"

    return name


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
    name = build_opportunity_name(customer_name, titulo_oportunidad)

    return {
        "locationId": location_id,
        "pipelineId": pipeline_id,
        "pipelineStageId": pipeline_stage_id,
        "contactId": contact_id,
        "name": name,
        "status": "open",
        # Los campos personalizados se identifican por "id" (ID interno de
        # GHL, como el de NetSuite que viene de la variable de entorno) o por
        # "key" (la clave del campo). "titulo_oportunidad" y
        # "unidad_comercial_ns" son claves, no IDs: antes iban en "id" y GHL
        # los ignoraba sin dar error.
        "customFields": [
            {
                "id": custom_field_ns_id,
                "field_value": str(netsuite_opportunity_id)
            },
            {
                "key": "titulo_oportunidad",
                "field_value": titulo_oportunidad
            },
            {
                "key": "unidad_comercial_ns",
                "field_value": unidad_comercial
            }
        ]
    }


def build_update_payload(
    existing,
    customer_name,
    titulo_oportunidad,
    unidad_comercial
):
    # Actualiza sólo nombre y datos informativos. NO toca la etapa ni el
    # estado: los maneja la integración de presupuestos, y reenviar la
    # oportunidad no debe devolverla a la etapa inicial.
    name = build_opportunity_name(customer_name, titulo_oportunidad)

    return {
        "name": name,
        "customFields": [
            {
                "key": "titulo_oportunidad",
                "field_value": titulo_oportunidad
            },
            {
                "key": "unidad_comercial_ns",
                "field_value": unidad_comercial
            }
        ]
    }