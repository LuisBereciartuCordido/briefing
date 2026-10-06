import json
from pathlib import Path

import pytest
import publish

from .test_schema import _informe_minimo_valido


def test_construir_asunto() -> None:
    informe = _informe_minimo_valido()
    asunto = publish.construir_asunto(informe, "Swans & Unicorns")
    assert asunto == "Swans & Unicorns · Semana del 2026-10-05 al 2026-10-11"


def _preparar_semana(tmp_path: Path) -> Path:
    carpeta = tmp_path / "2026-S41"
    carpeta.mkdir()
    (carpeta / "informe.json").write_text(json.dumps(_informe_minimo_valido()))
    (carpeta / "informe.md").write_text("# Hola\n\nCuerpo del email.")
    return carpeta


def test_main_crea_el_borrador_y_devuelve_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(publish, "DATA_DIR", tmp_path)
    _preparar_semana(tmp_path)

    llamadas = []
    monkeypatch.setattr(
        publish,
        "crear_borrador",
        lambda asunto, cuerpo: llamadas.append((asunto, cuerpo)) or {"id": "abc123"},
    )

    codigo = publish.main(["--semana", "2026-S41"])

    assert codigo == 0
    asunto, cuerpo = llamadas[0]
    assert asunto == "Swans & Unicorns · Semana del 2026-10-05 al 2026-10-11"
    assert cuerpo == "# Hola\n\nCuerpo del email."


def test_main_devuelve_1_si_buttondown_falla(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(publish, "DATA_DIR", tmp_path)
    _preparar_semana(tmp_path)

    def _falla(asunto: str, cuerpo: str) -> dict:
        raise RuntimeError("Buttondown no responde")

    monkeypatch.setattr(publish, "crear_borrador", _falla)

    codigo = publish.main(["--semana", "2026-S41"])

    assert codigo == 1
