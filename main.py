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
NETSUITE_OPP_CF_ID = os.getenv("NETSUITE_OPP_CF_ID")  # ID del campo NetSuite

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

def translate_unidad_comercial(value):
    mapping = {
        "1": "Hogar Seguro",
        "2": "Comercio Seguro",
        "3": "Obra Segura"
    }
    return mapping.get(str(value), None)

def prepare_ghl_payload(customer_name, netsuite_opportunity_id, titulo_oportunidad, unidad_comercial):
    return {
        "locationId": LOCATION_ID,
        "pipelineId": PIPELINE_ID,
        "pipelineStageId": PIPELINE_STAGE_ID,
        "contactId": customer_name.get("ghl_contact_id"),
        "name": customer_name.get("nombre"),
        "status": "open",
        "customFields": [
            {"id": NETSUITE_OPP_CF_ID, "field_value": str(netsuite_opportunity_id)},
            {"id": "titulo_oportunidad", "field_value": titulo_oportunidad},
            {"id": "unidad_comercial", "field_value": unidad_comercial},
        ]
    }

def send_to_ghl(payload):
    print("🚀 Creando Opportunity en GHL")
    print(payload)
    response = requests.post(
        f"{GHL_BASE_URL}/opportunities/",
        headers=ghl_headers(),
        json=payload,
        timeout=30
    )
    print("📨 Respuesta GHL:", response.status_code)
    print(response.text)
    return response

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
        return {"status": "error", "message": "ENV incompleto"}

    ghl_contact_id = payload.get("ghl_contact_id")
    netsuite_opportunity_id = payload.get("netsuite_opportunity_id")
    customer_name = payload.get("netsuite_customer_name")
    titulo_oportunidad = payload.get("titulo_oportunidad")
    unidad_comercial_val = payload.get("unidad_comercial")

    if not ghl_contact_id or not customer_name:
        return {"status": "error", "message": "ghl_contact_id o netsuite_customer_name faltante"}

    # -------------------------
    # Traducir unidad comercial
    # -------------------------
    unidad_comercial = translate_unidad_comercial(unidad_comercial_val)
    print(f"🏷 Unidad comercial traducida: {unidad_comercial}")

    # -------------------------
    # Chequear oportunidad existente en GHL
    # -------------------------
    # Esto simula búsqueda: se debería hacer GET a /opportunities con contactId y status=open
    # Para la prueba, asumimos que no hay oportunidad abierta o tiene NS ID
    oportunidad_existente = payload.get("ghl_opportunity_existente")  # opcional para pruebas
    if oportunidad_existente and not oportunidad_existente.get("netsuite_opportunity_id"):
        # Actualizar oportunidad existente
        print("🔄 Actualizando oportunidad abierta existente sin NS ID")
        ghl_payload = prepare_ghl_payload(
            customer_name={"nombre": customer_name, "ghl_contact_id": ghl_contact_id},
            netsuite_opportunity_id=netsuite_opportunity_id,
            titulo_oportunidad=titulo_oportunidad,
            unidad_comercial=unidad_comercial
        )
        # Simulación PATCH o PUT
        response = send_to_ghl(ghl_payload)
    else:
        # Crear nueva oportunidad
        print("✨ Creando nueva oportunidad")
        ghl_payload = prepare_ghl_payload(
            customer_name={"nombre": customer_name, "ghl_contact_id": ghl_contact_id},
            netsuite_opportunity_id=netsuite_opportunity_id,
            titulo_oportunidad=titulo_oportunidad,
            unidad_comercial=unidad_comercial
        )
        response = send_to_ghl(ghl_payload)

    if response.status_code >= 400:
        return {"status": "error", "ghl_status": response.status_code, "ghl_response": response.text}

    return {"status": "ok", "ghl_response": response.json()}