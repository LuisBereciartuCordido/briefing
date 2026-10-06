import pytest
import responses

from briefing.fuentes import ine
from briefing.fuentes.ine import SinObservaciones

URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC251856"

# Fixture tomada de una respuesta real de la API (tres meses, Oct-Dic 2025).
FIXTURE = {
    "COD": "IPC251856",
    "Nombre": "Nacional. Índice general. Variación anual. ",
    "Data": [
        {"Fecha": 1759269600000, "FK_Periodo": 10, "Anyo": 2025, "Valor": 3.1},
        {"Fecha": 1761951600000, "FK_Periodo": 11, "Anyo": 2025, "Valor": 3.0},
        {"Fecha": 1764543600000, "FK_Periodo": 12, "Anyo": 2025, "Valor": 2.9},
    ],
}


@responses.activate
def test_ipc_espana_toma_la_ultima_observacion() -> None:
    responses.add(responses.GET, URL, json=FIXTURE, status=200)

    dato = ine.ipc_espana()

    assert dato.valor == 2.9
    assert dato.unidad == "% interanual"
    assert dato.fuente == "INE"
    assert dato.fecha.startswith("2025-12")


@responses.activate
def test_sin_datos_lanza_error_explicito() -> None:
    responses.add(responses.GET, URL, json={"Data": []}, status=200)

    with pytest.raises(SinObservaciones):
        ine.ipc_espana()


@responses.activate
def test_error_http_se_propaga() -> None:
    responses.add(responses.GET, URL, status=503)

    with pytest.raises(Exception):
        ine.ipc_espana()
