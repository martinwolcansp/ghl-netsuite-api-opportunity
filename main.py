import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# =========================
# ENV
# =========================
GHL_API_KEY = os.getenv("GHL_API_KEY")
LOCATION_ID = os.getenv("LOCATION_ID")
PIPELINE_ID = os.getenv("PIPELINE_ID")
PIPELINE_STAGE_ID = os.getenv("PIPELINE_STAGE_ID")
NETSUITE_OPP_CF_ID = os.getenv("NETSUITE_OPP_CF_ID")  # ID del campo donde se guarda el ID de NetSuite

GHL_BASE_URL = "https://services.leadconnectorhq.com"

# =========================
# UTILIDADES
# =========================
UNIDAD_COMERCIAL_MAP = {
    "1": "Hogar Seguro",
    "2": "Comercio Seguro",
    "3": "Obra Segura"
}

def env_check():
    return {
        "GHL_API_KEY": bool(GHL_API_KEY),
        "LOCATION_ID": LOCATION_ID,
        "PIPELINE_ID": PIPELINE_ID,
        "PIPELINE_STAGE_ID": PIPELINE_STAGE_ID,
        "NETSUITE_OPP_CF_ID": NETSUITE_OPP_CF_ID
    }

def ghl_headers():
    return {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }

# =========================
# WEBHOOK
# =========================
@app.post("/webhook/opportunity")
async def webhook_opportunity(request: Request):
    payload = await request.json()
    print("🔥 Webhook recibido desde NetSuite")
    print(payload)

    print("🧪 ENV CHECK", env_check())

    # Validaciones mínimas
    required_envs = [GHL_API_KEY, LOCATION_ID, PIPELINE_ID, PIPELINE_STAGE_ID, NETSUITE_OPP_CF_ID]
    if not all(required_envs):
        print("❌ Variables de entorno incompletas")
        return {"status": "error", "message": "ENV incompleto"}

    ghl_contact_id = payload.get("ghl_contact_id")
    netsuite_opportunity_id = payload.get("netsuite_opportunity_id")
    customer_name = payload.get("netsuite_customer_name")
    titulo_oportunidad = payload.get("titulo_oportunidad")
    unidad_comercial = payload.get("unidad_comercial")

    if not ghl_contact_id:
        return {"status": "error", "message": "ghl_contact_id requerido"}
    if not customer_name:
        return {"status": "error", "message": "netsuite_customer_name requerido"}

    # Traducir unidad comercial
    unidad_comercial_label = UNIDAD_COMERCIAL_MAP.get(str(unidad_comercial), "Sin asignar")
    print(f"🏷 Unidad comercial traducida: {unidad_comercial_label}")

    # -------------------------
    # Buscar oportunidades abiertas del contacto
    # -------------------------
    search_resp = requests.get(
        f"{GHL_BASE_URL}/opportunities/",
        headers=ghl_headers(),
        params={
            "contactId": ghl_contact_id,
            "status": "open"
        },
        timeout=30
    )

    if search_resp.status_code >= 400:
        print("❌ Error al buscar oportunidades en GHL")
        return {"status": "error", "ghl_search_status": search_resp.status_code, "ghl_search_response": search_resp.text}

    open_opps = search_resp.json().get("opportunities", [])
    opp_to_update = None

    for opp in open_opps:
        custom_fields = {cf["id"]: cf.get("fieldValue") for cf in opp.get("customFields", [])}
        if not custom_fields.get(NETSUITE_OPP_CF_ID):
            opp_to_update = opp
            break

    if opp_to_update:
        print("✨ Actualizando oportunidad existente")
        opp_id = opp_to_update["id"]
        ghl_payload = {
            "pipelineId": PIPELINE_ID,
            "pipelineStageId": PIPELINE_STAGE_ID,
            "customFields": [
                {"id": NETSUITE_OPP_CF_ID, "field_value": str(netsuite_opportunity_id)},
                {"id": "titulo_oportunidad", "field_value": titulo_oportunidad},
                {"id": "unidad_comercial", "field_value": unidad_comercial_label}
            ]
        }

        update_resp = requests.put(
            f"{GHL_BASE_URL}/opportunities/{opp_id}",
            headers=ghl_headers(),
            json=ghl_payload,
            timeout=30
        )

        print("📨 Respuesta actualización GHL:", update_resp.status_code)
        print(update_resp.text)

        if update_resp.status_code >= 400:
            return {"status": "error", "ghl_update_status": update_resp.status_code, "ghl_update_response": update_resp.text}

        return {"status": "ok", "action": "update", "ghl_response": update_resp.json()}

    else:
        print("✨ Creando nueva oportunidad")
        ghl_payload = {
            "locationId": LOCATION_ID,
            "pipelineId": PIPELINE_ID,
            "pipelineStageId": PIPELINE_STAGE_ID,
            "contactId": ghl_contact_id,
            "name": customer_name,
            "status": "open",
            "customFields": [
                {"id": NETSUITE_OPP_CF_ID, "field_value": str(netsuite_opportunity_id)},
                {"id": "titulo_oportunidad", "field_value": titulo_oportunidad},
                {"id": "unidad_comercial", "field_value": unidad_comercial_label}
            ]
        }

        create_resp = requests.post(
            f"{GHL_BASE_URL}/opportunities/",
            headers=ghl_headers(),
            json=ghl_payload,
            timeout=30
        )

        print("📨 Respuesta creación GHL:", create_resp.status_code)
        print(create_resp.text)

        if create_resp.status_code >= 400:
            return {"status": "error", "ghl_create_status": create_resp.status_code, "ghl_create_response": create_resp.text}

        return {"status": "ok", "action": "create", "ghl_response": create_resp.json()}