"""Cliente del IPC de España vía la API JSON del INE (Tempus3).

Verificado contra la API real: servicios.ine.es devuelve un objeto con
"Data", una lista de observaciones ordenada de más antigua a más reciente,
cada una con "Fecha" (epoch en milisegundos) y "Valor".
"""

from __future__ import annotations

import datetime
import logging
from zoneinfo import ZoneInfo

import requests

from briefing.modelos import Dato

log = logging.getLogger(__name__)

# IPC251856: "Nacional. Índice general. Variación anual."
SERIE = "IPC251856"
BASE_URL = f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{SERIE}"
TIMEOUT_SEGUNDOS = 20
# "Fecha" llega como medianoche en hora de Madrid, no UTC: convertir con
# timezone.utc desplaza la fecha un día hacia atrás (comprobado contra la
# API real).
ZONA_INE = ZoneInfo("Europe/Madrid")


class SinObservaciones(ValueError):
    """El INE no devolvió ninguna observación para la serie pedida."""


def ipc_espana() -> Dato:
    """Último dato disponible del IPC de España, variación interanual."""
    log.info("Consultando INE: %s", BASE_URL)
    respuesta = requests.get(BASE_URL, params={"nult": 1}, timeout=TIMEOUT_SEGUNDOS)
    respuesta.raise_for_status()
    observaciones = respuesta.json().get("Data") or []
    if not observaciones:
        raise SinObservaciones(f"El INE no devolvió observaciones para la serie {SERIE}")

    observacion = observaciones[-1]
    fecha = (
        datetime.datetime.fromtimestamp(observacion["Fecha"] / 1000, tz=ZONA_INE)
        .date()
        .isoformat()
    )
    return Dato(
        valor=float(observacion["Valor"]),
        unidad="% interanual",
        fecha=fecha,
        fuente="INE",
        url=BASE_URL,
    )
