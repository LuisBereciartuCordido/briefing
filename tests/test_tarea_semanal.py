from pathlib import Path

RAIZ = Path(__file__).parent.parent
TAREA = (RAIZ / "TAREA_SEMANAL.md").read_text()


def test_referencia_los_cuatro_scripts_en_orden() -> None:
    posiciones = [
        TAREA.index(f"scripts/{script}")
        for script in ("fetch_data.py", "validate.py", "render.py", "publish.py")
    ]
    assert posiciones == sorted(posiciones), "los scripts deben aparecer en orden de ejecución"


def test_referencia_los_tres_prompts() -> None:
    for nombre in ("redactor.md", "verificador.md", "estilo.md"):
        assert f"prompts/{nombre}" in TAREA


def test_documenta_la_rama_de_archivo_y_el_limite_de_reintentos() -> None:
    assert "claude/archivo-semanal" in TAREA
    assert "2 intentos" in TAREA
