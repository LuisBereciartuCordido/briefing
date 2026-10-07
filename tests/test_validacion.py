import copy

import pytest

from briefing import validacion
from briefing.validacion import _parsear_numero

from .test_schema import _informe_minimo_valido


def _fuente(url="https://www.reuters.com/a", medio="Reuters", nivel=2, fecha="2026-10-06"):
    return {"url": url, "medio": medio, "nivel": nivel, "fecha": fecha, "idioma": "en"}


def _noticia(id_="2026-S41-x-01", confianza="una_fuente", fuentes=None, cifras=None, **texto):
    return {
        "id": id_,
        "hilo_id": "algo-2026",
        "titulo": texto.get("titulo", "Título"),
        "texto": texto.get("texto", "Texto de la noticia."),
        "por_que_importa": texto.get("por_que_importa", "Por qué importa."),
        "confianza": confianza,
        "relevancia_espana_ue": "media",
        "fuentes": fuentes if fuentes is not None else [_fuente()],
        "cifras": cifras if cifras is not None else [],
    }


def _informe_con(**overrides) -> dict:
    informe = copy.deepcopy(_informe_minimo_valido())
    informe.update(overrides)
    return informe


# fuentes.yaml de prueba, pequeño y estable: no depende del contenido real
# (que puede crecer) para que estos tests no se rompan cuando se amplíe.
FUENTES_CFG = {
    "niveles": {
        1: {"dominios": ["europa.eu"]},
        2: {"dominios": ["reuters.com", "bloomberg.com"]},
        3: {"dominios": ["project-syndicate.org"]},
    }
}


# --- _parsear_numero -------------------------------------------------------


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("2,9%", 2.9),
        ("82.1", 82.1),
        ("7.700,5 puntos", 7700.5),  # español: punto de miles, coma decimal
        ("7,700.5 USD", 7700.5),  # inglés: coma de miles, punto decimal
        ("-3,2 %", -3.2),
    ],
)
def test_parsear_numero(texto: str, esperado: float) -> None:
    assert _parsear_numero(texto) == esperado


def test_parsear_numero_sin_numero_lanza_value_error() -> None:
    with pytest.raises(ValueError):
        _parsear_numero("sin ningún número aquí")


# --- validar_titular --------------------------------------------------------


def test_titular_que_referencia_una_noticia_real_no_da_error() -> None:
    informe = _informe_con(macro_global=[_noticia(id_="2026-S41-macro-01")])
    informe["titular"] = {"texto": "Algo pasó", "noticia_id": "2026-S41-macro-01"}
    assert validacion.validar_titular(informe) == []


def test_titular_con_id_inexistente_da_error() -> None:
    informe = _informe_con(macro_global=[_noticia(id_="2026-S41-macro-01")])
    informe["titular"] = {"texto": "Algo pasó", "noticia_id": "no-existe"}
    assert len(validacion.validar_titular(informe)) == 1


def test_titular_puede_referenciar_una_noticia_de_un_modulo() -> None:
    informe = _informe_con(macro_global=[])
    informe["modulos"]["eeuu"] = {
        "sin_novedades": False,
        "noticias": [_noticia(id_="2026-S41-eeuu-01")],
    }
    informe["titular"] = {"texto": "Algo pasó", "noticia_id": "2026-S41-eeuu-01"}
    assert validacion.validar_titular(informe) == []


# --- validar_confianza_y_fuentes ------------------------------------------


def test_confirmado_con_una_fuente_nivel_1_no_da_error() -> None:
    informe = _informe_con(
        macro_global=[
            _noticia(
                confianza="confirmado",
                fuentes=[_fuente(url="https://www.ecb.europa.eu/x", nivel=1)],
            )
        ]
    )
    assert validacion.validar_confianza_y_fuentes(informe, FUENTES_CFG) == []


