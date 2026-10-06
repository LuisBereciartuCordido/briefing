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

# Series mensuales: solo se incluyen en datos.json si cambiaron desde la
# última vez que se vieron (proxy de "hubo publicación en el periodo",
# sección 6 de CLAUDE.md — ninguna de las tres APIs expone el calendario
# real de publicación, así que se usa el propio archivo histórico como
# referencia).
CLAVES_MENSUALES = {"ipca_eurozona", "ipc_espana", "ipc_eeuu"}

# Cuántas semanas hacia atrás buscar como máximo la última vez que se vio
# una clave mensual. Una sola semana atrás no basta: si esa clave se omitió
# por no haber cambiado, su archivo no la tiene, y mirar solo ahí haría que
# la semana siguiente la tratara erróneamente como "nueva" otra vez (sección
# 15.4 de CLAUDE.md, hallazgo real de /code-review). Los datos mensuales de
# este proyecto no tardan más de un par de meses en republicarse, así que 8
# semanas da margen de sobra.
LIMITE_SEMANAS_ATRAS = 8


def _fecha_conocida_mas_reciente(clave: str, semana_actual: str) -> str | None:
    """Última fecha de `clave` vista en datos.json, buscando hacia atrás
    semana a semana hasta LIMITE_SEMANAS_ATRAS. None si nunca se ha visto
    (primera vez, o ninguna semana anterior tiene datos.json)."""
    semana = semana_actual
    for _ in range(LIMITE_SEMANAS_ATRAS):
        semana = semana_anterior(semana)
        ruta = DATA_DIR / semana / "datos.json"
        if not ruta.exists():
            continue
        datos_semana = json.loads(ruta.read_text())
        if clave in datos_semana:
            return datos_semana[clave]["fecha"]
    return None


def incluir_si_es_nuevo(clave: str, dato: Dato, fecha_conocida: str | None) -> Dato | None:
    """None si un dato mensual no cambió desde la última vez que se vio; si no, el dato."""
    if fecha_conocida is not None and fecha_conocida == dato.fecha:
        log.info("%s sin cambios desde %s; se omite", clave, fecha_conocida)
        return None
    return dato


def descargar(semana: str) -> dict[str, dict]:
    """Descarga todos los datos duros y devuelve el dict listo para datos.json."""
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
            fecha_conocida = _fecha_conocida_mas_reciente(clave, semana)
            dato_filtrado = incluir_si_es_nuevo(clave, dato, fecha_conocida)
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
