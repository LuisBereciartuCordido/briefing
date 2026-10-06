"""Cliente de datos del BCE: tipo de la facilidad de depósito y EUR/USD.

Usa la API SDMX 2.1 del ECB Data Portal (sección 6 de CLAUDE.md), que no
requiere clave. Verificado contra la API real: data-api.ecb.europa.eu
devuelve "dataSets" y "structure" en la raíz de la respuesta (no bajo una
clave "data", como asumen algunos ejemplos de terceros).
"""

from __future__ import annotations

import logging

import requests

from briefing.modelos import Dato

log = logging.getLogger(__name__)

BASE_URL = "https://data-api.ecb.europa.eu/service/data"
TIMEOUT_SEGUNDOS = 20


class SinObservaciones(ValueError):
    """La respuesta del BCE no contiene ninguna observación para la serie pedida."""


def _ultima_observacion(dataflow: str, key: str) -> tuple[str, float]:
    """Pide lastNObservations=1 y devuelve (periodo, valor).

    Se pide solo la última observación: el BCE la fija por serie (una key
    SDMX totalmente específica), así que la respuesta siempre trae una
    única serie con una única observación.
    """
    url = f"{BASE_URL}/{dataflow}/{key}"
    log.info("Consultando BCE: %s", url)
    respuesta = requests.get(
        url,
        params={"lastNObservations": 1, "format": "jsondata"},
        headers={"Accept": "application/json"},
        timeout=TIMEOUT_SEGUNDOS,
    )
    respuesta.raise_for_status()
    cuerpo = respuesta.json()

    series = cuerpo["dataSets"][0].get("series", {})
    if not series:
        raise SinObservaciones(f"El BCE no devolvió series para {dataflow}/{key}")

    (observaciones,) = (serie["observations"] for serie in series.values())
    if not observaciones:
        raise SinObservaciones(f"El BCE no devolvió observaciones para {dataflow}/{key}")

    periodos = cuerpo["structure"]["dimensions"]["observation"][0]["values"]
    indice = max(int(i) for i in observaciones)
    valor = observaciones[str(indice)][0]
    periodo = periodos[indice]["id"]
    return periodo, float(valor)


def tipo_facilidad_deposito() -> Dato:
    """Tipo de la facilidad de depósito del BCE (dataflow FM), % anual."""
    dataflow, key = "FM", "D.U2.EUR.4F.KR.DFR.LEV"
    periodo, valor = _ultima_observacion(dataflow, key)
    return Dato(
        valor=valor,
        unidad="% anual",
        fecha=periodo,
        fuente="BCE",
        url=f"{BASE_URL}/{dataflow}/{key}",
    )


def eur_usd_referencia() -> Dato:
    """Tipo de cambio de referencia EUR/USD del BCE (dataflow EXR), USD por EUR."""
    dataflow, key = "EXR", "D.USD.EUR.SP00.A"
    periodo, valor = _ultima_observacion(dataflow, key)
    return Dato(
        valor=valor,
        unidad="USD por EUR",
        fecha=periodo,
        fuente="BCE",
        url=f"{BASE_URL}/{dataflow}/{key}",
    )
