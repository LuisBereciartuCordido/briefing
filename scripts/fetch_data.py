#!/usr/bin/env python3
"""Descarga los datos duros de la semana y los guarda en data/<semana>/datos.json.

Uso:
    python scripts/fetch_data.py [--semana AAAA-Sww]

Si falla cualquier fuente, el script termina con código de salida distinto
de cero y **no** escribe datos.json (sección 4 de CLAUDE.md: "si un paso
falla, el flujo se detiene... y no crea el borrador").
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path

from briefing.fuentes import ecb, eurostat, fred, ine, mercados
from briefing.modelos import Dato
from briefing.semanas import semana_anterior, semana_iso

log = logging.getLogger("fetch_data")

RAIZ = Path(__file__).resolve().parent.parent
DATA_DIR = RAIZ / "data"

# Series mensuales: solo se incluyen en datos.json si cambiaron respecto a
# la semana anterior (proxy de "hubo publicación en el periodo", sección 6
# de CLAUDE.md — ninguna de las tres APIs expone el calendario real de
# publicación, así que se usa el propio archivo histórico como referencia).
CLAVES_MENSUALES = {"ipca_eurozona", "ipc_espana", "ipc_eeuu"}


def leer_datos_semana_anterior(semana_actual: str) -> dict | None:
    """Lee datos.json de la semana ISO anterior, si existe."""
    ruta = DATA_DIR / semana_anterior(semana_actual) / "datos.json"
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text())


def incluir_si_es_nuevo(clave: str, dato: Dato, datos_semana_anterior: dict | None) -> Dato | None:
    """None si un dato mensual no cambió desde la semana anterior; si no, el dato."""
    if datos_semana_anterior is None:
        return dato
    anterior = datos_semana_anterior.get(clave)
    if anterior is not None and anterior.get("fecha") == dato.fecha:
        log.info("%s sin cambios desde la semana pasada (%s); se omite", clave, dato.fecha)
        return None
    return dato


def descargar(semana: str) -> dict[str, dict]:
    """Descarga todos los datos duros y devuelve el dict listo para datos.json."""
    anterior = leer_datos_semana_anterior(semana)
    datos: dict[str, Dato] = {}

    log.info("Descargando datos del BCE...")
    datos["bce_tipo_deposito"] = ecb.tipo_facilidad_deposito()
    datos["eur_usd"] = ecb.eur_usd_referencia()

    log.info("Descargando IPCA de la eurozona (Eurostat)...")
    datos["ipca_eurozona"] = eurostat.ipca_eurozona()

    log.info("Descargando IPC de España (INE)...")
    datos["ipc_espana"] = ine.ipc_espana()

    log.info("Descargando datos de la Fed y mercados de EE. UU. (FRED)...")
    datos["fed_tipo"] = fred.tipo_fed()
    datos["ipc_eeuu"] = fred.ipc_eeuu()
    datos["sp500"] = fred.sp500()
    datos["brent"] = fred.brent()

    log.info("Descargando mercados vía Yahoo Finance...")
    datos.update(mercados.cierres_semanales())

    resultado: dict[str, dict] = {}
    for clave, dato in datos.items():
        if clave in CLAVES_MENSUALES:
            dato_filtrado = incluir_si_es_nuevo(clave, dato, anterior)
            if dato_filtrado is None:
                continue
            resultado[clave] = dato_filtrado.to_dict()
        else:
            resultado[clave] = dato.to_dict()
    return resultado


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--semana", help="Forzar la semana ISO (AAAA-Sww); por defecto, la semana actual"
    )
    args = parser.parse_args(argv)

    semana = args.semana or semana_iso(datetime.date.today())

    try:
        datos = descargar(semana)
    except Exception:
        log.exception("Fallo al descargar los datos duros; no se escribe datos.json")
        return 1

    destino = DATA_DIR / semana
    destino.mkdir(parents=True, exist_ok=True)
    ruta_datos = destino / "datos.json"
    ruta_datos.write_text(json.dumps(datos, indent=2, ensure_ascii=False, sort_keys=True))
    log.info("Escrito %s", ruta_datos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