def test_confirmado_con_una_sola_fuente_nivel_2_da_error() -> None:
    informe = _informe_con(
        macro_global=[_noticia(confianza="confirmado", fuentes=[_fuente(nivel=2)])]
    )
    assert len(validacion.validar_confianza_y_fuentes(informe, FUENTES_CFG)) == 1


def test_confirmado_con_dos_fuentes_mismo_dominio_da_error() -> None:
    informe = _informe_con(
        macro_global=[
            _noticia(
                confianza="confirmado",
                fuentes=[
                    _fuente(url="https://www.reuters.com/a", nivel=2),
                    _fuente(url="https://www.reuters.com/b", nivel=2),
                ],
            )
        ]
    )
    assert len(validacion.validar_confianza_y_fuentes(informe, FUENTES_CFG)) == 1


def test_confirmado_con_dos_fuentes_dominios_distintos_no_da_error() -> None:
    informe = _informe_con(
        macro_global=[
            _noticia(
                confianza="confirmado",
                fuentes=[
                    _fuente(url="https://www.reuters.com/a", nivel=2),
                    _fuente(url="https://www.bloomberg.com/b", nivel=2),
                ],
            )
        ]
    )
    assert validacion.validar_confianza_y_fuentes(informe, FUENTES_CFG) == []


def test_confirmado_con_nivel_1_autodeclarado_pero_sin_catalogar_da_error() -> None:
    # El cambio clave de este bloque: antes, que la propia noticia se
    # autodeclarase nivel=1 bastaba para confirmar, sin comprobar nada
    # contra fuentes.yaml. Un dominio no catalogado ya no puede, por sí
    # solo, confirmar una noticia aunque diga nivel=1.
    informe = _informe_con(
        macro_global=[
            _noticia(
                confianza="confirmado",
                fuentes=[_fuente(url="https://www.mediodesconocido.com/a", nivel=1)],
            )
        ]
    )
    assert len(validacion.validar_confianza_y_fuentes(informe, FUENTES_CFG)) == 1


# --- validar_nivel_de_fuentes -----------------------------------------------


def test_nivel_declarado_coincide_con_el_catalogado_no_da_error() -> None:
    informe = _informe_con(
        macro_global=[_noticia(fuentes=[_fuente(url="https://www.reuters.com/a", nivel=2)])]
    )
    assert validacion.validar_nivel_de_fuentes(informe, FUENTES_CFG) == []


def test_nivel_declarado_distinto_del_catalogado_da_error() -> None:
    informe = _informe_con(
        macro_global=[_noticia(fuentes=[_fuente(url="https://www.reuters.com/a", nivel=1)])]
    )
    assert len(validacion.validar_nivel_de_fuentes(informe, FUENTES_CFG)) == 1


def test_nivel_declarado_para_dominio_no_catalogado_no_da_error() -> None:
    # Un dominio no catalogado no es error aquí: puede ser una fuente nueva
    # legítima (lo cubre, por separado, avisos_fuentes_no_catalogadas).
    informe = _informe_con(
        macro_global=[
            _noticia(fuentes=[_fuente(url="https://www.mediodesconocido.com/a", nivel=1)])
        ]
    )
    assert validacion.validar_nivel_de_fuentes(informe, FUENTES_CFG) == []


def test_nivel_catalogado_coincide_tambien_por_subdominio() -> None:
    informe = _informe_con(
        macro_global=[_noticia(fuentes=[_fuente(url="https://www.ecb.europa.eu/x", nivel=1)])]
    )
    assert validacion.validar_nivel_de_fuentes(informe, FUENTES_CFG) == []


# --- avisos_fuentes_no_catalogadas -------------------------------------------


def test_dominio_catalogado_no_genera_aviso() -> None:
    informe = _informe_con(
        macro_global=[_noticia(fuentes=[_fuente(url="https://www.reuters.com/a", nivel=2)])]
    )
    assert validacion.avisos_fuentes_no_catalogadas(informe, FUENTES_CFG) == []


