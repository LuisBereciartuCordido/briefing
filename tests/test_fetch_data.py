import json
from pathlib import Path

import fetch_data
from briefing.modelos import Dato


def test_fecha_conocida_mas_reciente_sin_historial_devuelve_none(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    assert fetch_data._fecha_conocida_mas_reciente("ipc_espana", "2026-S41") is None


def test_fecha_conocida_mas_reciente_lee_la_semana_inmediatamente_anterior(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    (tmp_path / "2026-S40").mkdir()
    (tmp_path / "2026-S40" / "datos.json").write_text(json.dumps({"ipc_espana": {"fecha": "x"}}))

    assert fetch_data._fecha_conocida_mas_reciente("ipc_espana", "2026-S41") == "x"


def test_fecha_conocida_mas_reciente_busca_varias_semanas_atras_si_hace_falta(
    tmp_path: Path, monkeypatch
) -> None:
    # Reproduce el bug real que encontró /code-review: si la clave se omitió
    # en la semana 41 (por no haber cambiado desde la 40), su archivo no la
    # tiene — hay que seguir buscando hasta la 40 para no tratarla como
    # "nueva" otra vez en la semana 42.
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    (tmp_path / "2026-S40").mkdir()
    (tmp_path / "2026-S40" / "datos.json").write_text(json.dumps({"ipc_espana": {"fecha": "x"}}))
    (tmp_path / "2026-S41").mkdir()
    (tmp_path / "2026-S41" / "datos.json").write_text(json.dumps({}))  # omitida esa semana

    assert fetch_data._fecha_conocida_mas_reciente("ipc_espana", "2026-S42") == "x"


def _dato(fecha: str = "2026-09-01") -> Dato:
    return Dato(valor=1.0, unidad="%", fecha=fecha, fuente="test", url="https://x")


def test_incluir_si_es_nuevo_sin_fecha_conocida_incluye_el_dato() -> None:
    assert fetch_data.incluir_si_es_nuevo("ipc_espana", _dato(), None) is not None


def test_incluir_si_es_nuevo_misma_fecha_se_omite() -> None:
    dato = _dato(fecha="2026-09-01")
    assert fetch_data.incluir_si_es_nuevo("ipc_espana", dato, "2026-09-01") is None


def test_incluir_si_es_nuevo_fecha_distinta_se_incluye() -> None:
    dato = _dato(fecha="2026-10-01")
    assert fetch_data.incluir_si_es_nuevo("ipc_espana", dato, "2026-09-01") is dato


def _parchear_fuentes(monkeypatch) -> None:
    monkeypatch.setattr(fetch_data.ecb, "tipo_facilidad_deposito", lambda: _dato("2026-10-06"))
    monkeypatch.setattr(fetch_data.ecb, "eur_usd_referencia", lambda: _dato("2026-10-06"))
    monkeypatch.setattr(fetch_data.eurostat, "ipca_eurozona", lambda: _dato("2026-09-01"))
    monkeypatch.setattr(fetch_data.ine, "ipc_espana", lambda: _dato("2026-09-01"))
    monkeypatch.setattr(fetch_data.fred, "tipo_fed", lambda: _dato("2026-10-03"))
    monkeypatch.setattr(fetch_data.fred, "ipc_eeuu", lambda: _dato("2026-09-01"))
    monkeypatch.setattr(fetch_data.fred, "sp500", lambda: _dato("2026-10-03"))
    monkeypatch.setattr(fetch_data.fred, "brent", lambda: _dato("2026-10-03"))
    monkeypatch.setattr(
        fetch_data.mercados,
        "cierres_semanales",
        lambda: {
            "nikkei225": _dato("2026-10-03"),
            "oro": _dato("2026-10-03"),
            "msci_world": _dato("2026-10-03"),
            "msci_em": _dato("2026-10-03"),
            "msci_europe": _dato("2026-10-03"),
        },
    )


def test_descargar_junta_los_13_instrumentos(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    _parchear_fuentes(monkeypatch)

    datos = fetch_data.descargar("2026-S41")

    assert set(datos) == {
        "bce_tipo_deposito",
        "eur_usd",
        "ipca_eurozona",
        "ipc_espana",
        "fed_tipo",
        "ipc_eeuu",
        "sp500",
        "brent",
        "nikkei225",
        "oro",
        "msci_world",
        "msci_em",
        "msci_europe",
    }


def test_descargar_omite_mensuales_sin_cambios(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    (tmp_path / "2026-S40").mkdir()
    (tmp_path / "2026-S40" / "datos.json").write_text(
        json.dumps({"ipc_espana": {"fecha": "2026-09-01"}})
    )
    _parchear_fuentes(monkeypatch)

    datos = fetch_data.descargar("2026-S41")

    assert "ipc_espana" not in datos


def test_descargar_sigue_omitiendo_mensuales_sin_cambios_varias_semanas_seguidas(
    tmp_path: Path, monkeypatch
) -> None:
    # Regresión del bug real de /code-review: si la semana 41 ya omitió
    # ipc_espana (sin cambios desde la 40), la semana 42 debe seguir
    # omitiéndolo — no tratarlo como "nuevo" solo porque el archivo de la
    # semana 41 no lo tiene.
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    (tmp_path / "2026-S40").mkdir()
    (tmp_path / "2026-S40" / "datos.json").write_text(
        json.dumps({"ipc_espana": {"fecha": "2026-09-01"}})
    )
    _parchear_fuentes(monkeypatch)  # fred.ipc_eeuu etc. siguen devolviendo "2026-09-01"

    datos_41 = fetch_data.descargar("2026-S41")
    assert "ipc_espana" not in datos_41
    (tmp_path / "2026-S41").mkdir()
    (tmp_path / "2026-S41" / "datos.json").write_text(json.dumps(datos_41))

    datos_42 = fetch_data.descargar("2026-S42")
    assert "ipc_espana" not in datos_42


def test_main_escribe_datos_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    _parchear_fuentes(monkeypatch)

    codigo = fetch_data.main(["--semana", "2026-S41"])

    assert codigo == 0
    contenido = json.loads((tmp_path / "2026-S41" / "datos.json").read_text())
    assert contenido["sp500"]["valor"] == 1.0


def test_main_no_escribe_nada_si_falla_una_fuente(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)

    def _falla():
        raise RuntimeError("BCE no responde")

    monkeypatch.setattr(fetch_data.ecb, "tipo_facilidad_deposito", _falla)

    codigo = fetch_data.main(["--semana", "2026-S41"])

    assert codigo == 1
    assert not (tmp_path / "2026-S41").exists()
