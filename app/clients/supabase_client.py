# app/clients/supabase_client.py
#
# Cliente mínimo de Supabase (PostgREST) para la prueba piloto de
# sincronización Oportunidad → GHL. A propósito NO usa una service_role
# key: reenvía el access token del usuario que hizo el pedido desde la
# web interna, así las políticas RLS de integracion-ghl-ns (ver/editar)
# son las que deciden qué puede leer o modificar cada uno. Este servicio
# nunca ve ni guarda una service key de Supabase.

import logging
import requests

from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY

logger = logging.getLogger("supabase_client")


def _headers(user_token):
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def get_oportunidad_con_contacto(oportunidad_id, user_token):
    """
    Trae la oportunidad junto con su contacto (embed de PostgREST).
    Si el usuario no tiene permiso 'ver'/'editar' sobre
    integracion-ghl-ns, RLS hace que PostgREST devuelva 0 filas — igual
    que si la oportunidad no existiera (comportamiento estándar de RLS,
    no un caso especial que haya que manejar distinto).

    Devuelve (fila_o_None, response_cruda_de_requests).
    """
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidad",
        headers=_headers(user_token),
        params={
            "id": f"eq.{oportunidad_id}",
            "select": "*,contacto(*)",
        },
        timeout=15,
    )

    if resp.status_code != 200:
        logger.error(f"Supabase GET oportunidad error: {resp.status_code} {resp.text}")
        return None, resp

    rows = resp.json()
    if not rows:
        return None, resp

    return rows[0], resp


def actualizar_sync_oportunidad(oportunidad_id, user_token, cambios):
    """
    PATCH parcial sobre la oportunidad (sync_estado, sync_mensaje,
    ghl_opportunity_id, fecha_creacion_ghl, sync_actualizado_en, etc.).
    Misma lógica de autorización que el GET: la política "editar" de RLS
    decide si el PATCH tiene efecto.
    """
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/oportunidad",
        headers={**_headers(user_token), "Prefer": "return=representation"},
        params={"id": f"eq.{oportunidad_id}"},
        json=cambios,
        timeout=15,
    )

    if resp.status_code not in (200, 204):
        logger.error(f"Supabase PATCH oportunidad error: {resp.status_code} {resp.text}")

    return resp
