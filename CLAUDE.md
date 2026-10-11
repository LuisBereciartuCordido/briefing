# Proyecto: The Macrochip — briefing semanal de economía y geopolítica

> Convenciones del proyecto y estado actual, para que las cargue Claude Code en cada sesión. El planteamiento original de este proyecto evolucionó con el desarrollo; este documento describe cómo funciona realmente hoy.

## 1. Contexto y objetivo

Newsletter semanal en español que explica, de forma veraz, clara y amena, el contexto económico y geopolítico global que mueve los mercados. El objetivo es que cualquier persona sin formación económica entienda por qué se mueven los precios de sus inversiones, sin recibir nunca consejos de inversión.

- **Público:** principalmente personas que viven en España, desde principiantes hasta inversores particulares de largo plazo.
- **Frecuencia:** semanal, el domingo por la tarde.
- **Mi perfil técnico:** estudiante de Ingeniería Informática. Manejo Python, Docker y automatización. Explica decisiones no obvias, pero no lo básico.

## 2. Restricciones clave

1. **Coste extra cero.** La redacción semanal la hace una **Routine de Claude Code en la nube** (claude.ai/code/routines), incluida en la suscripción Pro/Max. Nada de API de Anthropic en el flujo principal.
2. **Separación de responsabilidades:** lo determinista va en scripts de Python (`scripts/`, `src/briefing/`); lo que requiere criterio (investigar, redactar, verificar) lo hace Claude dentro de la Routine, siguiendo instrucciones versionadas en el repo (`prompts/`, `TAREA_SEMANAL.md`).
3. **Revisión humana obligatoria.** El flujo crea un **borrador** en Buttondown. Nunca envía directamente.
4. **Plan B preparado, no implementado.** El paso de redacción podría sustituirse en el futuro por llamadas a la API de Claude (con filtrado previo de RSS) sin tocar el resto del pipeline: el contrato real es que algo produzca `borrador.json` con la forma de `schema/informe.schema.json` — hoy lo hace la Routine siguiendo `prompts/redactor.md`, mañana podría hacerlo un script.
5. **Sin datos personales en el repo.** Nada de carteras, nombres de suscriptores ni claves. Las claves van en variables de entorno o *secrets* (en la Routine, como **API credentials**, ver sección 3).
6. **Copyright.** Nunca se copian párrafos de artículos de terceros en el informe, el JSON ni el paquete de contexto. Solo resúmenes propios, extractos muy breves cuando sea imprescindible, y enlaces.

## 3. Viabilidad (confirmada en la Fase 0)

- **Routines de Claude Code:** se crean en claude.ai/code/routines, corren como sesión completa (bash, Python, `WebSearch`/`WebFetch`) sin aprobaciones de permisos. El *environment* por defecto ("Trusted") solo permite tráfico de red a registros de paquetes. `WebSearch`/`WebFetch` no pasan por esa red bajo ningún modo (van por la conexión con Anthropic), así que la investigación del redactor funciona igual sea cual sea la red del *environment*.
- **Red del *environment* de producción: Full.** Para que `fetch_data.py`/`publish.py` lleguen a las APIs reales (BCE, Eurostat, INE, FRED, Yahoo Finance, Buttondown) hacía falta más que "Trusted". Se descartó "Custom" (listar dominios a mano) por el mantenimiento de mantenerla sincronizada con cualquier cambio de API, y se optó por "Full". El riesgo real que esto abre no es de red — es que el redactor cite una fuente con más nivel de confianza del que le corresponde (p. ej. un blog cualquiera autodeclarado nivel 1), y eso no lo arregla restringir dominios a nivel de red (`WebSearch`/`WebFetch` no pasan por ahí de todas formas). Lo arregla `validar_nivel_de_fuentes`/`avisos_fuentes_no_catalogadas` en `validate.py` (sección 10), que cruzan el nivel declarado de cada fuente contra `config/fuentes.yaml`.
- **Ramas:** una Routine empuja por defecto a una rama `claude/`-prefijada. Se usa `claude/archivo-semanal` como la rama fija donde la tarea semanal commitea (ver sección 14, es la única excepción a "Claude no commitea").
- **Buttondown:** `POST https://api.buttondown.com/v1/emails` con `Authorization: Token $BUTTONDOWN_API_KEY`, `status: "draft"`, cuerpo en Markdown — disponible en el plan gratuito.
- **APIs de datos:** BCE y Eurostat sin clave; INE sin clave; FRED con clave gratuita. Mercados: ver sección 6.
- **Secrets de la Routine:** no todas las claves se guardan igual. `BUTTONDOWN_API_KEY` va como **API credential** (cabecera `Authorization`, prefijo `Token`, host `api.buttondown.com`, ruta `/v1/emails`), porque Buttondown se autentica por cabecera. `FRED_API_KEY` va como **variable de entorno normal**, porque FRED espera la clave como parámetro de la URL (`?api_key=...`) y las API credentials solo pueden inyectar cabeceras, no *query params*.
- **Conectores:** la Routine de producción no lleva ninguno activo (se quitan los que vienen por defecto). Ninguno hace falta para este flujo, y cualquier conector activo es superficie de escritura que Claude puede usar sin preguntar durante la ejecución.

