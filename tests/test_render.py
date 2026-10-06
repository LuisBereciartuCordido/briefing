import copy

from briefing import render

from .test_schema import _informe_minimo_valido

MODULOS_CFG = [
    {"id": "eeuu", "titulo": "EE. UU."},
    {"id": "europa", "titulo": "Europa"},
    {"id": "asia_china", "titulo": "Asia y China"},
    {"id": "emergentes", "titulo": "Emergentes"},
    {"id": "energia_materias_primas", "titulo": "Energía y materias primas"},
    {"id": "tecnologia_ia", "titulo": "Tecnología e IA"},
    {"id": "geopolitica_riesgos", "titulo": "Geopolítica y riesgos"},
]

MERCADOS_CFG = [
    {"id": "sp500", "nombre": "S&P 500", "unidad": "puntos"},
    {"id": "eur_usd", "nombre": "EUR/USD", "unidad": "USD por EUR"},
    {"id": "oro", "nombre": "Oro", "unidad": "USD/onza"},
]


def test_formatear_valor_puntos_sin_decimales() -> None:
    assert render._formatear_valor(7700.5, "puntos") == "7,700 puntos"


def test_formatear_valor_porcentaje() -> None:
    assert render._formatear_valor(2.87, "% interanual") == "2.9 %"


def test_formatear_valor_eur_usd_cuatro_decimales() -> None:
    assert render._formatear_valor(1.0834, "USD por EUR") == "1.0834 USD"


def test_formatear_variacion_sin_semana_anterior() -> None:
    assert render._formatear_variacion(100, None) == "—"


def test_formatear_variacion_positiva_lleva_signo() -> None:
    assert render._formatear_variacion(110, 100) == "+10.00 %"


def test_formatear_variacion_negativa() -> None:
    assert render._formatear_variacion(90, 100) == "-10.00 %"


def test_renderizar_lo_esencial() -> None:
    informe = {"lo_esencial": ["Primera cosa.", "Segunda cosa."]}
    salida = render.renderizar_lo_esencial(informe)
    assert "- Primera cosa." in salida
    assert "- Segunda cosa." in salida


def test_renderizar_tabla_mercados_con_variacion() -> None:
    datos = {"sp500": {"valor": 7700.0}, "eur_usd": {"valor": 1.08}}
    anterior = {"sp500": {"valor": 7000.0}}

    salida = render.renderizar_tabla_mercados(datos, anterior, MERCADOS_CFG)

    assert "S&P 500" in salida
    assert "+10.00 %" in salida  # variación respecto a la semana anterior
    assert "—" in salida  # eur_usd no tiene semana anterior en este test
    assert "sin dato" in salida  # "oro" no está en `datos`


def test_renderizar_macro_global_incluye_emoji_de_confianza() -> None:
    informe = _informe_minimo_valido()
    salida = render.renderizar_macro_global(informe)
    assert "✅" in salida  # la noticia de ejemplo tiene confianza=confirmado
    assert informe["macro_global"][0]["titulo"] in salida


def test_renderizar_modulos_sin_novedades() -> None:
    informe = _informe_minimo_valido()  # todos los módulos vienen sin_novedades=True
    salida = render.renderizar_modulos(informe, MODULOS_CFG)
    assert "Sin novedades relevantes esta semana." in salida
    assert "EE. UU." in salida
    assert "Geopolítica y riesgos" in salida


def test_renderizar_modulos_respeta_el_orden_de_modulos_ids() -> None:
    informe = _informe_minimo_valido()
    salida = render.renderizar_modulos(informe, MODULOS_CFG)
    assert salida.index("EE. UU.") < salida.index("Europa") < salida.index("Geopolítica y riesgos")


def test_renderizar_concepto_semana() -> None:
    informe = _informe_minimo_valido()
    salida = render.renderizar_concepto_semana(informe)
    assert informe["concepto_semana"]["titulo"] in salida
    assert informe["concepto_semana"]["texto"] in salida


def test_renderizar_perspectiva_con_listas_vacias() -> None:
    informe = copy.deepcopy(_informe_minimo_valido())
    informe["perspectiva_largo_plazo"] = {"estructural": [], "ruido": []}
    salida = render.renderizar_perspectiva(informe)
    assert salida.count("(nada reseñable)") == 2


def test_renderizar_agenda() -> None:
    informe = _informe_minimo_valido()
    salida = render.renderizar_agenda(informe)
    assert informe["agenda"][0]["evento"] in salida


def test_renderizar_para_profundizar_omite_modulos_sin_novedades() -> None:
    informe = _informe_minimo_valido()  # todos los módulos están sin_novedades=True
    salida = render.renderizar_para_profundizar(informe)
    assert "Macro global" in salida  # macro_global sí tiene una noticia de ejemplo
    assert "eeuu" not in salida


def test_renderizar_indice_no_promete_enlaces_de_ancla() -> None:
    salida = render.renderizar_indice(MODULOS_CFG)
    assert "EE. UU." in salida
    assert "[" not in salida  # no son enlaces, solo una lista de lectura
