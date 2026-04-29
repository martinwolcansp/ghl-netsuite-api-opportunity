# app/main.py

from fastapi import FastAPI
from app.webhooks.opportunity_webhook import router as opportunity_router

app = FastAPI()

app.include_router(opportunity_router)