## 4. Arquitectura del repositorio

```
newsletter/
├── CLAUDE.md                  # Este archivo: convenciones + estado actual
├── TAREA_SEMANAL.md           # Instrucciones para la Routine semanal
├── README.md                  # Qué es el proyecto, el pipeline, decisiones de ingeniería
├── config/
│   ├── fuentes.yaml           # Dominios por nivel, antigüedad máxima
│   ├── modulos.yaml           # Módulos, orden, límite de palabras
│   ├── mercados.yaml          # Instrumentos de la tabla de mercados
│   ├── validacion.yaml        # Palabras de sensacionalismo/recomendación
│   └── general.yaml           # Nombre de la newsletter
├── prompts/
│   ├── redactor.md
│   ├── verificador.md
│   └── estilo.md
├── schema/
│   └── informe.schema.json
├── scripts/                   # CLIs delgadas; la lógica vive en src/briefing/
│   ├── fetch_data.py
│   ├── validate.py
│   ├── render.py
│   ├── publish.py
│   └── run_week.sh            # Encadena los 4 scripts, solo para pruebas locales
├── src/briefing/
│   ├── fuentes/                # ecb.py, eurostat.py, ine.py, fred.py, mercados.py
│   ├── modelos.py              # Dato, Informe y el resto de dataclasses
│   ├── semanas.py              # Aritmética de semana ISO
│   ├── validacion.py           # Comprobaciones sin red
│   ├── validacion_enlaces.py   # Comprobación de enlaces (con red)
│   ├── render.py
│   └── buttondown.py
├── data/
│   └── AAAA-SNN/
│       ├── datos.json
│       ├── borrador.json       # Salida del redactor
│       ├── informe.json        # Salida del verificador (validado)
│       ├── informe.md          # Email público
│       ├── transparencia.md    # "Cómo se hizo" — uso interno, no se publica
│       └── log.json
└── tests/
```

**Requisitos técnicos:** Python 3.11+, dependencias mínimas en `pyproject.toml`. Tipado, logs claros, errores explícitos — si un paso falla, el flujo se detiene y no crea el borrador. Tests para `validate.py`, `render.py`, el cliente de Buttondown, y en general para todo lo que vive en `src/briefing/`.

## 5. Contenido del informe

### Cabecera
- **Titular** (`titular.texto` + `titular.noticia_id`): una frase llamativa, tipo prensa, con la noticia más remarcable de toda la semana — no tiene por qué ser la primera de "Lo esencial". Va como encabezado principal bajo el logo (que ya lleva el nombre de la newsletter); la fecha del periodo queda como una línea pequeña debajo. "Llamativo" sigue sin significar "sensacionalista" (`prompts/estilo.md` no se relaja).

### Núcleo fijo
1. **Lo esencial:** 5 líneas como máximo.
2. **Tabla de mercados de la semana:** variación semanal de los instrumentos de `mercados.yaml`. Los números salen **solo** de `datos.json`.
3. **Macro global:** tipos de interés, inflación, crecimiento y dólar.

### Módulos (3-5 líneas cada uno, título propio)
EE. UU. · Europa · Asia y China · Emergentes · Energía y materias primas (incluye oro) · Tecnología e IA · Geopolítica y riesgos. Si un módulo no tiene novedades, se indica en una línea (`sin_novedades: true`, sin noticias).

