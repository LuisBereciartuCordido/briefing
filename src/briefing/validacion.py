"""Comprobaciones deterministas de informe.json (sección 10 de CLAUDE.md).

Separa "errores" (bloquean la publicación) de "avisos" (no bloquean, pero
se muestran en el resumen). La comprobación de enlaces caídos vive en
validacion_enlaces.py porque hace peticiones HTTP reales; todo lo de este
módulo es puro (no toca la red ni el disco), lo que lo hace fácil de
testear y de reutilizar.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from briefing.modelos import MODULOS_IDS, todas_las_noticias


@dataclass
class ResultadoValidacion:
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def es_valido(self) -> bool:
        return not self.errores


def _dominio(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def _nivel_catalogado(dominio: str, fuentes_cfg: dict) -> int | None:
    """Nivel real de un dominio según fuentes.yaml, o None si no está catalogado.

    Coincide también por subdominio: "ecb.europa.eu" coincide con el
    catalogado "europa.eu", no solo por igualdad exacta (config/fuentes.yaml
    documenta por qué: europa.eu cubre todas las instituciones de la UE).
    """
    for nivel, datos_nivel in fuentes_cfg["niveles"].items():
        for catalogado in datos_nivel["dominios"]:
            if dominio == catalogado or dominio.endswith("." + catalogado):
                return nivel
    return None


def validar_confianza_y_fuentes(informe: dict, fuentes_cfg: dict) -> list[str]:
    """confirmado exige >=2 fuentes de dominios distintos, o alguna de nivel 1 real.

    "Nivel 1 real" = catalogado como tal en fuentes.yaml, no el `nivel` que
    la propia noticia autodeclara: un dominio no catalogado no puede, por sí
    solo, confirmar una noticia aunque diga nivel=1 (el mismatch entre nivel
    declarado y nivel catalogado lo bloquea aparte validar_nivel_de_fuentes).
    """
    errores = []
    for ubicacion, noticia in todas_las_noticias(informe):
        if noticia["confianza"] != "confirmado":
            continue
        fuentes = noticia["fuentes"]
        dominios_distintos = {_dominio(f["url"]) for f in fuentes}
        hay_nivel_1_real = any(
            _nivel_catalogado(_dominio(f["url"]), fuentes_cfg) == 1 for f in fuentes
        )
        if len(dominios_distintos) < 2 and not hay_nivel_1_real:
            errores.append(
                f"[{ubicacion}] {noticia['id']}: confianza=confirmado pero no tiene "
                f"ni 2 fuentes de dominios distintos ni ninguna catalogada como nivel 1"
            )
    return errores


def validar_nivel_de_fuentes(informe: dict, fuentes_cfg: dict) -> list[str]:
    """El nivel que declara cada fuente debe coincidir con el de fuentes.yaml.

    Sin esto, el esquema solo exige que `nivel` sea 1, 2 o 3 — nada impedía
    que una noticia autodeclarase nivel=1 citando un dominio catalogado como
    nivel 2 (o al revés). Un dominio no catalogado no es error aquí: eso lo
    cubre avisos_fuentes_no_catalogadas, porque puede ser una fuente nueva
    legítima que solo falta añadir a la lista.
    """
    errores = []
    for ubicacion, noticia in todas_las_noticias(informe):
        for fuente in noticia["fuentes"]:
            dominio = _dominio(fuente["url"])
            nivel_real = _nivel_catalogado(dominio, fuentes_cfg)
            if nivel_real is not None and nivel_real != fuente["nivel"]:
                errores.append(
                    f"[{ubicacion}] {noticia['id']}: {dominio} está catalogado como "
                    f"nivel {nivel_real} en fuentes.yaml, pero la fuente declara "
                    f"nivel {fuente['nivel']}"
                )
    return errores


def avisos_fuentes_no_catalogadas(informe: dict, fuentes_cfg: dict) -> list[str]:
    """Aviso (no bloquea) por cada dominio citado que no está en fuentes.yaml.

    Puede ser una fuente nueva legítima — por eso es aviso, no error — pero
    conviene revisarla y, si corresponde, añadirla a fuentes.yaml en vez de
    dejarla citada sin catalogar semana tras semana.
    """
    avisos = []
    dominios_avisados: set[str] = set()
    for _, noticia in todas_las_noticias(informe):
        for fuente in noticia["fuentes"]:
            dominio = _dominio(fuente["url"])
            if dominio in dominios_avisados:
                continue
            if _nivel_catalogado(dominio, fuentes_cfg) is None:
                avisos.append(f"{dominio}: dominio no catalogado en fuentes.yaml")
                dominios_avisados.add(dominio)
    return avisos


def validar_titular(informe: dict) -> list[str]:
    """titular.noticia_id debe corresponder a una noticia real del informe.

    Sin esta comprobación, un id mal escrito o que quedó huérfano tras
    deduplicar en la "Unión" (sección 8) pasaría el esquema sin más —
    noticia_id es solo una cadena, el esquema no sabe qué ids existen
    (hallazgo real de /code-review).
    """
    ids_existentes = {n["id"] for _, n in todas_las_noticias(informe)}
    noticia_id = informe["titular"]["noticia_id"]
    if noticia_id not in ids_existentes:
        return [f"titular.noticia_id ('{noticia_id}') no corresponde a ninguna noticia del informe"]
    return []


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


def validar_fechas_fuente(informe: dict, antiguedad_maxima_dias: int = 10) -> list[str]:
    """Una fuente más antigua que `antiguedad_maxima_dias` (prompts/redactor.md,
    config/fuentes.yaml) debe estar marcada como contexto histórico.

    No exige que la fuente caiga dentro del periodo exacto del informe: una
    noticia del lunes puede perfectamente citar un artículo del jueves
    anterior, que sigue siendo "de esta semana" a efectos periodísticos.
    Lo que no se permite sin marcar es una fuente más vieja que el límite
    de antigüedad, ni una fuente con fecha futura respecto al cierre del
    periodo (eso sería sospechoso, no "reciente").
    """
    fin = datetime.date.fromisoformat(informe["periodo"]["fin"])
    limite_antiguedad = fin - datetime.timedelta(days=antiguedad_maxima_dias)
    errores = []
    for ubicacion, noticia in todas_las_noticias(informe):
        for fuente in noticia["fuentes"]:
            if fuente.get("contexto_historico", False):
                continue
            fecha_fuente = datetime.date.fromisoformat(fuente["fecha"])
            if not (limite_antiguedad <= fecha_fuente <= fin):
                errores.append(
                    f"[{ubicacion}] {noticia['id']}: fuente del {fuente['fecha']} tiene más "
                    f"de {antiguedad_maxima_dias} días de antigüedad respecto al "
                    f"{fin.isoformat()} (o es posterior), y no está marcada como contexto histórico"
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
