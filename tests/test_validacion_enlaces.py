import requests
import responses

from briefing.validacion_enlaces import comprobar_enlace, comprobar_enlaces_informe

URL = "https://www.reuters.com/articulo"


@responses.activate
def test_enlace_ok_no_reintenta() -> None:
    responses.add(responses.GET, URL, status=200)

    resultado, motivo = comprobar_enlace(URL)

    assert (resultado, motivo) == ("ok", None)
    assert len(responses.calls) == 1


@responses.activate
def test_enlace_roto_tras_agotar_reintentos() -> None:
    responses.add(responses.GET, URL, status=404)
    responses.add(responses.GET, URL, status=404)

    resultado, motivo = comprobar_enlace(URL, intentos=2)

    assert resultado == "error"
    assert "404" in motivo
    assert len(responses.calls) == 2


@responses.activate
def test_posible_bloqueo_de_bots_es_aviso_no_error() -> None:
    responses.add(responses.GET, URL, status=403)

    resultado, motivo = comprobar_enlace(URL, intentos=2)

    assert resultado == "aviso"
    assert "403" in motivo
    assert len(responses.calls) == 1  # no hace falta reintentar un bloqueo


@responses.activate
def test_fallo_de_red_que_se_recupera_al_reintentar() -> None:
    responses.add(responses.GET, URL, body=requests.exceptions.ConnectionError())
    responses.add(responses.GET, URL, status=200)

    resultado, motivo = comprobar_enlace(URL, intentos=2)

    assert (resultado, motivo) == ("ok", None)


@responses.activate
def test_fallo_de_red_persistente_es_error() -> None:
    responses.add(responses.GET, URL, body=requests.exceptions.ConnectionError())
    responses.add(responses.GET, URL, body=requests.exceptions.ConnectionError())

    resultado, motivo = comprobar_enlace(URL, intentos=2)

    assert resultado == "error"


def _noticia(url: str) -> dict:
    return {
        "id": "x",
        "fuentes": [{"url": url, "medio": "Reuters", "nivel": 2, "fecha": "2026-10-06", "idioma": "es"}],
    }


@responses.activate
def test_comprobar_enlaces_informe_deduplica_urls_repetidas() -> None:
    responses.add(responses.GET, URL, status=200)
    informe = {
        "macro_global": [_noticia(URL)],
        "modulos": {"eeuu": {"noticias": [_noticia(URL)]}},  # misma URL, otra noticia
    }

    errores, avisos = comprobar_enlaces_informe(informe)

    assert errores == []
    assert avisos == []
    assert len(responses.calls) == 1  # se comprobó una sola vez, no dos


@responses.activate
def test_comprobar_enlaces_informe_separa_errores_de_avisos() -> None:
    responses.add(responses.GET, "https://www.reuters.com/rota", status=404)
    responses.add(responses.GET, "https://www.ft.com/bloqueada", status=403)
    informe = {
        "macro_global": [_noticia("https://www.reuters.com/rota")],
        "modulos": {"eeuu": {"noticias": [_noticia("https://www.ft.com/bloqueada")]}},
    }

    errores, avisos = comprobar_enlaces_informe(informe)

    assert len(errores) == 1
    assert len(avisos) == 1