### Cierre
4. **Concepto de la semana:** explicación en 4-5 líneas de un concepto que aparezca en el informe, con un `id` para enlazarlo en el futuro con un curso para principiantes.
5. **Perspectiva de largo plazo:** qué de esta semana es estructural (años) y qué es ruido (días).
6. **Para profundizar:** enlaces agrupados por módulo.
7. **Paquete de contexto para IA** (sección 11).
8. **Aviso fijo:** "Contenido informativo. No es asesoramiento financiero."

**Longitud del cuerpo principal (puntos 1-6):** lectura de 5 a 7 minutos. Límite de palabras por módulo en `modulos.yaml`.

**No hay agenda de la semana siguiente.** Se valoró y se descartó: el seguimiento real de una historia ya lo da `hilo_id` cuando esa historia sigue siendo noticia — una lista de fechas de reuniones y publicaciones de datos no aporta nada que un calendario económico cualquiera no dé ya, y no tenía ningún mecanismo que la conectara con el resto del informe.

**"Cómo se hizo este informe" (transparencia) no se envía a los suscriptores.** Mostrar las correcciones del verificador a todo el mundo resta fiabilidad percibida en vez de sumarla. Se sigue generando — en `data/<semana>/transparencia.md`, de uso interno — pero nunca se adjunta al borrador de Buttondown. El detalle completo, como siempre, queda también en `log.json`.

## 6. Datos duros (`fetch_data.py`)

Descarga automática, sin pasar por el modelo. Cada dato en `datos.json` lleva: valor, unidad, fecha, fuente y URL.

- **BCE:** tipo de la facilidad de depósito y EUR/USD de referencia — ECB Data Portal (SDMX 2.1, sin clave).
- **Inflación:** IPCA de la eurozona (Eurostat, JSON-stat) e IPC de España (INE). Mensuales: solo se incluyen en `datos.json` si cambiaron desde la última vez que se vieron (hasta 8 semanas atrás), para no repetir el mismo dato como "nuevo" cada semana.
- **EE. UU.:** tipo de la Fed e IPC — FRED (clave gratuita).
- **Mercados:** S&P 500 y Brent desde FRED (oficial). Nikkei 225, oro y los proxies de MSCI World/Emerging Markets/Europe (vía ETFs, ya que MSCI no licencia sus índices gratis) desde el endpoint no oficial de Yahoo Finance — sin clave, sin *challenge* anti-bot, el mismo mecanismo que usa la librería `yfinance`. **Riesgo asumido, sin fuente de respaldo:** es un endpoint no documentado que Yahoo podría cambiar sin aviso, y al correr en infraestructura cloud compartida un bloqueo de IP por otro usuario podría afectarnos. Si falla, el flujo se detiene sin publicar, igual que cualquier otro fallo — no hay una segunda fuente implementada de antemano para un problema que no ha ocurrido.
- Los clientes de BCE, Eurostat, INE y FRED (y las comprobaciones de enlaces de `validate.py`) no llevan una cabecera `User-Agent` propia: un valor genérico como `"Mozilla/5.0"` hace que algunos CDN (comprobado con `fred.stlouisfed.org`) dejen la conexión colgada en vez de responder, tratándolo como tráfico sospechoso. El user-agent por defecto de `requests` llega bien. **Yahoo Finance es la excepción deliberada:** ese endpoint sí necesita un `User-Agent` de navegador para no ser rechazado — ver `src/briefing/fuentes/mercados.py`.

## 7. Esquema de datos (`informe.schema.json`)

Decisión central de la arquitectura: el email, el paquete de contexto y la transparencia salen todos de este JSON.

```json
{
  "semana": "2026-S41",
  "periodo": {"inicio": "AAAA-MM-DD", "fin": "AAAA-MM-DD"},
  "titular": {"texto": "...", "noticia_id": "2026-S41-eeuu-01"},
  "lo_esencial": ["..."],
  "macro_global": [ /* noticia */ ],
  "modulos": {
    "eeuu": {"sin_novedades": false, "noticias": [ /* noticia */ ]}
  },
  "concepto_semana": {"id": "curva-de-tipos", "titulo": "...", "texto": "..."},
  "perspectiva_largo_plazo": {"estructural": ["..."], "ruido": ["..."]},
  "fuentes_descartadas": [{"url": "...", "motivo": "antigua | nivel 3 | contradictoria | paywall | otro"}],
  "cambios_verificador": [{"noticia_id": "...", "cambio": "...", "motivo": "..."}]
}
```

