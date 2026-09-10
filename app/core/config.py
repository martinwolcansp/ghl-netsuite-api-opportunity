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

# =========================
# SUPABASE (prueba piloto — sincronización Oportunidad → GHL)
# =========================
# Se usa la anon key + el access token del usuario logueado en la web
# interna (reenviado en el Authorization header), NUNCA una service_role
# key acá: la autorización real la dan las políticas RLS de
# integracion-ghl-ns sobre las tablas contacto/oportunidad.
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# =========================
# CORS (para que la web interna pueda llamar a este servicio desde el navegador)
# =========================
# Lista separada por comas, ej: "https://interna.spseguridad.com.ar,https://otra.com"
# Si queda vacía, se permite cualquier origen (útil mientras la web interna
# todavía no tiene un dominio de producción fijo) — restringir apenas se
# tenga el dominio definitivo.
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
