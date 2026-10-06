"""Cliente mínimo de la API de Buttondown para crear un email como borrador.

Solo sabe hacer una cosa: crear un borrador (`status: "draft"`). Nunca
envía nada — enviar el email de verdad es una acción manual del usuario
desde Buttondown (sección 2.3 de CLAUDE.md: "revisión humana obligatoria").
"""

from __future__ import annotations

import logging
import os

import requests

log = logging.getLogger(__name__)

BASE_URL = "https://api.buttondown.com/v1/emails"
TIMEOUT_SEGUNDOS = 20

# Fuerza el modo Markdown explícitamente en vez de confiar en la
# autodetección de Buttondown (que busca etiquetas HTML o sintaxis
# Markdown en el cuerpo): así el comportamiento no depende de que
# informe.md siempre tenga encabezados u otra marca reconocible.
_CABECERA_MODO_MARKDOWN = "<!-- buttondown-editor-mode: plaintext -->\n"


class ButtondownApiKeyFaltante(RuntimeError):
    """No se encontró la variable de entorno BUTTONDOWN_API_KEY."""


class ErrorButtondown(RuntimeError):
    """La API de Buttondown respondió con un error."""


def _clave_api() -> str:
    clave = os.environ.get("BUTTONDOWN_API_KEY")
    if not clave:
        raise ButtondownApiKeyFaltante("Falta la variable de entorno BUTTONDOWN_API_KEY")
    return clave


def crear_borrador(subject: str, body: str) -> dict:
    """Crea un email en Buttondown con status="draft". Nunca lo envía.

    Devuelve el JSON de la respuesta de la API (incluye su "id").
    """
    log.info("Creando borrador en Buttondown: %s", subject)
    respuesta = requests.post(
        BASE_URL,
        json={
            "subject": subject,
            "body": _CABECERA_MODO_MARKDOWN + body,
            "status": "draft",
        },
        headers={"Authorization": f"Token {_clave_api()}"},
        timeout=TIMEOUT_SEGUNDOS,
    )
    if respuesta.status_code >= 400:
        raise ErrorButtondown(f"Buttondown devolvió HTTP {respuesta.status_code}: {respuesta.text}")
    return respuesta.json()
