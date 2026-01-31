from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

GHL_API_KEY = os.getenv("GHL_API_KEY")

PIPELINE_ID = "61MQv4xKuvTQesby42pC"
STAGE_ID = "71989c58-aeee-4c5a-bfc6-02997375065b"

@app.post("/webhook/opportunity")
async def receive_opportunity(request: Request):
    payload = await request.json()

    print("🔥 Webhook recibido desde NetSuite")
    print(payload)

    ghl_payload = {
        "contactId": payload.get("ghl_contact_id"),
        "name": payload.get("netsuite_title"),
        "pipelineId": PIPELINE_ID,
        "stageId": STAGE_ID,
        "status": "open"
    }

    print("🚀 Enviando Opportunity a GHL")
    print(ghl_payload)

    response = requests.post(
        "https://services.leadconnectorhq.com/opportunities/",
        headers={
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        },
        json=ghl_payload,
        timeout=10
    )

    print("📨 Respuesta GHL:", response.status_code)
    print(response.text)

    return {
        "status": "ok",
        "ghl_response_status": response.status_code
    }

