"""Comprobaciones deterministas de informe.json (sección 12 de CLAUDE.md).

Separa "errores" (bloquean la publicación) de "avisos" (no bloquean, pero
se muestran en el resumen). La comprobación de enlaces caídos vive en
validacion_enlaces.py porque hace peticiones HTTP reales; todo lo de este
módulo es puro (no toca la red ni el disco), lo que lo hace fácil de
testear y de reutilizar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from briefing.modelos import MODULOS_IDS


@dataclass
class ResultadoValidacion:
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def es_valido(self) -> bool:
        return not self.errores


def todas_las_noticias(informe: dict) -> list[tuple[str, dict]]:
    """[(ubicacion, noticia), ...] de todo el informe, para no repetir el recorrido."""
    noticias = [("macro_global", n) for n in informe.get("macro_global", [])]
    for id_modulo, modulo in informe.get("modulos", {}).items():
        noticias += [(id_modulo, n) for n in modulo.get("noticias", [])]
    return noticias


def _dominio(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def validar_confianza_y_fuentes(informe: dict) -> list[str]:
    """confirmado exige >=2 fuentes de dominios distintos, o alguna de nivel 1."""
    errores = []
    for ubicacion, noticia in todas_las_noticias(informe):
        if noticia["confianza"] != "confirmado":
            continue
        fuentes = noticia["fuentes"]
        dominios_distintos = {_dominio(f["url"]) for f in fuentes}
        hay_nivel_1 = any(f["nivel"] == 1 for f in fuentes)
        if len(dominios_distintos) < 2 and not hay_nivel_1:
            errores.append(
                f"[{ubicacion}] {noticia['id']}: confianza=confirmado pero no tiene "
                f"ni 2 fuentes de dominios distintos ni ninguna de nivel 1"
            )
    return errores


def _parsear_numero(texto: str) -> float:
    """Extrae el primer número de un texto.

    Cuando aparecen los dos separadores, el último es el decimal y el otro
    es de miles (sirve tanto para "7.700,5" en español como para
    "7,700.5" en inglés). Con un solo separador no hay forma fiable de
    saber si es decimal o de miles (sin saber el idioma de origen), así
    que se asume siempre decimal — que es como vienen los números crudos
    en datos.json. Si el redactor escribe miles con un único punto o coma
    y sin parte decimal (p. ej. "7.700" queriendo decir siete mil
    setecientos), esta función lo interpretará mal a propósito: es
    preferible que validate.py señale una cifra para revisar a mano que
    adivinar en silencio.
    """
    coincidencia = re.search(r"-?\d[\d.,]*", texto)
    if not coincidencia:
        raise ValueError(f"no se encontró ningún número en «{texto}»")
    numero = coincidencia.group()

    if "," in numero and "." in numero:
        if numero.rindex(",") > numero.rindex("."):
            numero = numero.replace(".", "").replace(",", ".")
        else:
            numero = numero.replace(",", "")
    elif "," in numero:
        numero = numero.replace(",", ".")

    return float(numero)


def validar_cifras(informe: dict, datos: dict) -> list[str]:
    """Cada cifra con ref_datos debe existir en datos.json y coincidir en valor."""
    errores = []
    for ubicacion, noticia in todas_las_noticias(informe):
        for cifra in noticia.get("cifras", []):
            ref = cifra["ref_datos"]
            if ref is None:
                continue
            if ref not in datos:
                errores.append(
                    f"[{ubicacion}] {noticia['id']}: cifra «{cifra['valor']}» referencia "
                    f"'{ref}', que no existe en datos.json"
                )
                continue
            try:
                valor_cifra = _parsear_numero(cifra["valor"])
            except ValueError as exc:
                errores.append(
                    f"[{ubicacion}] {noticia['id']}: no se pudo interpretar la cifra "
                    f"«{cifra['valor']}» ({exc})"
                )
                continue
            valor_dato = float(datos[ref]["valor"])
            tolerancia = max(0.01, abs(valor_dato) * 0.005)
            if abs(valor_cifra - valor_dato) > tolerancia:
                errores.append(
                    f"[{ubicacion}] {noticia['id']}: cifra «{cifra['valor']}» "
                    f"({valor_cifra}) no coincide con datos.json['{ref}'] ({valor_dato})"
                )
    return errores


def validar_fechas_fuente(informe: dict) -> list[str]:
    """Una fuente fuera del periodo debe estar marcada como contexto histórico."""
    inicio = informe["periodo"]["inicio"]
    fin = informe["periodo"]["fin"]
    errores = []
    for ubicacion, noticia in todas_las_noticias(informe):
        for fuente in noticia["fuentes"]:
            if fuente.get("contexto_historico", False):
                continue
            if not (inicio <= fuente["fecha"] <= fin):
                errores.append(
                    f"[{ubicacion}] {noticia['id']}: fuente del {fuente['fecha']} fuera "
                    f"del periodo {inicio}/{fin} y sin marcar como contexto histórico"
                )
    return errores


def validar_palabras_prohibidas(informe: dict, palabras: dict[str, list[str]]) -> list[str]:
    """Bloquea noticias con sensacionalismo o recomendaciones de inversión."""
    todas_las_palabras = [
        (categoria, palabra.lower())
        for categoria, lista in palabras.items()
        for palabra in lista
    ]
    errores = []
    for ubicacion, noticia in todas_las_noticias(informe):
        texto = " ".join(
            [noticia["titulo"], noticia["texto"], noticia["por_que_importa"]]
        ).lower()
        for categoria, palabra in todas_las_palabras:
            if palabra in texto:
                errores.append(
                    f"[{ubicacion}] {noticia['id']}: contiene «{palabra}» ({categoria})"
                )
    return errores


def avisos_limite_palabras(informe: dict, modulos_cfg: list[dict]) -> list[str]:
    """Avisa si el texto de un módulo supera su límite de palabras."""
    limites = {m["id"]: m["limite_palabras"] for m in modulos_cfg}
    avisos = []
    for id_modulo in MODULOS_IDS:
        modulo = informe["modulos"][id_modulo]
        if modulo.get("sin_novedades"):
            continue
        texto = " ".join(
            " ".join([n["titulo"], n["texto"], n["por_que_importa"]])
            for n in modulo["noticias"]
        )
        n_palabras = len(texto.split())
        limite = limites.get(id_modulo)
        if limite and n_palabras > limite:
            avisos.append(
                f"Módulo '{id_modulo}': {n_palabras} palabras, supera el límite de {limite}"
            )
    return avisos


def avisos_concentracion_medios(informe: dict, umbral: float = 0.5) -> list[str]:
    """Avisa si más de `umbral` de las fuentes del informe son del mismo medio."""
    medios: dict[str, int] = {}
    total = 0
    for _, noticia in todas_las_noticias(informe):
        for fuente in noticia["fuentes"]:
            medios[fuente["medio"]] = medios.get(fuente["medio"], 0) + 1
            total += 1

    if total == 0:
        return []

    avisos = []
    for medio, cuenta in medios.items():
        proporcion = cuenta / total
        if proporcion > umbral:
            avisos.append(
                f"'{medio}' es el {proporcion:.0%} de todas las fuentes del informe "
                f"(umbral: {umbral:.0%})"
            )
    return avisos


def avisos_modulo_sin_fuentes_fiables(informe: dict) -> list[str]:
    """Avisa si un módulo con novedades no tiene ninguna fuente de nivel 1 o 2."""
    avisos = []
    for id_modulo in MODULOS_IDS:
        modulo = informe["modulos"][id_modulo]
        if modulo.get("sin_novedades"):
            continue
        niveles = {
            fuente["nivel"] for noticia in modulo["noticias"] for fuente in noticia["fuentes"]
        }
        if niveles and niveles.issubset({3}):
            avisos.append(f"Módulo '{id_modulo}': ninguna fuente de nivel 1 o 2")
    return avisos
