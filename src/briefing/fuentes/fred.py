"""Cliente de datos de la Fed y mercados de EE. UU. vía la API de FRED.

Requiere la variable de entorno FRED_API_KEY (clave gratuita, se obtiene
en https://fred.stlouisfed.org/docs/api/api_key.html).
"""

from __future__ import annotations

import logging
import os

import requests

from briefing.modelos import Dato

log = logging.getLogger(__name__)

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
TIMEOUT_SEGUNDOS = 20


class FredApiKeyFaltante(RuntimeError):
    """No se encontró la variable de entorno FRED_API_KEY."""


class SinObservaciones(ValueError):
    """FRED no devolvió ninguna observación válida para la serie pedida."""


def _clave_api() -> str:
    clave = os.environ.get("FRED_API_KEY")
    if not clave:
        raise FredApiKeyFaltante(
            "Falta la variable de entorno FRED_API_KEY (clave gratuita de FRED)"
        )
    return clave


def _ultima_observacion(serie: str, **parametros_extra: str) -> tuple[str, float]:
    parametros = {
        "series_id": serie,
        "api_key": _clave_api(),
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
        **parametros_extra,
    }
    log.info("Consultando FRED: serie %s", serie)
    respuesta = requests.get(BASE_URL, params=parametros, timeout=TIMEOUT_SEGUNDOS)
    respuesta.raise_for_status()
    observaciones = respuesta.json().get("observations") or []
    if not observaciones:
        raise SinObservaciones(f"FRED no devolvió observaciones para la serie {serie}")

    observacion = observaciones[0]
    if observacion["value"] == ".":
        raise SinObservaciones(
            f"FRED devolvió un valor vacío para la serie {serie} en {observacion['date']}"
        )
    return observacion["date"], float(observacion["value"])


def _url_serie(serie: str) -> str:
    return f"https://fred.stlouisfed.org/series/{serie}"


def tipo_fed() -> Dato:
    """Tipo de interés efectivo de los fondos federales (FEDFUNDS), % anual."""
    fecha, valor = _ultima_observacion("FEDFUNDS")
    return Dato(valor=valor, unidad="% anual", fecha=fecha, fuente="FRED", url=_url_serie("FEDFUNDS"))


def ipc_eeuu() -> Dato:
    """IPC de EE. UU., variación interanual (CPIAUCSL con units=pc1)."""
    fecha, valor = _ultima_observacion("CPIAUCSL", units="pc1")
    return Dato(
        valor=valor, unidad="% interanual", fecha=fecha, fuente="FRED", url=_url_serie("CPIAUCSL")
    )


def sp500() -> Dato:
    """Último cierre diario del S&P 500 (SP500)."""
    fecha, valor = _ultima_observacion("SP500")
    return Dato(valor=valor, unidad="puntos", fecha=fecha, fuente="FRED", url=_url_serie("SP500"))


def brent() -> Dato:
    """Precio del Brent, USD por barril (DCOILBRENTEU)."""
    fecha, valor = _ultima_observacion("DCOILBRENTEU")
    return Dato(
        valor=valor, unidad="USD/barril", fecha=fecha, fuente="FRED", url=_url_serie("DCOILBRENTEU")
    )
