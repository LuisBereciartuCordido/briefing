"""Cliente de inflación de Eurostat: IPCA de la eurozona, variación interanual.

Usa el dataset prc_hicp_manr de la API de difusión de Eurostat. Esta API
devuelve XML por defecto (format=JSON es obligatorio), y aun pidiendo JSON
el formato no es SDMX-JSON como el BCE, sino JSON-stat 2.0 — una forma
distinta, verificada contra la API real antes de escribir el parser (ver
la desviación registrada en CLAUDE.md, sección 6).
"""

from __future__ import annotations

import logging

import requests

from briefing.modelos import Dato

log = logging.getLogger(__name__)

DATASET = "prc_hicp_manr"
# M = mensual, RCH_A = tasa de variación interanual, CP00 = índice general
# (todas las partidas), EA20 = zona euro de 20 países.
KEY = "M.RCH_A.CP00.EA20"
BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data"
TIMEOUT_SEGUNDOS = 20


class SinObservaciones(ValueError):
    """La respuesta de Eurostat no contiene ningún valor para la serie pedida."""


def ipca_eurozona() -> Dato:
    """Último dato disponible del IPCA de la eurozona, variación interanual.

    "fecha" es el primer día del mes de referencia del dato (p. ej.
    "2025-12-01" para el dato de diciembre de 2025), no la fecha de
    publicación: Eurostat no la expone en esta respuesta.
    """
    url = f"{BASE_URL}/{DATASET}/{KEY}"
    log.info("Consultando Eurostat: %s", url)
    respuesta = requests.get(url, params={"format": "JSON"}, timeout=TIMEOUT_SEGUNDOS)
    respuesta.raise_for_status()
    cuerpo = respuesta.json()

    valores = cuerpo.get("value") or {}
    if not valores:
        raise SinObservaciones(f"Eurostat no devolvió valores para {DATASET}/{KEY}")

    indice_por_periodo = cuerpo["dimension"]["time"]["category"]["index"]
    periodo_por_indice = {indice: periodo for periodo, indice in indice_por_periodo.items()}

    ultimo_indice = max(int(i) for i in valores)
    periodo = periodo_por_indice[ultimo_indice]
    valor = valores[str(ultimo_indice)]

    return Dato(
        valor=float(valor),
        unidad="% interanual",
        fecha=f"{periodo}-01",
        fuente="Eurostat",
        url=url,
    )
