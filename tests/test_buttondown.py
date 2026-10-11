import json

import pytest
import responses

from briefing.buttondown import ErrorButtondown, crear_borrador

URL = "https://api.buttondown.com/v1/emails"


@pytest.fixture(autouse=True)
def clave_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUTTONDOWN_API_KEY", "clave-de-prueba")


@responses.activate
def test_crear_borrador_envia_status_draft_y_la_cabecera_de_autenticacion() -> None:
    responses.add(responses.POST, URL, json={"id": "abc123"}, status=201)

    resultado = crear_borrador("Asunto de prueba", "# Hola")

    assert resultado == {"id": "abc123"}
    peticion = responses.calls[0].request
    assert peticion.headers["Authorization"] == "Token clave-de-prueba"
    cuerpo = json.loads(peticion.body)
    assert cuerpo["subject"] == "Asunto de prueba"
    assert cuerpo["status"] == "draft"
    assert cuerpo["body"].endswith("# Hola")
    assert "buttondown-editor-mode: plaintext" in cuerpo["body"]


@responses.activate
def test_error_de_la_api_lanza_error_explicito() -> None:
    responses.add(responses.POST, URL, body="Unauthorized", status=401)

    with pytest.raises(ErrorButtondown):
        crear_borrador("Asunto", "cuerpo")


@responses.activate
def test_sin_api_key_no_manda_cabecera_de_autenticacion(monkeypatch: pytest.MonkeyPatch) -> None:
    # No es un error local: en la Routine, BUTTONDOWN_API_KEY es un API
    # credential del *environment*, no una variable de entorno legible por
    # este código — el proxy de red añade la cabecera, no el propio script
    # (hallazgo real de la primera ejecución real, semana 2026-S41: el
    # código fallaba aquí en vez de dejar que el proxy completara la
    # petición). Si no hay credential en ningún sitio, Buttondown
    # responde 401 y eso ya lo cubre el otro test con ErrorButtondown.
    monkeypatch.delenv("BUTTONDOWN_API_KEY", raising=False)
    responses.add(responses.POST, URL, json={"id": "abc123"}, status=201)

    crear_borrador("Asunto", "cuerpo")

    peticion = responses.calls[0].request
    assert "Authorization" not in peticion.headers
