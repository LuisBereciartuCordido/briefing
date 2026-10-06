"""Renderiza informe.json (+ datos.json) a Markdown (sección 13 de CLAUDE.md).

El cuerpo principal (puntos 1 a 7 de la sección 5) vive en este módulo.
Las piezas de cierre (paquete de contexto para IA, transparencia y aviso
legal) se añaden en un commit posterior, junto con el ensamblado final y
la CLI en scripts/render.py.
"""

from __future__ import annotations

from briefing.modelos import MODULOS_IDS

EMOJI_CONFIANZA = {
    "confirmado": "✅",
    "una_fuente": "⚠️",
    "interpretacion": "💬",
}


def _formatear_valor(valor: float, unidad: str) -> str:
    if unidad == "puntos":
        return f"{valor:,.0f} puntos"
    if unidad in ("% anual", "% interanual"):
        return f"{valor:.1f} %"
    if unidad == "USD por EUR":
        return f"{valor:.4f} USD"
    return f"{valor:,.2f} {unidad}"


def _formatear_variacion(actual: float, anterior: float | None) -> str:
    if anterior is None or anterior == 0:
        return "—"
    variacion = (actual - anterior) / anterior * 100
    return f"{variacion:+.2f} %"


def renderizar_lo_esencial(informe: dict) -> str:
    lineas = "\n".join(f"- {linea}" for linea in informe["lo_esencial"])
    return f"## Lo esencial\n\n{lineas}\n"


def renderizar_tabla_mercados(
    datos: dict, datos_semana_anterior: dict | None, mercados_cfg: list[dict]
) -> str:
    filas = ["| Instrumento | Valor | Variación semanal |", "| :-- | --: | --: |"]
    for instrumento in mercados_cfg:
        id_ = instrumento["id"]
        dato = datos.get(id_)
        if dato is None:
            filas.append(f"| {instrumento['nombre']} | sin dato | — |")
            continue
        anterior = (datos_semana_anterior or {}).get(id_, {}).get("valor")
        valor_fmt = _formatear_valor(dato["valor"], instrumento["unidad"])
        variacion_fmt = _formatear_variacion(dato["valor"], anterior)
        filas.append(f"| {instrumento['nombre']} | {valor_fmt} | {variacion_fmt} |")
    tabla = "\n".join(filas)
    return f"## Mercados esta semana\n\n{tabla}\n"


def _renderizar_fuentes(fuentes: list[dict]) -> str:
    return " · ".join(f"[{f['medio']}]({f['url']})" for f in fuentes)


def _renderizar_noticia(noticia: dict) -> str:
    emoji = EMOJI_CONFIANZA[noticia["confianza"]]
    return (
        f"**{noticia['titulo']}**\n\n"
        f"{noticia['texto']} {emoji}\n\n"
        f"*Por qué importa:* {noticia['por_que_importa']}\n\n"
        f"Fuentes: {_renderizar_fuentes(noticia['fuentes'])}\n"
    )


def renderizar_macro_global(informe: dict) -> str:
    noticias = "\n".join(_renderizar_noticia(n) for n in informe["macro_global"])
    return f"## Macro global\n\n{noticias}"


def renderizar_modulos(informe: dict, modulos_cfg: list[dict]) -> str:
    titulos = {m["id"]: m["titulo"] for m in modulos_cfg}
    secciones = []
    for id_modulo in MODULOS_IDS:
        modulo = informe["modulos"][id_modulo]
        titulo = titulos.get(id_modulo, id_modulo)
        if modulo.get("sin_novedades"):
            secciones.append(f"## {titulo}\n\n_Sin novedades relevantes esta semana._\n")
            continue
        noticias = "\n".join(_renderizar_noticia(n) for n in modulo["noticias"])
        secciones.append(f"## {titulo}\n\n{noticias}")
    return "\n\n".join(secciones)


def renderizar_concepto_semana(informe: dict) -> str:
    concepto = informe["concepto_semana"]
    return f"## Concepto de la semana: {concepto['titulo']}\n\n{concepto['texto']}\n"


def renderizar_perspectiva(informe: dict) -> str:
    perspectiva = informe["perspectiva_largo_plazo"]
    estructural = "\n".join(f"- {linea}" for linea in perspectiva["estructural"]) or "- (nada reseñable)"
    ruido = "\n".join(f"- {linea}" for linea in perspectiva["ruido"]) or "- (nada reseñable)"
    return (
        "## Perspectiva de largo plazo\n\n"
        f"**Estructural (relevancia de años):**\n\n{estructural}\n\n"
        f"**Ruido (relevancia de días):**\n\n{ruido}\n"
    )


def renderizar_agenda(informe: dict) -> str:
    filas = ["| Fecha | Evento | Por qué importa |", "| :-- | :-- | :-- |"]
    for evento in informe["agenda"]:
        filas.append(f"| {evento['fecha']} | {evento['evento']} | {evento['por_que_importa']} |")
    tabla = "\n".join(filas)
    return f"## Agenda de la semana siguiente\n\n{tabla}\n"


def renderizar_para_profundizar(informe: dict) -> str:
    bloques = []
    for id_modulo in ("macro_global", *MODULOS_IDS):
        if id_modulo == "macro_global":
            noticias = informe["macro_global"]
            titulo = "Macro global"
        else:
            modulo = informe["modulos"][id_modulo]
            if modulo.get("sin_novedades"):
                continue
            noticias = modulo["noticias"]
            titulo = id_modulo
        if not noticias:
            continue
        enlaces = "\n".join(
            f"- {_renderizar_fuentes(n['fuentes'])}" for n in noticias
        )
        bloques.append(f"**{titulo}**\n\n{enlaces}")
    return "## Para profundizar\n\n" + "\n\n".join(bloques) + "\n"


def renderizar_indice(modulos_cfg: list[dict]) -> str:
    # Sin enlaces de anclaje: el soporte de "#ancla" dentro de un email es
    # demasiado inconsistente entre clientes de correo para prometer que
    # vayan a funcionar. Es una lista de lectura, no de navegación.
    lineas = "\n".join(f"- {m['titulo']}" for m in modulos_cfg)
    return f"**En este informe:**\n\n{lineas}\n"
