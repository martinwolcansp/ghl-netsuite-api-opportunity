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
NETSUITE_OPP_CF_ID = os.getenv("NETSUITE_OPP_CF_ID")  # campo donde se guarda el ID de NetSuite

GHL_BASE_URL = "https://services.leadconnectorhq.com"

# =========================
# UTILS
# =========================
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

# ------------------------
# Unidad comercial mapping
# ------------------------
UNIDAD_MAP = {
    "1": "Hogar Seguro",
    "2": "Comercio Seguro",
    "3": "Obra Segura"
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

    required_envs = [GHL_API_KEY, LOCATION_ID, PIPELINE_ID, PIPELINE_STAGE_ID, NETSUITE_OPP_CF_ID]
    if not all(required_envs):
        print("❌ Variables de entorno incompletas")
        return {"status": "error", "message": "ENV incompleto"}

    ghl_contact_id = payload.get("ghl_contact_id")
    netsuite_opportunity_id = payload.get("netsuite_opportunity_id")
    customer_name = payload.get("netsuite_customer_name")
    titulo_oportunidad = payload.get("titulo_oportunidad")
    unidad_comercial_val = payload.get("unidad_comercial")
    unidad_comercial = UNIDAD_MAP.get(str(unidad_comercial_val), "Otro")

    if not ghl_contact_id or not customer_name:
        print("❌ Datos mínimos faltantes")
        return {"status": "error", "message": "ghl_contact_id o customer_name requerido"}

    print("🏷 Unidad comercial traducida:", unidad_comercial)

    # =========================
    # Buscar oportunidades abiertas del contacto
    # =========================
    search_body = {
        "filters": [
            {"field": "contactId", "operator": "equals", "value": ghl_contact_id},
            {"field": "status", "operator": "equals", "value": "open"}
        ],
        "location_id": LOCATION_ID,
        "pipeline_id": PIPELINE_ID
    }

    try:
        search_resp = requests.post(
            f"{GHL_BASE_URL}/opportunities/search",
            headers=ghl_headers(),
            json=search_body,
            timeout=30
        )
        print("🔍 Search status:", search_resp.status_code)
        search_data = search_resp.json()
        print("🔍 Search response:", search_data)

    except Exception as e:
        print("❌ Error al buscar oportunidades en GHL", str(e))
        search_data = None

    # =========================
    # Determinar acción: crear o actualizar
    # =========================
    update_opportunity_id = None
    if search_data and search_resp.status_code == 200 and search_data.get("opportunities"):
        for opp in search_data["opportunities"]:
            # Solo actualizar si el campo NetSuite ID está vacío
            opp_custom_fields = {cf["id"]: cf["fieldValue"] for cf in opp.get("customFields", [])}
            if not opp_custom_fields.get(NETSUITE_OPP_CF_ID):
                update_opportunity_id = opp["id"]
                print("✨ Oportunidad abierta encontrada para actualizar:", update_opportunity_id)
                break

    # Payload GHL
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
            {"id": "unidad_comercial", "field_value": unidad_comercial}
        ]
    }

    if update_opportunity_id:
        print("🚀 Actualizando oportunidad existente en GHL")
        resp = requests.put(
            f"{GHL_BASE_URL}/opportunities/{update_opportunity_id}",
            headers=ghl_headers(),
            json=ghl_payload,
            timeout=30
        )
    else:
        print("✨ Creando nueva oportunidad")
        resp = requests.post(
            f"{GHL_BASE_URL}/opportunities/",
            headers=ghl_headers(),
            json=ghl_payload,
            timeout=30
        )

    print("📨 Respuesta GHL:", resp.status_code)
    print(resp.text)

    return {"status": "ok", "ghl_response": resp.json() if resp.status_code < 400 else resp.text}