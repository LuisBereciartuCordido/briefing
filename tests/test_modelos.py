from briefing.modelos import Confianza, Informe, Relevancia

from .test_schema import _informe_minimo_valido


def test_informe_from_dict_reconstruye_los_tipos() -> None:
    informe = Informe.from_dict(_informe_minimo_valido())

    assert informe.semana == "2026-S41"
    assert informe.periodo.inicio == "2026-10-05"
    assert set(informe.modulos) == {
        "eeuu",
        "europa",
        "asia_china",
        "emergentes",
        "energia_materias_primas",
        "tecnologia_ia",
        "geopolitica_riesgos",
    }

    noticia = informe.macro_global[0]
    assert noticia.confianza is Confianza.CONFIRMADO
    assert noticia.relevancia_espana_ue is Relevancia.ALTA
    assert noticia.fuentes[0].nivel == 1
    assert noticia.cifras == []
