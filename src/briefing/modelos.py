"""Modelos tipados que reflejan schema/informe.schema.json.

No sustituyen la validación contra el esquema (eso lo hace validate.py con
jsonschema): son la representación en memoria que usan render.py y el resto
del código una vez que informe.json ya se sabe válido.
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
class EventoAgenda:
    fecha: str
    evento: str
    por_que_importa: str


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
    lo_esencial: list[str]
    macro_global: list[Noticia]
    modulos: dict[str, Modulo]
    concepto_semana: ConceptoSemana
    perspectiva_largo_plazo: PerspectivaLargoPlazo
    agenda: list[EventoAgenda]
    fuentes_descartadas: list[FuenteDescartada] = field(default_factory=list)
    cambios_verificador: list[CambioVerificador] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Informe":
        return cls(
            semana=data["semana"],
            periodo=Periodo(**data["periodo"]),
            lo_esencial=list(data["lo_esencial"]),
            macro_global=[Noticia.from_dict(n) for n in data["macro_global"]],
            modulos={k: Modulo.from_dict(v) for k, v in data["modulos"].items()},
            concepto_semana=ConceptoSemana(**data["concepto_semana"]),
            perspectiva_largo_plazo=PerspectivaLargoPlazo(**data["perspectiva_largo_plazo"]),
            agenda=[EventoAgenda(**a) for a in data["agenda"]],
            fuentes_descartadas=[
                FuenteDescartada(**f) for f in data.get("fuentes_descartadas", [])
            ],
            cambios_verificador=[
                CambioVerificador(**c) for c in data.get("cambios_verificador", [])
            ],
        )