def test_dominio_no_catalogado_genera_aviso() -> None:
    informe = _informe_con(
        macro_global=[
            _noticia(fuentes=[_fuente(url="https://www.mediodesconocido.com/a", nivel=2)])
        ]
    )
    assert len(validacion.avisos_fuentes_no_catalogadas(informe, FUENTES_CFG)) == 1


def test_dominio_no_catalogado_repetido_avisa_una_sola_vez() -> None:
    informe = _informe_con(
        macro_global=[
            _noticia(
                id_="2026-S41-x-01",
                fuentes=[_fuente(url="https://www.mediodesconocido.com/a", nivel=2)],
            ),
            _noticia(
                id_="2026-S41-x-02",
                fuentes=[_fuente(url="https://www.mediodesconocido.com/b", nivel=2)],
            ),
        ]
    )
    assert len(validacion.avisos_fuentes_no_catalogadas(informe, FUENTES_CFG)) == 1


# --- validar_cifras ---------------------------------------------------------


def test_cifra_sin_ref_datos_no_se_comprueba() -> None:
    informe = _informe_con(
        macro_global=[_noticia(cifras=[{"valor": "2,9%", "ref_datos": None}])]
    )
    assert validacion.validar_cifras(informe, datos={}) == []


def test_cifra_con_ref_datos_inexistente_da_error() -> None:
    informe = _informe_con(
        macro_global=[_noticia(cifras=[{"valor": "2,9%", "ref_datos": "no_existe"}])]
    )
    assert len(validacion.validar_cifras(informe, datos={})) == 1


def test_cifra_que_coincide_dentro_de_tolerancia_no_da_error() -> None:
    informe = _informe_con(
        macro_global=[_noticia(cifras=[{"valor": "2,90%", "ref_datos": "ipc_espana"}])]
    )
    datos = {"ipc_espana": {"valor": 2.9}}
    assert validacion.validar_cifras(informe, datos) == []


def test_cifra_que_no_coincide_da_error() -> None:
    informe = _informe_con(
        macro_global=[_noticia(cifras=[{"valor": "3,5%", "ref_datos": "ipc_espana"}])]
    )
    datos = {"ipc_espana": {"valor": 2.9}}
    assert len(validacion.validar_cifras(informe, datos)) == 1


# --- validar_fechas_fuente ---------------------------------------------------


def test_fuente_dentro_del_periodo_no_da_error() -> None:
    informe = _informe_con(macro_global=[_noticia(fuentes=[_fuente(fecha="2026-10-07")])])
    assert validacion.validar_fechas_fuente(informe) == []


def test_fuente_antes_del_periodo_pero_reciente_no_da_error() -> None:
    # El periodo del informe mínimo es 2026-10-05 a 2026-10-11. Una fuente
    # del 2026-10-02 es anterior al inicio del periodo, pero solo tiene 9
    # días de antigüedad respecto al cierre (10-11) — dentro del límite de
    # 10 días de prompts/redactor.md, así que no debería bloquear. Este es
    # justo el caso real que encontró la prueba en local de la sección 15.4.
    informe = _informe_con(macro_global=[_noticia(fuentes=[_fuente(fecha="2026-10-02")])])
    assert validacion.validar_fechas_fuente(informe) == []


def test_fuente_demasiado_antigua_sin_marcar_da_error() -> None:
    informe = _informe_con(macro_global=[_noticia(fuentes=[_fuente(fecha="2026-01-01")])])
    assert len(validacion.validar_fechas_fuente(informe)) == 1


def test_fuente_demasiado_antigua_marcada_como_historica_no_da_error() -> None:
    fuente = _fuente(fecha="2026-01-01")
    fuente["contexto_historico"] = True
    informe = _informe_con(macro_global=[_noticia(fuentes=[fuente])])
    assert validacion.validar_fechas_fuente(informe) == []


