from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook/opportunity")
async def receive_opportunity(request: Request):
    payload = await request.json()

    print("🔥 Webhook recibido desde NetSuite")
    print(payload)

    ghl_payload = {
        "contactId": payload.get("ghl_contact_id"),
        "name": payload.get("netsuite_title"),
        "pipelineId": "PIPELINE_ID",
        "stageId": "STAGE_ID",
        "status": "open"
    }

    print("🚀 Payload a enviar a GHL")
    print(ghl_payload)

    return {"status": "ok"}
