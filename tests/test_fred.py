import pytest
import responses
from responses import matchers

from briefing.fuentes import fred
from briefing.fuentes.fred import FredApiKeyFaltante, SinObservaciones

URL = "https://api.stlouisfed.org/fred/series/observations"


@pytest.fixture(autouse=True)
def clave_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRED_API_KEY", "clave-de-prueba")


def _mock_serie(serie: str, fecha: str, valor: str, **params_extra: str) -> None:
    responses.add(
        responses.GET,
        URL,
        json={"observations": [{"date": fecha, "value": valor}]},
        status=200,
        match=[
            matchers.query_param_matcher(
                {"series_id": serie, **params_extra}, strict_match=False
            )
        ],
    )


@responses.activate
def test_tipo_fed() -> None:
    _mock_serie("FEDFUNDS", "2026-09-01", "4.5")

    dato = fred.tipo_fed()

    assert dato.valor == 4.5
    assert dato.unidad == "% anual"
    assert dato.fuente == "FRED"


@responses.activate
def test_ipc_eeuu_pide_la_variacion_interanual() -> None:
    _mock_serie("CPIAUCSL", "2026-09-01", "2.8", units="pc1")

    dato = fred.ipc_eeuu()

    assert dato.valor == 2.8
    assert dato.unidad == "% interanual"


@responses.activate
def test_sp500() -> None:
    _mock_serie("SP500", "2026-10-03", "7700.5")

    dato = fred.sp500()

    assert dato.valor == 7700.5
    assert dato.unidad == "puntos"


@responses.activate
def test_brent() -> None:
    _mock_serie("DCOILBRENTEU", "2026-10-03", "82.1")

    dato = fred.brent()

    assert dato.valor == 82.1
    assert dato.unidad == "USD/barril"


@responses.activate
def test_valor_vacio_lanza_error_explicito() -> None:
    responses.add(
        responses.GET,
        URL,
        json={"observations": [{"date": "2026-09-01", "value": "."}]},
        status=200,
    )

    with pytest.raises(SinObservaciones):
        fred.tipo_fed()


def test_sin_api_key_lanza_error_explicito(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    with pytest.raises(FredApiKeyFaltante):
        fred.tipo_fed()
