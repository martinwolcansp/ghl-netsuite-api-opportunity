# app/core/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# GHL CORE
# =========================
GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("LOCATION_ID")

PIPELINE_ID = os.getenv("PIPELINE_ID")
PIPELINE_STAGE_ID = os.getenv("PIPELINE_STAGE_ID")

# =========================
# CUSTOM FIELDS
# =========================
CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID = os.getenv("CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID")