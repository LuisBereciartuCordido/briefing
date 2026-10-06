import copy
import json
from pathlib import Path

import validate

from .test_schema import _informe_minimo_valido

SCHEMA = json.loads(validate.SCHEMA_PATH.read_text())
MODULOS_CFG = [{"id": "eeuu", "limite_palabras": 110}]
PALABRAS: dict[str, list[str]] = {"sensacionalismo": [], "recomendacion": []}


def test_informe_valido_no_tiene_errores() -> None:
    # El informe mínimo solo trae una fuente (BCE), así que SÍ dispara el
    # aviso (no bloqueante) de concentración de medios: es el comportamiento
    # esperado, no un fallo. Lo que importa aquí es que no hay errores.
    resultado = validate.validar_informe(
        _informe_minimo_valido(),
        datos={},
        esquema=SCHEMA,
        palabras=PALABRAS,
        modulos_cfg=MODULOS_CFG,
        comprobar_enlaces=False,
    )

    assert resultado.es_valido
    assert resultado.errores == []


def test_error_de_esquema_no_sigue_con_las_demas_comprobaciones() -> None:
    informe = copy.deepcopy(_informe_minimo_valido())
    del informe["modulos"]["geopolitica_riesgos"]  # rompe el esquema (módulo obligatorio)

    resultado = validate.validar_informe(
        informe,
        datos={},
        esquema=SCHEMA,
        palabras=PALABRAS,
        modulos_cfg=MODULOS_CFG,
        comprobar_enlaces=False,
    )

    assert not resultado.es_valido
    assert len(resultado.errores) == 1  # solo el error de esquema, sin cascada


def test_titular_con_id_inexistente_bloquea_un_informe_por_lo_demas_valido() -> None:
    informe = copy.deepcopy(_informe_minimo_valido())
    informe["titular"]["noticia_id"] = "no-existe"

    resultado = validate.validar_informe(
        informe,
        datos={},
        esquema=SCHEMA,
        palabras=PALABRAS,
        modulos_cfg=MODULOS_CFG,
        comprobar_enlaces=False,
    )

    assert not resultado.es_valido
    assert "no-existe" in resultado.errores[0]


def test_palabra_prohibida_bloquea_un_informe_por_lo_demas_valido() -> None:
    informe = copy.deepcopy(_informe_minimo_valido())
    informe["macro_global"][0]["texto"] += " Cunde el pánico en los mercados."

    resultado = validate.validar_informe(
        informe,
        datos={},
        esquema=SCHEMA,
        palabras={"sensacionalismo": ["pánico"], "recomendacion": []},
        modulos_cfg=MODULOS_CFG,
        comprobar_enlaces=False,
    )

    assert not resultado.es_valido


def _escribir_semana(tmp_path: Path, semana: str, informe: dict, datos: dict) -> Path:
    carpeta = tmp_path / semana
    carpeta.mkdir()
    (carpeta / "informe.json").write_text(json.dumps(informe))
    (carpeta / "datos.json").write_text(json.dumps(datos))
    return carpeta


def test_main_informe_valido_devuelve_0_y_escribe_log(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(validate, "DATA_DIR", tmp_path)
    carpeta = _escribir_semana(tmp_path, "2026-S41", _informe_minimo_valido(), {})

    codigo = validate.main(["--semana", "2026-S41", "--sin-comprobar-enlaces"])

    assert codigo == 0
    log_contenido = json.loads((carpeta / "log.json").read_text())
    assert log_contenido["validacion"]["errores"] == []


def test_main_informe_invalido_devuelve_1_y_registra_el_error(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(validate, "DATA_DIR", tmp_path)
    informe_roto = copy.deepcopy(_informe_minimo_valido())
    del informe_roto["modulos"]["geopolitica_riesgos"]
    carpeta = _escribir_semana(tmp_path, "2026-S41", informe_roto, {})

    codigo = validate.main(["--semana", "2026-S41", "--sin-comprobar-enlaces"])

    assert codigo == 1
    log_contenido = json.loads((carpeta / "log.json").read_text())
    assert len(log_contenido["validacion"]["errores"]) == 1
