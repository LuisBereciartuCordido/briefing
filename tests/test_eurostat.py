import pytest
import responses

from briefing.fuentes import eurostat
from briefing.fuentes.eurostat import SinObservaciones

URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/prc_hicp_manr/M.RCH_A.CP00.EA20"

FIXTURE = {
    "value": {"345": 2.3, "346": 2.1, "347": 2.9},
    "dimension": {
        "time": {
            "category": {"index": {"2025-10": 345, "2025-11": 346, "2025-12": 347}}
        }
    },
}


@responses.activate
def test_ipca_eurozona_toma_el_indice_mas_alto_no_el_ultimo_insertado() -> None:
    responses.add(responses.GET, URL, json=FIXTURE, status=200)

    dato = eurostat.ipca_eurozona()

    assert dato.valor == 2.9
    assert dato.fecha == "2025-12-01"
    assert dato.unidad == "% interanual"
    assert dato.fuente == "Eurostat"


@responses.activate
def test_sin_valores_lanza_error_explicito() -> None:
    responses.add(
        responses.GET,
        URL,
        json={"value": {}, "dimension": {"time": {"category": {"index": {}}}}},
        status=200,
    )

    with pytest.raises(SinObservaciones):
        eurostat.ipca_eurozona()


@responses.activate
def test_error_http_se_propaga() -> None:
    responses.add(responses.GET, URL, status=503)

    with pytest.raises(Exception):
        eurostat.ipca_eurozona()