Cada **noticia**:

```json
{
  "id": "2026-S41-eeuu-01",
  "hilo_id": "fed-tipos-2026",
  "titulo": "...",
  "texto": "...",
  "por_que_importa": "...",
  "confianza": "confirmado | una_fuente | interpretacion",
  "relevancia_espana_ue": "alta | media | baja",
  "fuentes": [{"url": "...", "medio": "...", "nivel": 1, "fecha": "AAAA-MM-DD", "idioma": "en", "contexto_historico": false}],
  "cifras": [{"valor": "...", "ref_datos": "clave en datos.json o null"}]
}
```

- `hilo_id` agrupa la misma historia entre semanas. Antes de asignarlo, el redactor revisa los `hilo_id` de las últimas 4 semanas en `data/` y los reutiliza si es la misma historia.
- `cifras[].ref_datos` permite a `validate.py` comprobar los números contra `datos.json`.
- `fuentes[].contexto_historico` (opcional, por defecto `false`): marca una fuente citada deliberadamente como contexto histórico aunque su fecha caiga fuera de la ventana de antigüedad permitida (sección 10). Sin este campo no había forma de declarar esa excepción.
- `titular.noticia_id` debe apuntar a un `id` real de alguna noticia del informe; `validate.py` lo comprueba.
- El esquema exige al menos una noticia en un módulo cuando `sin_novedades` es `false` (si no hay novedades, se declara explícitamente en vez de dejar la lista vacía).

## 8. Flujo semanal (`TAREA_SEMANAL.md`)

`TAREA_SEMANAL.md` lleva las instrucciones ejecutables; este archivo solo las convenciones. La Routine la ejecuta un prompt corto: "Lee y ejecuta TAREA_SEMANAL.md", el domingo hacia mediodía (hora de Madrid). El entorno es efímero (no trae las dependencias preinstaladas), así que lo primero que hace `TAREA_SEMANAL.md` es `pip install -e .`.

1. `fetch_data.py` → `datos.json`. Si falla, detenerse.
2. **Redacción, un módulo cada vez:** investigar con búsqueda web respetando `fuentes.yaml`, escribir cada módulo en `borrador.json` siguiendo `prompts/redactor.md` y `prompts/estilo.md`.
3. **Unión:** titular, lo esencial, macro global, concepto de la semana, perspectiva de largo plazo. Eliminar duplicados entre módulos.
4. **Verificación en frío:** releer `borrador.json` como revisor escéptico (`prompts/verificador.md`), reabriendo las fuentes. Resultado: `informe.json` con `cambios_verificador`.
5. `validate.py`, máximo 2 intentos. Si persiste el error, detenerse sin publicar (queda en `log.json`).
6. `render.py` → `informe.md` (público) + `transparencia.md` (interno).
7. `publish.py` → borrador en Buttondown, asunto `"{NOMBRE}: {titular}"`.
8. Commit de `data/<semana>/` a la rama `claude/archivo-semanal` — la única vez que Claude commitea y pushea directamente (sección 14).
9. Resumen breve: módulos cubiertos, fuentes, avisos del validador, enlace al borrador.

## 9. Prompts de criterio

El contenido completo vive en sus propios archivos — no se duplica aquí para que no se desincronicen:

- **`prompts/redactor.md`:** reglas de fuentes por nivel (ver `config/fuentes.yaml`), prioridades de selección, reglas de contenido (hechos vs. interpretación, nada de predicciones ni recomendaciones), cómo reutilizar `hilo_id`, y cómo escribir el titular.
- **`prompts/verificador.md`:** la lista de comprobaciones del revisor escéptico — fuentes, cifras, independencia, interpretación vs. hecho, fechas, plagio.
- **`prompts/estilo.md`:** tono, explicación de términos técnicos, prohibición de sensacionalismo, emojis de confianza (✅/⚠️/💬). Comparten este archivo redactor y verificador.

## 10. Validaciones deterministas (`validate.py`)

