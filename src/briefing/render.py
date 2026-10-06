"""Renderiza informe.json (+ datos.json) a Markdown (sección 13 de CLAUDE.md)."""

from __future__ import annotations

from briefing.modelos import MODULOS_IDS, todas_las_noticias

AVISO_LEGAL = "Contenido informativo. No es asesoramiento financiero."

INSTRUCCION_CONTEXTO_IA = "Copia este bloque y pégalo en tu asistente de IA para profundizar."

PROMPT_SUGERIDO_IA = (
    "Usa este contexto para explicarme en detalle [tema] y qué significa para "
    "alguien que vive en España. Si algo no está en el contexto, búscalo en "
    "fuentes fiables y dime cuáles son."
)

LIMITE_CONTEXTO_IA_CARACTERES = 6000

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


def renderizar_titulo(informe: dict, nombre_newsletter: str) -> str:
    periodo = informe["periodo"]
    return f"# {nombre_newsletter} · Semana del {periodo['inicio']} al {periodo['fin']}\n"


def renderizar_contexto_ia(
    informe: dict, datos: dict, *, limite_caracteres: int = LIMITE_CONTEXTO_IA_CARACTERES
) -> str:
    """Bloque de código copiable con el contexto en bruto (sección 13).

    Solo usa resúmenes propios (ya están en informe.json, nunca texto
    copiado de un artículo) y datos con su fecha y fuente — nunca un
    número suelto sin de dónde sale.
    """
    lineas = [
        f"PROMPT SUGERIDO: {PROMPT_SUGERIDO_IA}",
        "",
        f"PERIODO: {informe['periodo']['inicio']} a {informe['periodo']['fin']}",
        "",
        "DATOS DUROS:",
    ]
    for clave, dato in sorted(datos.items()):
        lineas.append(
            f"- {clave}: {dato['valor']} {dato['unidad']} "
            f"({dato['fecha']}, fuente: {dato['fuente']})"
        )

    lineas.append("")
    lineas.append("NOTICIAS:")
    for _, noticia in todas_las_noticias(informe):
        fuentes = "; ".join(f"{f['medio']} {f['fecha']}" for f in noticia["fuentes"])
        lineas.append(
            f"- [{noticia['hilo_id']}] {noticia['titulo']} — {noticia['texto']} "
            f"(confianza: {noticia['confianza']}; fuentes: {fuentes})"
        )

    cuerpo = "\n".join(lineas)
    nota_recorte = ""
    if len(cuerpo) > limite_caracteres:
        # Mejor un contexto algo más corto que un email roto: se recorta y
        # se avisa dentro del propio bloque, en vez de fallar.
        cuerpo = cuerpo[:limite_caracteres].rstrip()
        nota_recorte = "\n\n[...contexto recortado por tamaño...]"

    return (
        "## Paquete de contexto para IA\n\n"
        f"{INSTRUCCION_CONTEXTO_IA}\n\n"
        "```\n"
        f"{cuerpo}{nota_recorte}\n"
        "```\n"
    )


def renderizar_transparencia(informe: dict) -> str:
    """Versión breve de "cómo se hizo este informe" (sección 13).

    El detalle completo (cada cambio, cada fuente descartada con su
    motivo exacto) queda en log.json; aquí solo van los números.
    """
    conteo_niveles = {1: 0, 2: 0, 3: 0}
    for _, noticia in todas_las_noticias(informe):
        for fuente in noticia["fuentes"]:
            conteo_niveles[fuente["nivel"]] += 1
    resumen_niveles = ", ".join(f"nivel {n}: {c}" for n, c in sorted(conteo_niveles.items()))

    conteo_descartes: dict[str, int] = {}
    for descartada in informe.get("fuentes_descartadas", []):
        motivo = descartada["motivo"]
        conteo_descartes[motivo] = conteo_descartes.get(motivo, 0) + 1
    resumen_descartes = (
        ", ".join(f"{motivo}: {c}" for motivo, c in conteo_descartes.items()) or "ninguna"
    )

    cambios = informe.get("cambios_verificador", [])
    primeros_cambios = "\n".join(f"- {c['noticia_id']}: {c['cambio']}" for c in cambios[:5])
    resumen_cambios = primeros_cambios or "- (sin cambios)"
    if len(cambios) > 5:
        resumen_cambios += f"\n\n_{len(cambios) - 5} cambio(s) más en log.json._"

    return (
        "## Cómo se hizo este informe\n\n"
        f"Fuentes citadas por nivel: {resumen_niveles}.\n\n"
        f"Fuentes descartadas: {resumen_descartes}.\n\n"
        f"Principales cambios del verificador:\n\n{resumen_cambios}\n\n"
        "El detalle completo queda en `log.json`.\n"
    )


def renderizar_aviso_legal() -> str:
    return f"---\n\n_{AVISO_LEGAL}_\n"


def renderizar_informe(
    informe: dict,
    datos: dict,
    datos_semana_anterior: dict | None,
    *,
    mercados_cfg: list[dict],
    modulos_cfg: list[dict],
    nombre_newsletter: str,
) -> str:
    """Ensambla el Markdown completo del email, en el orden de la sección 5."""
    secciones = [
        renderizar_titulo(informe, nombre_newsletter),
        renderizar_indice(modulos_cfg),
        renderizar_lo_esencial(informe),
        renderizar_tabla_mercados(datos, datos_semana_anterior, mercados_cfg),
        renderizar_macro_global(informe),
        renderizar_modulos(informe, modulos_cfg),
        renderizar_concepto_semana(informe),
        renderizar_perspectiva(informe),
        renderizar_agenda(informe),
        renderizar_para_profundizar(informe),
        renderizar_contexto_ia(informe, datos),
        renderizar_transparencia(informe),
        renderizar_aviso_legal(),
    ]
    return "\n\n".join(secciones) + "\n"
