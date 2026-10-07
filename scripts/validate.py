#!/usr/bin/env python3
"""Valida informe.json contra el esquema y las reglas de la sección 10 de CLAUDE.md.

Uso:
    python scripts/validate.py --semana AAAA-Sww [--sin-comprobar-enlaces]

Si hay errores (bloqueantes), termina con código de salida 1: el flujo
semanal (sección 8.5) debe detenerse sin publicar el borrador. Los
errores y avisos quedan siempre en data/<semana>/log.json, se publique o
no, para poder revisarlos después.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import jsonschema
import yaml

from briefing import validacion
from briefing.validacion import ResultadoValidacion
from briefing.validacion_enlaces import comprobar_enlaces_informe

log = logging.getLogger("validate")

RAIZ = Path(__file__).resolve().parent.parent
DATA_DIR = RAIZ / "data"
CONFIG_DIR = RAIZ / "config"
SCHEMA_PATH = RAIZ / "schema" / "informe.schema.json"


def _errores_de_esquema(informe: dict, esquema: dict) -> list[str]:
    validador = jsonschema.Draft202012Validator(esquema, format_checker=jsonschema.FormatChecker())
    return sorted(
        f"{'.'.join(str(p) for p in error.path) or '(raíz)'}: {error.message}"
        for error in validador.iter_errors(informe)
    )


def validar_informe(
    informe: dict,
    datos: dict,
    *,
    esquema: dict,
    palabras: dict[str, list[str]],
    modulos_cfg: list[dict],
    fuentes_cfg: dict,
    antiguedad_maxima_dias: int = 10,
    comprobar_enlaces: bool = True,
) -> ResultadoValidacion:
    """Corre todas las comprobaciones de la sección 10 sobre un informe ya cargado."""
    resultado = ResultadoValidacion()

    errores_esquema = _errores_de_esquema(informe, esquema)
    resultado.errores.extend(errores_esquema)
    if errores_esquema:
        # El resto de comprobaciones asumen que informe.json tiene la forma
        # del esquema; si no la tiene, seguir solo daría errores en cascada
        # que no aportan nada nuevo.
        return resultado

    resultado.errores.extend(validacion.validar_titular(informe))
    resultado.errores.extend(validacion.validar_confianza_y_fuentes(informe, fuentes_cfg))
    resultado.errores.extend(validacion.validar_nivel_de_fuentes(informe, fuentes_cfg))
    resultado.errores.extend(validacion.validar_cifras(informe, datos))
    resultado.errores.extend(
        validacion.validar_fechas_fuente(informe, antiguedad_maxima_dias)
    )
    resultado.errores.extend(validacion.validar_palabras_prohibidas(informe, palabras))

    resultado.avisos.extend(validacion.avisos_limite_palabras(informe, modulos_cfg))
    resultado.avisos.extend(validacion.avisos_concentracion_medios(informe))
    resultado.avisos.extend(validacion.avisos_modulo_sin_fuentes_fiables(informe))
    resultado.avisos.extend(validacion.avisos_fuentes_no_catalogadas(informe, fuentes_cfg))
    resultado.avisos.extend(validacion.avisos_titular_largo(informe))
    resultado.avisos.extend(validacion.avisos_concepto_semana_largo(informe))

    if comprobar_enlaces:
        errores_enlaces, avisos_enlaces = comprobar_enlaces_informe(informe)
        resultado.errores.extend(errores_enlaces)
        resultado.avisos.extend(avisos_enlaces)

    return resultado


def _escribir_en_log(carpeta: Path, resultado: ResultadoValidacion) -> None:
    ruta = carpeta / "log.json"
    contenido = json.loads(ruta.read_text()) if ruta.exists() else {}
    contenido["validacion"] = {"errores": resultado.errores, "avisos": resultado.avisos}
    ruta.write_text(json.dumps(contenido, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semana", required=True, help="Semana ISO a validar (AAAA-Sww)")
    parser.add_argument(
        "--sin-comprobar-enlaces",
        action="store_true",
        help="No comprobar los enlaces por HTTP (más rápido para iterar en local)",
    )
    args = parser.parse_args(argv)

    carpeta = DATA_DIR / args.semana
    informe = json.loads((carpeta / "informe.json").read_text())
    datos = json.loads((carpeta / "datos.json").read_text())
    esquema = json.loads(SCHEMA_PATH.read_text())
    palabras = yaml.safe_load((CONFIG_DIR / "validacion.yaml").read_text())
    modulos_cfg = yaml.safe_load((CONFIG_DIR / "modulos.yaml").read_text())
    fuentes_cfg = yaml.safe_load((CONFIG_DIR / "fuentes.yaml").read_text())

    resultado = validar_informe(
        informe,
        datos,
        esquema=esquema,
        palabras=palabras,
        antiguedad_maxima_dias=fuentes_cfg["antiguedad_maxima_dias"],
        modulos_cfg=modulos_cfg,
        fuentes_cfg=fuentes_cfg,
        comprobar_enlaces=not args.sin_comprobar_enlaces,
    )
    _escribir_en_log(carpeta, resultado)

    for error in resultado.errores:
        log.error(error)
    for aviso in resultado.avisos:
        log.warning(aviso)

    if not resultado.es_valido:
        log.error("informe.json tiene %d error(es); no se debe publicar", len(resultado.errores))
        return 1

    log.info("informe.json válido (%d aviso(s))", len(resultado.avisos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
