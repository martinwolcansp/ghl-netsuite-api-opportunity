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
NETSUITE_OPP_CF_ID = os.getenv("NETSUITE_OPP_CF_ID")  # campo NetSuite ID

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

def translate_unidad_comercial(valor):
    mapping = {"1": "Hogar Seguro", "2": "Comercio Seguro", "3": "Obra Segura"}
    return mapping.get(str(valor), "Otro")

# =========================
# WEBHOOK
# =========================
@app.post("/webhook/opportunity")
async def webhook_opportunity(request: Request):
    payload = await request.json()
    print("🔥 Webhook recibido desde NetSuite")
    print(payload)
    print("🧪 ENV CHECK", env_check())

    # -------------------------
    # Validaciones mínimas
    # -------------------------
    required_envs = [
        GHL_API_KEY,
        LOCATION_ID,
        PIPELINE_ID,
        PIPELINE_STAGE_ID,
        NETSUITE_OPP_CF_ID
    ]
    if not all(required_envs):
        return {"status": "error", "message": "ENV incompleto"}

    ghl_contact_id = payload.get("ghl_contact_id")
    netsuite_opportunity_id = payload.get("netsuite_opportunity_id")
    customer_name = payload.get("netsuite_customer_name")
    titulo_oportunidad = payload.get("titulo_oportunidad")
    unidad_comercial = translate_unidad_comercial(payload.get("unidad_comercial"))

    if not ghl_contact_id or not customer_name:
        return {"status": "error", "message": "ghl_contact_id y customer_name requeridos"}

    # =========================
    # 1️⃣ Buscar oportunidades abiertas
    # =========================
    search_params = {
        "contact_id": ghl_contact_id,
        "status": "open",
        "location_id": LOCATION_ID,
        "limit": 50  # por si hay muchas
    }
    try:
        resp = requests.get(
            f"{GHL_BASE_URL}/opportunities/search",
            headers=ghl_headers(),
            params=search_params,
            timeout=30
        )
        resp.raise_for_status()
        opportunities = resp.json().get("opportunities", [])
        print(f"🔍 Oportunidades abiertas encontradas: {len(opportunities)}")
    except Exception as e:
        print("❌ Error al buscar oportunidades en GHL")
        print(e)
        opportunities = []

    # Filtrar oportunidades sin NetSuite Opportunity ID
    open_without_ns_id = [
        opp for opp in opportunities
        if not any(
            cf.get("id") == NETSUITE_OPP_CF_ID and cf.get("fieldValue")
            for cf in opp.get("customFields", [])
        )
    ]

    if open_without_ns_id:
        # =========================
        # 2️⃣ Actualizar oportunidad existente
        # =========================
        opp_to_update = open_without_ns_id[0]  # tomamos la primera
        opp_id = opp_to_update.get("id")
        print(f"✨ Actualizando oportunidad existente: {opp_id}")

        ghl_payload = {
            "pipelineId": PIPELINE_ID,
            "pipelineStageId": PIPELINE_STAGE_ID,
            "customFields": [
                {"id": NETSUITE_OPP_CF_ID, "field_value": str(netsuite_opportunity_id)},
                {"id": "titulo_oportunidad", "field_value": titulo_oportunidad},
                {"id": "unidad_comercial_ns", "field_value": unidad_comercial}
            ]
        }

        update_resp = requests.put(
            f"{GHL_BASE_URL}/opportunities/{opp_id}",
            headers=ghl_headers(),
            json=ghl_payload,
            timeout=30
        )
        print("🚀 Respuesta actualización GHL:", update_resp.status_code)
        print(update_resp.text)
        return {"status": "ok", "action": "updated", "ghl_response": update_resp.json()}

    else:
        # =========================
        # 3️⃣ Crear nueva oportunidad
        # =========================
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
                {"id": "unidad_comercial_ns", "field_value": unidad_comercial}
            ]
        }

        create_resp = requests.post(
            f"{GHL_BASE_URL}/opportunities/",
            headers=ghl_headers(),
            json=ghl_payload,
            timeout=30
        )
        print("🚀 Respuesta GHL:", create_resp.status_code)
        print(create_resp.text)
        return {"status": "ok", "action": "created", "ghl_response": create_resp.json()}