Errores que bloquean la publicación:
- `informe.json` no cumple el esquema (incluye: `titular.noticia_id` inexistente, módulo `sin_novedades: false` sin noticias).
- `confianza = confirmado` con menos de 2 fuentes de dominios distintos y ninguna catalogada como nivel 1 en `config/fuentes.yaml`. Un dominio no catalogado no cuenta como nivel 1 aunque la propia noticia lo declare así — tiene que ser un dominio *realmente* catalogado.
- El nivel que declara una fuente no coincide con el nivel catalogado para su dominio en `config/fuentes.yaml` (la comprobación es por subdominio: `ecb.europa.eu` coincide con el catalogado `europa.eu`).
- Un enlace que no responde tras reintentos. Si un medio bloquea bots o tiene paywall, es un **aviso**, no un error.
- Una cifra con `ref_datos` que no coincide con `datos.json`.
- Una fuente más antigua que `antiguedad_maxima_dias` (`config/fuentes.yaml`, 10 por defecto) **respecto al cierre del periodo** y sin `contexto_historico: true`. No exige que la fecha caiga dentro del periodo exacto: una noticia del lunes puede citar perfectamente un artículo de días antes.
- Una noticia con palabras de `config/validacion.yaml` (sensacionalismo o recomendación).

Avisos (no bloquean): módulo que supera su límite de palabras; más del 50 % de las fuentes de un solo medio; módulo sin ninguna fuente de nivel 1 o 2; un dominio citado que no está catalogado en `config/fuentes.yaml` (puede ser una fuente nueva legítima — el aviso es para revisarla y, si corresponde, añadirla); `titular.texto` de más de 60 caracteres (se reutiliza tal cual como asunto del email y se trunca en varios clientes de correo); `concepto_semana.texto` de más de 120 palabras (sección 5: "4-5 líneas").

`validate.py` escribe siempre sus hallazgos en `data/<semana>/log.json`, bajo la clave `"validacion"`, sin pisar el resto de contenido que el archivo ya tuviera. `fuentes_descartadas` y `cambios_verificador` no se duplican ahí: ya son campos de `informe.json`, y de ahí los lee `render.py` para `transparencia.md`.

## 11. Renderizado del email (`render.py`)

- Markdown limpio, legible en móvil.
- Cabecera: logo (`config/general.yaml:logo_url`, subido una sola vez a Buttondown vía `POST /v1/images`; el logo ya lleva el nombre de la newsletter en la propia imagen, no se repite como texto aparte) + `titular` como encabezado principal + fecha del periodo en una línea pequeña debajo. El logo va con `<img width="...">` explícito (no la sintaxis Markdown de imagen) y a alta resolución: algunos clientes de correo lo estiraban más allá de su tamaño natural y se pixelaba (comprobado en un borrador real).
- Índice de módulos sin enlaces de ancla (el soporte de `#ancla` dentro de un email es demasiado inconsistente entre clientes de correo).
- Mercados: lista (no tabla) desde `datos.json`, con variación semanal calculada contra la semana ISO anterior (o `—` si no hay dato previo). Es una lista a propósito: una tabla Markdown se lee peor en móvil con 3 columnas, y el editor "fancy" de Buttondown pierde la cabecera de las tablas al tocarlas — una lista no tiene cabecera que perder. La variación va en verde o rojo (subida/bajada) con un `<span style="color:...">` suelto dentro del Markdown — Buttondown lo acepta sin pasar todo el email a HTML ("All HTML is valid Markdown", docs.buttondown.com/using-markdown).
- Enlaces de fuente en línea tras cada afirmación, agrupados también en "Para profundizar".
- **Paquete de contexto para IA**, en un bloque de código copiable: instrucción + prompt sugerido + periodo + datos duros con fecha/fuente + cada noticia en forma compacta (título, resumen propio, confianza, fuentes, `hilo_id`). Nunca texto copiado de artículos. Si supera `LIMITE_CONTEXTO_IA_CARACTERES`, se recorta con un aviso dentro del propio bloque.
- Aviso legal fijo al final.
- `transparencia.md` se escribe aparte (ver sección 5) con `renderizar_transparencia()`: fuentes por nivel, descartes por motivo, y los primeros 5 cambios del verificador (el resto, en `log.json`).

