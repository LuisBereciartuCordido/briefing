from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def test_los_tres_prompts_existen_y_no_estan_vacios() -> None:
    for nombre in ("redactor.md", "verificador.md", "estilo.md"):
        contenido = (PROMPTS_DIR / nombre).read_text()
        assert len(contenido.strip()) > 0, f"{nombre} está vacío"


def test_redactor_y_verificador_referencian_estilo_y_esquema() -> None:
    redactor = (PROMPTS_DIR / "redactor.md").read_text()
    verificador = (PROMPTS_DIR / "verificador.md").read_text()

    assert "prompts/estilo.md" in redactor
    assert "schema/informe.schema.json" in redactor
    assert "prompts/estilo.md" in verificador
    assert "schema/informe.schema.json" in verificador


def test_redactor_referencia_los_configs_por_nivel_modulos_y_fuentes() -> None:
    redactor = (PROMPTS_DIR / "redactor.md").read_text()
    assert "config/fuentes.yaml" in redactor
    assert "config/modulos.yaml" in redactor
