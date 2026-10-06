import json

import pytest
import responses

from briefing.buttondown import ButtondownApiKeyFaltante, ErrorButtondown, crear_borrador

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


def test_sin_api_key_lanza_error_explicito(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BUTTONDOWN_API_KEY", raising=False)

    with pytest.raises(ButtondownApiKeyFaltante):
        crear_borrador("Asunto", "cuerpo")
