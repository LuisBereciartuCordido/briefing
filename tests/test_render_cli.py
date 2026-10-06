import json
from pathlib import Path

import render

from .test_schema import _informe_minimo_valido


def test_main_escribe_informe_md(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(render, "DATA_DIR", tmp_path)

    carpeta = tmp_path / "2026-S41"
    carpeta.mkdir()
    (carpeta / "informe.json").write_text(json.dumps(_informe_minimo_valido()))
    (carpeta / "datos.json").write_text(json.dumps({}))

    codigo = render.main(["--semana", "2026-S41"])

    assert codigo == 0
    contenido = (carpeta / "informe.md").read_text()
    assert "Swans & Unicorns" in contenido
    assert "No es asesoramiento financiero" in contenido


def test_main_usa_datos_de_la_semana_anterior_si_existen(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(render, "DATA_DIR", tmp_path)

    def _dato(valor: float) -> dict:
        return {"valor": valor, "unidad": "puntos", "fecha": "2026-10-03", "fuente": "FRED", "url": "https://x"}

    (tmp_path / "2026-S40").mkdir()
    (tmp_path / "2026-S40" / "datos.json").write_text(json.dumps({"sp500": _dato(7000.0)}))

    carpeta = tmp_path / "2026-S41"
    carpeta.mkdir()
    (carpeta / "informe.json").write_text(json.dumps(_informe_minimo_valido()))
    (carpeta / "datos.json").write_text(json.dumps({"sp500": _dato(7700.0)}))

    render.main(["--semana", "2026-S41"])

    contenido = (carpeta / "informe.md").read_text()
    assert "+10.00 %" in contenido  # variación calculada contra la semana anterior
