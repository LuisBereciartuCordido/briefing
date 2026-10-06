import datetime

from briefing.semanas import periodo_de_semana, semana_anterior, semana_iso


def test_semana_iso() -> None:
    assert semana_iso(datetime.date(2026, 10, 5)) == "2026-S41"


def test_periodo_de_semana() -> None:
    lunes, domingo = periodo_de_semana("2026-S41")
    assert lunes == datetime.date(2026, 10, 5)
    assert domingo == datetime.date(2026, 10, 11)


def test_semana_anterior() -> None:
    assert semana_anterior("2026-S41") == "2026-S40"


def test_semana_anterior_cruza_el_año() -> None:
    assert semana_anterior("2026-S01") == "2025-S52"
