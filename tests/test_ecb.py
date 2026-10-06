import pytest
import responses

from briefing.fuentes import ecb
from briefing.fuentes.ecb import SinObservaciones

FIXTURE_DFR = {
    "dataSets": [
        {
            "series": {
                "0:0:0:0:0:0:0": {
                    "observations": {"0": [2.5, 0, 0, None, None]},
                }
            }
        }
    ],
    "structure": {
        "dimensions": {
            "observation": [
                {
                    "id": "TIME_PERIOD",
                    "values": [{"id": "2026-10-06", "name": "2026-10-06"}],
                }
            ]
        }
    },
}

FIXTURE_SIN_SERIES = {
    "dataSets": [{"series": {}}],
    "structure": {"dimensions": {"observation": [{"values": []}]}},
}


@responses.activate
def test_tipo_facilidad_deposito_parsea_la_ultima_observacion() -> None:
    responses.add(
        responses.GET,
        "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV",
        json=FIXTURE_DFR,
        status=200,
    )

    dato = ecb.tipo_facilidad_deposito()

    assert dato.valor == 2.5
    assert dato.fecha == "2026-10-06"
    assert dato.unidad == "% anual"
    assert dato.fuente == "BCE"
    assert "FM/D.U2.EUR.4F.KR.DFR.LEV" in dato.url


@responses.activate
def test_eur_usd_referencia_usa_el_dataflow_exr() -> None:
    fixture = {
        **FIXTURE_DFR,
        "dataSets": [
            {"series": {"0:0:0:0:0:0:0": {"observations": {"0": [1.0834]}}}}
        ],
    }
    responses.add(
        responses.GET,
        "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A",
        json=fixture,
        status=200,
    )

    dato = ecb.eur_usd_referencia()

    assert dato.valor == 1.0834
    assert dato.unidad == "USD por EUR"


@responses.activate
def test_sin_series_lanza_error_explicito() -> None:
    responses.add(
        responses.GET,
        "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV",
        json=FIXTURE_SIN_SERIES,
        status=200,
    )

    with pytest.raises(SinObservaciones):
        ecb.tipo_facilidad_deposito()


@responses.activate
def test_error_http_se_propaga() -> None:
    responses.add(
        responses.GET,
        "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV",
        status=503,
    )

    with pytest.raises(Exception):  # requests.exceptions.HTTPError
        ecb.tipo_facilidad_deposito()
