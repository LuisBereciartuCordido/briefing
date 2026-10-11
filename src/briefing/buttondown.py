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


class ErrorButtondown(RuntimeError):
    """La API de Buttondown respondió con un error."""


def _cabeceras() -> dict[str, str]:
    """Cabecera de autenticación, solo si BUTTONDOWN_API_KEY es una variable
    de entorno real legible.

    En local (`.env`) sí lo es. En la Routine, `BUTTONDOWN_API_KEY` está
    configurada como **API credential** del *environment* (sección 3 de
    CLAUDE.md), no como variable de entorno: ahí el secreto no es legible
    por este código a propósito — es el propio proxy de red de la Routine
    quien añade la cabecera `Authorization` a las peticiones hacia
    api.buttondown.com. Intentar leer la variable y fallar si no está
    (como hacía antes esta función) rompía justo ese caso real: la
    primera ejecución real de la Routine (2026-S41) dio 401 porque el
    código mandaba una petición sin autenticar, en vez de dejar que el
    proxy la completara. Si de verdad no hay credential configurada en
    ningún sitio, Buttondown devuelve 401 igualmente y eso ya lo convierte
    ErrorButtondown en un fallo explícito más abajo.
    """
    clave = os.environ.get("BUTTONDOWN_API_KEY")
    return {"Authorization": f"Token {clave}"} if clave else {}


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
        headers=_cabeceras(),
        timeout=TIMEOUT_SEGUNDOS,
    )
    if respuesta.status_code >= 400:
        raise ErrorButtondown(f"Buttondown devolvió HTTP {respuesta.status_code}: {respuesta.text}")
    return respuesta.json()