**Publicar en Buttondown (`publish.py`):** fuerza el modo Markdown explícitamente (`<!-- buttondown-editor-mode: plaintext -->`) en vez de confiar en la autodetección. Solo sabe crear borradores (`status: "draft"`) — nunca envía.

> **Cuidado al revisar el borrador ya creado:** abrir el borrador en el editor "fancy" (visual) de Buttondown y hacer clic dentro del cuerpo reconvierte el Markdown a HTML (comprobado) — con el riesgo de que algo se reformatee sin que lo pidas. Revísalo en una vista de solo lectura si puedes; si necesitas editarlo, comprueba el resultado antes de enviarlo.

## 12. Fuera de alcance por ahora (diseña sin cerrar estas puertas)

- Curso de conceptos para principiantes (`concepto_semana.id` servirá para enlazarlo).
- Páginas de hilos de historia y "ponerme al día" a partir del archivo (`hilo_id` lo prepara).
- Módulos elegidos por cada lector.
- Servidor MCP con el archivo.
- Redacción por API (Plan B de la sección 2).

## 13. Cómo seguimos trabajando

1. Para una funcionalidad o cambio nuevo: plan corto si hace falta decidir algo no obvio, implementación por partes pequeñas con tests, siguiendo las reglas de git de la sección 14.
2. Antes de un cambio que afecte al flujo real, probarlo en local (`scripts/run_week.sh`, o los scripts por separado) antes de depender de que lo ejecute la Routine.
3. Si una instrucción de este documento resulta imposible, contradictoria o claramente mejorable al implementarla: decirlo antes de implementarla, no en silencio.

## 14. Git y commits

Poca experiencia con git. **El dueño del proyecto hace todos los commits, el push y los Pull Requests — Claude nunca ejecuta `git commit`, `git push` ni `gh pr create`.** El trabajo de Claude es generar el código ya listo para commitear y explicarlo.

**División del trabajo por funcionalidad**
- Unidades pequeñas, cada una equivalente a un commit. Una unidad = un cambio lógico; si hace falta un "y" para describirla, son dos.
- Para cada unidad: indicar en qué **rama** trabajar (`main` siempre con tests en verde y sin código a medias), dejar los archivos listos, correr los tests, y antes del commit dar una explicación: **qué es** (archivos y qué hacen), **cómo funciona** (la lógica clave), **qué aporta** (a qué parte de este documento corresponde).
- Después, proponer el mensaje de commit (Conventional Commits, tipo en inglés y descripción en español, imperativo, menos de 72 caracteres):
  - `feat: añade descarga del IPC del INE`
  - `fix: corrige el redondeo del EUR/USD en la tabla`
  - `test: cubre los enlaces caídos en validate.py`
  - `docs: explica cómo crear la Routine`
  - `refactor:`, `chore:` (dependencias, configuración)
  - `data(2026-S41): informe semanal` para los commits de la tarea programada
- Si el porqué no es obvio, sugerir también un cuerpo para el commit.
- Al terminar una rama, avisar de que está lista para el Pull Request y proponer el resumen de qué cambia y cómo se ha probado.
- **Excepción:** los commits de datos semanales de la Routine (nadie presente para commitear) — esa sesión sí commitea y pushea sola, a `claude/archivo-semanal` (sección 8).

**Seguridad**
- Nunca generar ni dejar en el working tree claves ni `.env`. El `.gitignore` incluye `.env`, `__pycache__/`, entornos virtuales y archivos del sistema.
- Antes de decir que algo está listo para commitear, revisar el contenido en busca de claves o datos personales.
- Si alguna vez se sube una clave por error: avisar de inmediato, hay que revocarla.

**Nunca sin permiso explícito**
- `git push --force`, `git reset --hard`, reescribir historial publicado o borrar ramas remotas. En general, ningún comando de git que modifique el repositorio salvo lectura (`status`, `diff`, `log`).

## Configuración

- `{NOMBRE}`: **"The Macrochip"** (`config/general.yaml`).
- Secrets: `BUTTONDOWN_API_KEY`, `FRED_API_KEY`. En el *environment* de la Routine (plan Pro/Max), como **API credentials** en vez de variables de entorno planas, para que no sean visibles dentro de la sesión.
