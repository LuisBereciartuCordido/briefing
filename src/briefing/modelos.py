"""Modelos tipados que reflejan schema/informe.schema.json.

No sustituyen la validación contra el esquema (eso lo hace validate.py con
jsonschema): son la representación en memoria que usan render.py y el resto
del código una vez que informe.json ya se sabe válido.

También incluye Dato, el modelo que usan los clientes de
src/briefing/fuentes/ para datos.json (sección 6 de CLAUDE.md), que no
tiene esquema propio porque no lo produce el redactor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

MODULOS_IDS = (
    "eeuu",
    "europa",
    "asia_china",
    "emergentes",
    "energia_materias_primas",
    "tecnologia_ia",
    "geopolitica_riesgos",
)


def todas_las_noticias(informe: dict) -> list[tuple[str, dict]]:
    """[(ubicacion, noticia), ...] de todo el informe (macro_global + módulos).

    Vive aquí, y no en validacion.py, porque validacion.py,
    validacion_enlaces.py y render.py necesitan recorrer el informe
    exactamente igual y ninguno de los tres debería depender de otro solo
    por esto.
    """
    noticias = [("macro_global", n) for n in informe.get("macro_global", [])]
    for id_modulo, modulo in informe.get("modulos", {}).items():
        noticias += [(id_modulo, n) for n in modulo.get("noticias", [])]
    return noticias


@dataclass(frozen=True, slots=True)
class Dato:
    """Un dato duro de datos.json: valor, unidad, fecha, fuente y URL."""

    valor: float
    unidad: str
    fecha: str
    fuente: str
    url: str

    def to_dict(self) -> dict:
        return {
            "valor": self.valor,
            "unidad": self.unidad,
            "fecha": self.fecha,
            "fuente": self.fuente,
            "url": self.url,
        }


class Confianza(str, Enum):
    CONFIRMADO = "confirmado"
    UNA_FUENTE = "una_fuente"
    INTERPRETACION = "interpretacion"


class Relevancia(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


@dataclass(frozen=True, slots=True)
class Fuente:
    url: str
    medio: str
    nivel: int
    fecha: str
    idioma: str

    @classmethod
    def from_dict(cls, data: dict) -> "Fuente":
        return cls(**data)


@dataclass(frozen=True, slots=True)
class Cifra:
    valor: str
    ref_datos: str | None

    @classmethod
    def from_dict(cls, data: dict) -> "Cifra":
        return cls(**data)


@dataclass(frozen=True, slots=True)
class Noticia:
    id: str
    hilo_id: str
    titulo: str
    texto: str
    por_que_importa: str
    confianza: Confianza
    relevancia_espana_ue: Relevancia
    fuentes: list[Fuente]
    cifras: list[Cifra] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Noticia":
        return cls(
            id=data["id"],
            hilo_id=data["hilo_id"],
            titulo=data["titulo"],
            texto=data["texto"],
            por_que_importa=data["por_que_importa"],
            confianza=Confianza(data["confianza"]),
            relevancia_espana_ue=Relevancia(data["relevancia_espana_ue"]),
            fuentes=[Fuente.from_dict(f) for f in data["fuentes"]],
            cifras=[Cifra.from_dict(c) for c in data.get("cifras", [])],
        )


@dataclass(frozen=True, slots=True)
class Modulo:
    sin_novedades: bool
    noticias: list[Noticia] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Modulo":
        return cls(
            sin_novedades=data["sin_novedades"],
            noticias=[Noticia.from_dict(n) for n in data.get("noticias", [])],
        )


@dataclass(frozen=True, slots=True)
class Periodo:
    inicio: str
    fin: str


@dataclass(frozen=True, slots=True)
class ConceptoSemana:
    id: str
    titulo: str
    texto: str


@dataclass(frozen=True, slots=True)
class PerspectivaLargoPlazo:
    estructural: list[str]
    ruido: list[str]


@dataclass(frozen=True, slots=True)
class Titular:
    texto: str
    noticia_id: str


@dataclass(frozen=True, slots=True)
class FuenteDescartada:
    url: str
    motivo: str


@dataclass(frozen=True, slots=True)
class CambioVerificador:
    noticia_id: str
    cambio: str
    motivo: str


@dataclass(frozen=True, slots=True)
class Informe:
    semana: str
    periodo: Periodo
    titular: Titular
    lo_esencial: list[str]
    macro_global: list[Noticia]
    modulos: dict[str, Modulo]
    concepto_semana: ConceptoSemana
    perspectiva_largo_plazo: PerspectivaLargoPlazo
    fuentes_descartadas: list[FuenteDescartada] = field(default_factory=list)
    cambios_verificador: list[CambioVerificador] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Informe":
        return cls(
            semana=data["semana"],
            periodo=Periodo(**data["periodo"]),
            titular=Titular(**data["titular"]),
            lo_esencial=list(data["lo_esencial"]),
            macro_global=[Noticia.from_dict(n) for n in data["macro_global"]],
            modulos={k: Modulo.from_dict(v) for k, v in data["modulos"].items()},
            concepto_semana=ConceptoSemana(**data["concepto_semana"]),
            perspectiva_largo_plazo=PerspectivaLargoPlazo(**data["perspectiva_largo_plazo"]),
            fuentes_descartadas=[
                FuenteDescartada(**f) for f in data.get("fuentes_descartadas", [])
            ],
            cambios_verificador=[
                CambioVerificador(**c) for c in data.get("cambios_verificador", [])
            ],
        )