def test_fuente_con_fecha_futura_da_error() -> None:
    informe = _informe_con(macro_global=[_noticia(fuentes=[_fuente(fecha="2026-10-12")])])
    assert len(validacion.validar_fechas_fuente(informe)) == 1


def test_antiguedad_maxima_dias_es_configurable() -> None:
    informe = _informe_con(macro_global=[_noticia(fuentes=[_fuente(fecha="2026-10-02")])])
    # Con un límite de solo 3 días, esa misma fuente del 10-02 ya no entra.
    assert len(validacion.validar_fechas_fuente(informe, antiguedad_maxima_dias=3)) == 1


# --- validar_palabras_prohibidas --------------------------------------------

PALABRAS = {"sensacionalismo": ["pánico"], "recomendacion": ["deberías comprar"]}


def test_texto_limpio_no_da_error() -> None:
    informe = _informe_con(macro_global=[_noticia(texto="Todo normal esta semana.")])
    assert validacion.validar_palabras_prohibidas(informe, PALABRAS) == []


def test_texto_con_palabra_prohibida_da_error() -> None:
    informe = _informe_con(macro_global=[_noticia(texto="Cunde el pánico en los mercados.")])
    assert len(validacion.validar_palabras_prohibidas(informe, PALABRAS)) == 1


# --- avisos_limite_palabras --------------------------------------------------

MODULOS_CFG = [{"id": "eeuu", "limite_palabras": 5}]


def test_modulo_bajo_el_limite_no_avisa() -> None:
    informe = _informe_minimo_valido()
    informe["modulos"]["eeuu"] = {
        "sin_novedades": False,
        "noticias": [_noticia(titulo="corto", texto="", por_que_importa="")],
    }
    assert validacion.avisos_limite_palabras(informe, MODULOS_CFG) == []


def test_modulo_supera_el_limite_avisa() -> None:
    informe = _informe_minimo_valido()
    informe["modulos"]["eeuu"] = {
        "sin_novedades": False,
        "noticias": [
            _noticia(titulo="una frase con bastantes palabras de más", texto="", por_que_importa="")
        ],
    }
    assert len(validacion.avisos_limite_palabras(informe, MODULOS_CFG)) == 1


def test_modulo_sin_novedades_no_se_cuenta() -> None:
    informe = _informe_minimo_valido()  # todos los módulos ya vienen con sin_novedades=True
    assert validacion.avisos_limite_palabras(informe, MODULOS_CFG) == []


# --- avisos_concentracion_medios --------------------------------------------


def test_fuentes_repartidas_no_avisa() -> None:
    informe = _informe_con(
        macro_global=[
            _noticia(fuentes=[_fuente(medio="Reuters"), _fuente(medio="Bloomberg")])
        ]
    )
    assert validacion.avisos_concentracion_medios(informe) == []


def test_un_medio_mayoritario_avisa() -> None:
    informe = _informe_con(
        macro_global=[
            _noticia(
                fuentes=[_fuente(medio="Reuters"), _fuente(medio="Reuters"), _fuente(medio="BCE")]
            )
        ]
    )
    assert len(validacion.avisos_concentracion_medios(informe)) == 1


# --- avisos_modulo_sin_fuentes_fiables ---------------------------------------


def test_modulo_con_fuente_nivel_2_no_avisa() -> None:
    informe = _informe_minimo_valido()
    informe["modulos"]["eeuu"] = {
        "sin_novedades": False,
        "noticias": [_noticia(fuentes=[_fuente(nivel=2)])],
    }
    assert validacion.avisos_modulo_sin_fuentes_fiables(informe) == []


def test_modulo_solo_con_fuentes_nivel_3_avisa() -> None:
    informe = _informe_minimo_valido()
    informe["modulos"]["eeuu"] = {
        "sin_novedades": False,
        "noticias": [_noticia(fuentes=[_fuente(nivel=3)])],
    }
    assert len(validacion.avisos_modulo_sin_fuentes_fiables(informe)) == 1
