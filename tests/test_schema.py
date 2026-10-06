import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "informe.schema.json"


@pytest.fixture()
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _modulo_vacio() -> dict:
    return {"sin_novedades": True, "noticias": []}


def _informe_minimo_valido() -> dict:
    return {
        "semana": "2026-S41",
        "periodo": {"inicio": "2026-10-05", "fin": "2026-10-11"},
        "titular": {
            "texto": "El BCE mantiene los tipos mientras el mercado mira a octubre",
            "noticia_id": "2026-S41-macro-01",
        },
        "lo_esencial": ["El BCE mantiene los tipos sin cambios."],
        "macro_global": [
            {
                "id": "2026-S41-macro-01",
                "hilo_id": "bce-tipos-2026",
                "titulo": "El BCE mantiene los tipos",
                "texto": "El Banco Central Europeo no movió los tipos de interés.",
                "por_que_importa": "Afecta a las hipotecas variables.",
                "confianza": "confirmado",
                "relevancia_espana_ue": "alta",
                "fuentes": [
                    {
                        "url": "https://www.ecb.europa.eu/press/pr/date/2026/html/ecb.mp261005.es.html",
                        "medio": "BCE",
                        "nivel": 1,
                        "fecha": "2026-10-05",
                        "idioma": "es",
                    }
                ],
                "cifras": [],
            }
        ],
        "modulos": {
            "eeuu": _modulo_vacio(),
            "europa": _modulo_vacio(),
            "asia_china": _modulo_vacio(),
            "emergentes": _modulo_vacio(),
            "energia_materias_primas": _modulo_vacio(),
            "tecnologia_ia": _modulo_vacio(),
            "geopolitica_riesgos": _modulo_vacio(),
        },
        "concepto_semana": {
            "id": "tipos-de-interes",
            "titulo": "¿Qué son los tipos de interés?",
            "texto": "El precio del dinero, fijado por los bancos centrales.",
        },
        "perspectiva_largo_plazo": {
            "estructural": ["La política monetaria sigue restrictiva."],
            "ruido": [],
        },
        "fuentes_descartadas": [],
        "cambios_verificador": [],
    }


def test_informe_minimo_valido_pasa_el_esquema(schema: dict) -> None:
    jsonschema.validate(_informe_minimo_valido(), schema)


def test_falta_un_modulo_obligatorio_falla(schema: dict) -> None:
    informe = _informe_minimo_valido()
    del informe["modulos"]["geopolitica_riesgos"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(informe, schema)


def test_confianza_con_valor_no_permitido_falla(schema: dict) -> None:
    informe = _informe_minimo_valido()
    informe["macro_global"][0]["confianza"] = "muy_segura"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(informe, schema)


def test_noticia_sin_fuentes_falla(schema: dict) -> None:
    informe = _informe_minimo_valido()
    informe["macro_global"][0]["fuentes"] = []
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(informe, schema)


def test_fuente_con_contexto_historico_es_opcional(schema: dict) -> None:
    informe = _informe_minimo_valido()
    informe["macro_global"][0]["fuentes"][0]["contexto_historico"] = True
    jsonschema.validate(informe, schema)  # no debe lanzar

    # Y sigue siendo válida sin el campo (no es obligatorio).
    informe_sin_campo = _informe_minimo_valido()
    jsonschema.validate(informe_sin_campo, schema)


def test_modulo_sin_novedades_false_y_sin_noticias_falla(schema: dict) -> None:
    # Hallazgo real de /code-review: sin esta regla, render.py produciría
    # una sección "## Título\n\n" vacía, sin ningún aviso.
    informe = _informe_minimo_valido()
    informe["modulos"]["eeuu"] = {"sin_novedades": False, "noticias": []}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(informe, schema)


def test_modulo_sin_novedades_true_y_sin_noticias_pasa(schema: dict) -> None:
    informe = _informe_minimo_valido()
    informe["modulos"]["eeuu"] = {"sin_novedades": True, "noticias": []}
    jsonschema.validate(informe, schema)  # no debe lanzar
