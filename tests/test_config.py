from pathlib import Path

import yaml

from briefing.modelos import MODULOS_IDS

CONFIG_DIR = Path(__file__).parent.parent / "config"


def test_modulos_yaml_coincide_con_el_esquema() -> None:
    modulos = yaml.safe_load((CONFIG_DIR / "modulos.yaml").read_text())

    ids = [m["id"] for m in modulos]
    assert ids == list(MODULOS_IDS), (
        "El orden/los ids de config/modulos.yaml deben coincidir "
        "exactamente con MODULOS_IDS (y con schema/informe.schema.json)"
    )
    for modulo in modulos:
        assert modulo["titulo"]
        assert modulo["limite_palabras"] > 0


def test_fuentes_yaml_tiene_los_tres_niveles() -> None:
    fuentes = yaml.safe_load((CONFIG_DIR / "fuentes.yaml").read_text())

    assert set(fuentes["niveles"]) == {1, 2, 3}
    for nivel, datos in fuentes["niveles"].items():
        assert datos["descripcion"]
        assert len(datos["dominios"]) > 0
        for dominio in datos["dominios"]:
            assert "." in dominio and "/" not in dominio, (
                f"'{dominio}' en nivel {nivel} debería ser un dominio, no una URL"
            )

    assert fuentes["antiguedad_maxima_dias"] > 0


def test_mercados_yaml_tiene_ids_unicos() -> None:
    mercados = yaml.safe_load((CONFIG_DIR / "mercados.yaml").read_text())

    ids = [m["id"] for m in mercados]
    assert len(ids) == len(set(ids)), "Los ids de config/mercados.yaml deben ser únicos"
    for instrumento in mercados:
        assert instrumento["nombre"]
        assert instrumento["unidad"]
