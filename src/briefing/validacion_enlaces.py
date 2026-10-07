"""Comprobación de enlaces caídos de informe.json (sección 10 de CLAUDE.md).

Separado de validacion.py porque hace peticiones HTTP reales: así el resto
de comprobaciones se pueden testear sin red, y esta se puede desactivar
sola (--sin-comprobar-enlaces en scripts/validate.py) para iterar rápido
en local.
"""

from __future__ import annotations

import logging

import requests

from briefing.modelos import todas_las_noticias

log = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 10
INTENTOS = 2

# Deliberadamente sin cabecera "User-Agent" propia (sección 6: se
# comprobó en vivo que un valor como "Mozilla/5.0" —ni un navegador real
# ni el user-agent por defecto de requests— hace que algunos CDN (p. ej.
# fred.stlouisfed.org) dejen la conexión colgada en vez de responder,
# y eso se ve como un enlace roto sin serlo. El user-agent por defecto de
# requests llega bien a esos sitios; si otro sitio lo bloquea, ya lo
# cubre CODIGOS_POSIBLE_BLOQUEO como aviso, no como error.
CABECERAS: dict[str, str] = {}

# Códigos que normalmente significan "nos detectó como bot" o "paywall",
# no que el enlace esté roto: se avisa, no se bloquea (sección 10).
CODIGOS_POSIBLE_BLOQUEO = {401, 403, 429, 999}


def comprobar_enlace(
    url: str,
    *,
    sesion=requests,
    intentos: int = INTENTOS,
    timeout: int = TIMEOUT_SEGUNDOS,
) -> tuple[str, str | None]:
    """Comprueba una URL con reintentos. Devuelve ("ok", None), ("aviso", motivo)
    o ("error", motivo)."""
    ultimo_motivo = "sin detalle"
    for _ in range(intentos):
        try:
            respuesta = sesion.get(url, timeout=timeout, headers=CABECERAS, allow_redirects=True)
        except requests.RequestException as exc:
            ultimo_motivo = str(exc)
            continue
        if respuesta.status_code < 400:
            return "ok", None
        if respuesta.status_code in CODIGOS_POSIBLE_BLOQUEO:
            return (
                "aviso",
                f"{url} devolvió HTTP {respuesta.status_code} (posible bloqueo de bots o paywall)",
            )
        ultimo_motivo = f"HTTP {respuesta.status_code}"
    return "error", f"{url} no respondió correctamente tras {intentos} intentos ({ultimo_motivo})"


def comprobar_enlaces_informe(informe: dict, *, sesion=requests) -> tuple[list[str], list[str]]:
    """Comprueba cada URL única citada en el informe. Devuelve (errores, avisos)."""
    urls = sorted(
        {
            fuente["url"]
            for _, noticia in todas_las_noticias(informe)
            for fuente in noticia["fuentes"]
        }
    )
    errores: list[str] = []
    avisos: list[str] = []
    for url in urls:
        log.info("Comprobando enlace: %s", url)
        resultado, motivo = comprobar_enlace(url, sesion=sesion)
        if resultado == "error":
            assert motivo is not None
            errores.append(motivo)
        elif resultado == "aviso":
            assert motivo is not None
            avisos.append(motivo)
    return errores, avisos
