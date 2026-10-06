# Proyecto: Briefing semanal de economía y geopolítica

> Prompt para Claude Code. Léelo entero antes de escribir código. **Empieza por la Fase 0 y no avances sin mi confirmación.**

## 1. Contexto y objetivo

Quiero una newsletter semanal en español que explique, de forma veraz, clara y amena, el contexto económico y geopolítico global que mueve los mercados. El objetivo es que cualquier persona sin formación económica entienda por qué se mueven los precios de sus inversiones, sin recibir nunca consejos de inversión.

- **Público:** principalmente personas que viven en España, desde principiantes hasta inversores particulares de largo plazo.
- **Frecuencia:** semanal, el domingo por la tarde.
- **Primeros lectores:** yo y un amigo. Diseña pensando en que pueda crecer.
- **Mi perfil técnico:** soy estudiante de Ingeniería Informática. Manejo Python, Docker y automatización. Explica decisiones no obvias, pero no lo básico.

## 2. Restricciones clave

1. **Coste extra cero.** La redacción semanal la hará una **tarea programada de Claude Code en la web** (claude.ai/code/scheduled), incluida en mi suscripción. **No uses la API de Anthropic** en el flujo principal ni necesites una clave de API de Anthropic.
2. **Separación de responsabilidades:**
   - Lo **determinista** va en scripts de Python: descarga de datos, validación, renderizado y publicación.
   - Lo que requiere **criterio** (investigar, redactar, verificar) lo hace Claude dentro de la tarea programada, siguiendo instrucciones versionadas en el repo.
3. **Revisión humana obligatoria.** El flujo crea un **borrador** en Buttondown. Nunca envía directamente. Yo lo apruebo y lo envío.
4. **Plan B preparado.** El paso de redacción debe estar detrás de una interfaz clara, de modo que en el futuro pueda sustituirse por llamadas a la API de Claude (con filtrado previo de RSS) cambiando solo ese paso. No lo implementes ahora: deja el punto de extensión y documéntalo.
5. **Sin datos personales en el repo.** Nada de carteras, nombres de suscriptores ni claves. Las claves van en variables de entorno o *secrets*.
6. **Copyright.** Nunca copies párrafos de artículos de terceros en el informe, el JSON ni el paquete de contexto. Solo resúmenes propios, extractos muy breves cuando sea imprescindible, y enlaces.

## 3. Fase 0: verificación de viabilidad (hazla primero)

Antes de construir nada, investiga y verifica en la documentación oficial actual (no te fíes de tu memoria) y dame un informe breve:

1. **Tareas programadas de Claude Code en la web:**
   - Cómo se crean y configuran.
   - Qué herramientas tienen disponibles (búsqueda web, lectura de páginas, bash, Python).
   - Si el entorno en la nube **tiene acceso de red saliente** a: la API de Buttondown, las APIs de datos de la sección 6 y webs de medios.
   - Cómo se configuran **variables de entorno / secrets** en ese entorno.
   - Límites de duración, uso de cuota y comportamiento ante errores.
2. **Ramas:** por lo que sé, las tareas programadas solo pueden hacer push por defecto a ramas con prefijo `claude/`. Confírmalo y propón cómo guardar el archivo histórico semanal teniendo esto en cuenta (por ejemplo, una rama `claude/archivo` que yo fusiono periódicamente, o cambiar ese permiso si es seguro).
3. **API de Buttondown:** endpoints actuales para crear un email como borrador, autenticación, formato del cuerpo (Markdown) y si el plan gratuito permite todo esto. Consulta su documentación, no la supongas.
4. **APIs de datos de la sección 6:** confirma que funcionan sin clave o con clave gratuita, y su formato.

Si algo bloquea la Opción 1 (por ejemplo, sin red saliente o sin búsqueda web), detente y explícame alternativas antes de seguir.

## 4. Arquitectura del repositorio (propuesta, ajústala si lo justificas)

```
briefing/
├── CLAUDE.md                  # Convenciones del proyecto para Claude Code (git, estilo de código, comandos)
├── TAREA_SEMANAL.md           # Instrucciones para la tarea programada semanal (sección 8)
├── README.md                  # Instalación, configuración, cómo crear la tarea programada
├── config/
│   ├── fuentes.yaml           # Fuentes por niveles, dominios permitidos, feeds RSS
│   ├── modulos.yaml           # Módulos, orden, límite de palabras por módulo
│   └── mercados.yaml          # Instrumentos de la tabla de mercados
├── prompts/
│   ├── redactor.md            # Sección 9
│   ├── verificador.md         # Sección 10
│   └── estilo.md              # Sección 11 (compartido por ambos)
├── schema/
│   └── informe.schema.json    # Sección 7
├── scripts/
│   ├── fetch_data.py          # Descarga los datos duros → datos.json
│   ├── validate.py            # Comprobaciones deterministas (sección 12)
│   ├── render.py              # JSON → email en Markdown (sección 13)
│   ├── publish.py             # Crea el borrador en Buttondown
│   └── run_week.sh            # Orquestación de los pasos deterministas
├── src/briefing/              # Código compartido (clientes, modelos, utilidades)
├── data/
│   └── AAAA-SNN/              # Una carpeta por semana ISO
│       ├── datos.json
│       ├── borrador.json      # Salida del redactor
│       ├── informe.json       # Salida del verificador (validado)
│       ├── informe.md         # Email renderizado
│       └── log.json           # Fuentes descartadas, cambios del verificador, errores
└── tests/
```

**Requisitos técnicos:**
- Python 3.11 o superior y dependencias mínimas, fijadas en `requirements.txt` o `pyproject.toml`.
- Tipado, logs claros y errores explícitos. Si un paso falla, el flujo se detiene con un mensaje entendible y **no crea el borrador**.
- Tests para `validate.py`, `render.py` y el cliente de Buttondown (con mocks).
- Ejecutable también en local con un comando, para pruebas.

## 5. Contenido del informe

### Cabecera
0. **Titular:** una frase llamativa, tipo prensa, que recoge la noticia más remarcable de la semana entre todas las que hay en el informe (no necesariamente la de "Lo esencial" #1). Va debajo del nombre de la newsletter, como un subtítulo. Nada de sensacionalismo (sigue valiendo `prompts/estilo.md`): "llamativo" es "da ganas de leer", no "exagerado". Guarda también a qué noticia se refiere (`noticia_id`), para poder enlazarla.

### Núcleo fijo (siempre)
1. **Lo esencial:** 5 líneas como máximo.
2. **Tabla de mercados de la semana:** variación semanal de los instrumentos de `mercados.yaml`. Propuesta inicial: S&P 500, MSCI World, MSCI Emerging Markets, MSCI Europe (o Euro Stoxx 50), Nikkei 225 o MSCI Japan, oro, Brent y EUR/USD. Los números salen **solo** de `datos.json`.
3. **Macro global:** tipos de interés, inflación, crecimiento y dólar.

### Módulos (cada uno de 3 a 5 líneas, con título propio)
EE. UU. · Europa · Asia y China · Emergentes · Energía y materias primas (incluye oro) · Tecnología e IA · Geopolítica y riesgos.

Si un módulo no tiene novedades relevantes, se indica en una línea.

### Cierre
4. **Concepto de la semana:** explicación en 4-5 líneas de un concepto que aparezca en el informe. Guarda un identificador del concepto para enlazarlo en el futuro con el curso para principiantes.
5. **Perspectiva de largo plazo:** qué de esta semana tiene relevancia estructural (años) y qué es ruido (días).
6. **Para profundizar:** enlaces agrupados por módulo.
7. **Paquete de contexto para IA** (sección 13).
8. **Aviso fijo:** "Contenido informativo. No es asesoramiento financiero."

**Longitud del cuerpo principal (puntos 1 a 6):** lectura de 5 a 7 minutos. Pon un límite de palabras por módulo en `modulos.yaml`.

> **Decisión de producto (revisada tras la primera prueba real, sección 15.4):**
> - **Sin agenda de la semana siguiente.** Se quita del informe: no aportaba suficiente valor frente a su coste de mantenimiento, y el dueño del proyecto no le veía el sentido al verlo con contenido real.
> - **"Cómo se hizo este informe" deja de ir en el email que reciben los suscriptores.** Mostrar las correcciones del verificador a todo el mundo da sensación de "esto tiene fallos", lo contrario de lo que se busca (transmitir fiabilidad). Sigue generándose — el dueño del proyecto sí quiere verlo — pero en un archivo aparte de solo lectura interna (`data/<semana>/transparencia.md`), no en `informe.md`. El detalle completo, como siempre, queda también en `log.json`.

## 6. Datos duros (`fetch_data.py`)

Descarga automática, sin pasar por el modelo. Prioriza fuentes oficiales sin clave.

- **Eurozona y BCE:** tipos del BCE y EUR/USD de referencia (API del ECB Data Portal).
- **Inflación:** IPCA de la eurozona (Eurostat) e **IPC de España (API del INE)**. Son mensuales: inclúyelos solo si hubo publicación en el periodo, e indica siempre la fecha del dato.
- **EE. UU.:** tipos de la Fed e inflación (por ejemplo FRED, que requiere una clave gratuita: usa un secret).
- **Mercados:** cierres semanales de los instrumentos de `mercados.yaml`. Investiga qué fuente gratuita es fiable y estable. Si solo hay opciones no oficiales, elige la más robusta, documenta el riesgo y añade una de respaldo.

Cada dato en `datos.json` lleva: valor, unidad, fecha del dato, fuente y URL.

> **Desviación registrada (rama `feat/fetch-data`):** para S&P 500, Brent y Fed se usa FRED (oficial); para EUR/USD y tipos del BCE, el ECB Data Portal (oficial). Para Nikkei 225, oro y los proxies de MSCI (World/EM/Europe vía ETFs) **no existe fuente oficial gratuita**. La candidata inicial, Stooq, quedó descartada en la práctica: ahora exige superar un *challenge* anti-bot en JavaScript incluso en sus endpoints CSV, incompatible con una petición HTTP simple desde un script. Se usa en su lugar el endpoint no oficial de Yahoo Finance (`query1.finance.yahoo.com/v8/finance/chart/...`), el mismo mecanismo que usa la librería `yfinance`: sin clave, sin *challenge*, datos de mercado reales. Riesgo: es un endpoint no documentado que Yahoo podría cambiar sin aviso, y al correr en infraestructura cloud compartida de Claude Code, un bloqueo de IP por abuso de otro usuario podría afectarnos sin que lo controlemos. **No se añade una fuente de respaldo** (desviación explícita de "añade una de respaldo" de esta sección): no hay ninguna alternativa gratuita y fiable verificada hoy, y construir un segundo cliente para un fallo que no ha ocurrido sería la abstracción prematura que este proyecto quiere evitar. Si `fetch_data.py` falla por esto, el flujo se detiene sin publicar (igual que cualquier otro fallo) y se revisará con datos reales del problema.

## 7. Esquema de datos (`informe.schema.json`)

Esta es la decisión más importante de la arquitectura. Todo (email, paquete de contexto, transparencia y, en el futuro, hilos y "ponerme al día") sale de este JSON. Propuesta mínima, amplíala si hace falta:

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
  "fuentes": [{"url": "...", "medio": "...", "nivel": 1, "fecha": "AAAA-MM-DD", "idioma": "en"}],
  "cifras": [{"valor": "...", "ref_datos": "clave en datos.json o null"}]
}
```

- `hilo_id` agrupa la misma historia entre semanas. Antes de asignarlo, el redactor debe revisar los `hilo_id` de las últimas 4 semanas en `data/` y reutilizarlos cuando sea la misma historia.
- `cifras` permite que `validate.py` compruebe los números contra `datos.json`.

> **Desviación registrada (rama `feat/validate`):** cada fuente puede llevar también `"contexto_historico": true|false` (por defecto `false`). Sin este campo, la regla de la sección 12 ("una fuente con fecha fuera del periodo **y sin marca de contexto histórico**") era imposible de comprobar — no había forma de que el redactor declarase esa excepción en ningún sitio del esquema original. Es opcional y no afecta a ningún informe existente.

## 8. Flujo semanal (`TAREA_SEMANAL.md`, para la tarea programada)

`CLAUDE.md` se carga automáticamente en cada sesión de Claude Code, así que **no** debe contener las instrucciones semanales: solo las convenciones del proyecto (sección 16). La tarea programada se configura con un prompt corto del tipo "Lee y ejecuta TAREA_SEMANAL.md".

La tarea programada se ejecuta el **domingo hacia mediodía (hora de Madrid)**, para que yo revise el borrador y lo envíe por la tarde. Pasos:

1. Ejecutar `fetch_data.py` → `datos.json`. Si falla, detenerse.
2. **Redacción, un módulo cada vez:** para cada módulo de `modulos.yaml`, investigar con búsqueda web respetando `fuentes.yaml` y escribir sus noticias en `borrador.json` siguiendo `prompts/redactor.md` y `prompts/estilo.md`. Tratar cada módulo por separado garantiza una cobertura equilibrada.
3. **Unión:** redactar "Titular", "Lo esencial", "Macro global", "Concepto de la semana" y "Perspectiva de largo plazo", y eliminar duplicados entre módulos. El titular recoge la noticia más remarcable del conjunto, no necesariamente una de "Lo esencial".
4. **Verificación en frío:** releer `borrador.json` como revisor escéptico siguiendo `prompts/verificador.md`. Abrir de nuevo las fuentes para comprobar cada afirmación (no fiarse del recuerdo de la redacción). Resultado: `informe.json` con `cambios_verificador`.
5. Ejecutar `validate.py`. Si hay errores, corregirlos y repetir (máximo 2 intentos). Si persisten, detenerse sin publicar y dejar el error en `log.json`.
6. Ejecutar `render.py` → `informe.md` (el email público) y `transparencia.md` (solo para uso interno, no se publica).
7. Ejecutar `publish.py` → **borrador** en Buttondown con el asunto: "{NOMBRE}: {titular}".
8. Commit de la carpeta de la semana según la estrategia de ramas acordada en la Fase 0.
9. Terminar con un resumen breve: módulos cubiertos, número de fuentes, avisos del validador y enlace al borrador.

## 9. `prompts/redactor.md`

```
Eres un analista que redacta un resumen semanal de economía y geopolítica en español. Lo leen personas que viven en España, curiosas pero sin formación económica, que quieren entender el contexto global que mueve los mercados. No buscan consejos de inversión.

FECHA: {fecha}. PERIODO: {inicio} a {fin}.
DATOS DUROS: datos.json. Úsalos tal cual, sin redondear distinto ni modificarlos.

REGLAS DE FUENTES
- Nivel 1 (primarias): bancos centrales (BCE, Fed, BoJ, PBoC...), FMI, BIS, OCDE, Eurostat, BLS, INE, organismos oficiales y comunicados oficiales.
- Nivel 2 (agencias y prensa económica reconocida): Reuters, Bloomberg, Financial Times, The Economist, Wall Street Journal, Nikkei Asia, Caixin, Expansión, Cinco Días, y similares.
- Nivel 3 (opinión y análisis): solo como contexto y siempre marcado como interpretación.
- Usa las mejores fuentes en cualquier idioma. El informe siempre se escribe en español.
- Todo dato numérico sale de datos.json o de una fuente de nivel 1, o de nivel 2 que cite la primaria.
- Todo hecho de actualidad necesita al menos 2 fuentes independientes. Varios medios que repiten el mismo teletipo cuentan como una sola. Con una sola fuente, confianza = "una_fuente".
- Si dos fuentes se contradicen, explica la discrepancia. No elijas una en silencio.
- Ignora artículos de más de 10 días, salvo como contexto histórico declarado.
- Si no hay información fiable sobre algo, dilo. Nunca rellenes.
- Registra en fuentes_descartadas lo que descartes y por qué.

PRIORIDADES
- Lo principal es el contexto global: selecciona por impacto en la economía y los mercados mundiales.
- Si dos noticias tienen una relevancia global parecida, prioriza la de más impacto en España o la UE.
- En el módulo de Europa incluye las políticas europeas con impacto económico (BCE, aranceles y comercio, presupuestos y gasto de los grandes países) y la inflación española frente a la de la eurozona cuando haya dato nuevo.
- Nunca antepongas una noticia local a una global más importante.

REGLAS DE CONTENIDO
- Separa hechos de interpretación. Para causas de movimientos de mercado usa "pudo influir" o "se asocia con", nunca "causó".
- No predigas precios. No des recomendaciones de compra, venta ni asignación.
- Cada noticia termina con "Por qué importa": su conexión con la economía o los ahorros de una persona normal, sin recomendar nada.

Sigue además prompts/estilo.md. Escribe la salida en el formato de schema/informe.schema.json.
```

## 10. `prompts/verificador.md`

```
Eres un revisor escéptico. Recibes borrador.json, datos.json y acceso a las fuentes citadas. Vuelve a abrir las fuentes y no te fíes de lo que recuerdes de la redacción.

Para cada noticia comprueba:
1. ¿Las fuentes citadas dicen realmente eso? Si no, corrige o elimina.
2. ¿Las cifras coinciden exactamente con la fuente o con datos.json?
3. ¿Un hecho de actualidad tiene 2 fuentes independientes? Si no, confianza = "una_fuente".
4. ¿Hay una interpretación presentada como hecho? Reescríbela ("pudo influir") con confianza = "interpretacion".
5. ¿Hay predicciones de precios o recomendaciones? Elimínalas.
6. ¿Las fechas de las fuentes están dentro del periodo?
7. ¿Hay texto copiado de un artículo? Parafraséalo.
8. Mantén el estilo cercano y claro de prompts/estilo.md. Si reescribes, usa el mismo tono y explica cualquier término técnico nuevo.

Devuelve informe.json con el mismo esquema y registra cada cambio en cambios_verificador.
```

## 11. `prompts/estilo.md`

```
- Escribe para alguien curioso e inteligente, sin formación en economía. Si un estudiante de bachillerato no entendería una frase, reescríbela.
- Tono profesional pero cercano y moderno, como un amigo que sabe del tema. Tutea al lector.
- Explica cada término técnico la primera vez que aparece, en la misma frase. Ejemplo: "el BCE (el banco central de la zona euro, que fija el precio del dinero)".
- Usa comparaciones cotidianas cuando ayuden.
- Empieza cada módulo por lo más interesante o sorprendente, no con relleno.
- Frases cortas. Párrafos de 2 o 3 líneas como máximo.
- Prohibido el sensacionalismo: nada de "desplome histórico", "pánico" o "lo que nadie te cuenta" salvo que los datos lo justifiquen literalmente. Interesante no es alarmante.
- Etiquetas de confianza al final de la frase: ✅ confirmado, ⚠️ una sola fuente, 💬 interpretación u opinión.
```

## 12. Validaciones deterministas (`validate.py`)

Errores que bloquean la publicación:
- `informe.json` no cumple el esquema.
- Una noticia sin fuentes, o con `confianza = confirmado` y menos de 2 fuentes independientes (dominios distintos) sin ninguna de nivel 1.
- Un enlace que no responde (comprobación HTTP con reintentos y *timeout*). Si un medio bloquea bots o tiene paywall, avisar en vez de bloquear, y registrarlo.
- Una cifra con `ref_datos` que no coincide con `datos.json`.
- Una fuente con fecha fuera del periodo y sin marca de contexto histórico.
- Una noticia con palabras de la lista de sensacionalismo o recomendación (lista configurable en YAML).

Avisos (no bloquean, pero aparecen en el resumen):
- Módulo que supera su límite de palabras.
- Más del 50 % de las fuentes de un solo medio.
- Módulo sin ninguna fuente de nivel 1 o 2.

> **Aclaración (rama `feat/validate`):** `fuentes_descartadas` y `cambios_verificador` ya son campos de `informe.json` (sección 7) — eso es lo que lee `render.py` para la transparencia breve. `validate.py` **no** los duplica en `log.json`: solo escribe sus propios hallazgos (`errores`/`avisos` de esta sección) bajo la clave `"validacion"`, sin pisar el resto de contenido que `log.json` ya tuviera. Si una rama futura (verificador, orquestación) también escribe en `log.json`, que añada su propia clave en vez de sobrescribir el archivo entero.

## 13. Renderizado del email (`render.py`)

- Markdown limpio, compatible con Buttondown y legible en móvil.
- **Título llamativo:** nombre de la newsletter + el `titular` del informe como subtítulo, no una fecha mecánica. La fecha del periodo queda como una línea pequeña debajo.
- Índice al principio con los módulos.
- Tabla de mercados generada desde `datos.json`.
- Enlaces de fuente en línea tras cada afirmación y agrupados en "Para profundizar".
- **Paquete de contexto para IA**, al final, dentro de un bloque de código copiable. Contenido:
  - Instrucción breve para el lector: "Copia este bloque y pégalo en tu asistente de IA para profundizar".
  - Un prompt sugerido, por ejemplo: "Usa este contexto para explicarme en detalle [tema] y qué significa para alguien que vive en España. Si algo no está en el contexto, búscalo en fuentes fiables y dime cuáles son".
  - Periodo, datos duros con fecha y fuente.
  - Cada noticia en forma compacta: título, resumen propio, confianza, fuentes (URL y fecha) y `hilo_id`.
  - Sin texto copiado de artículos.
  - Tamaño razonable: si supera un límite configurable, resumir más.
- Aviso legal fijo al final.

**"Cómo se hizo este informe" (transparencia) NO va en `informe.md`** (decisión de producto, sección 5): mostrar las correcciones del verificador a todos los suscriptores resta fiabilidad percibida en vez de sumarla. En su lugar, `render.py` escribe esa misma sección (número de fuentes por nivel, descartes por motivo, cambios del verificador) en un archivo separado, `data/<semana>/transparencia.md`, de uso interno — nunca se publica ni se adjunta al borrador de Buttondown. El detalle completo, como siempre, queda también en `log.json`.

> **Hallazgo real (sección 15.4, prueba en local):** `publish.py` crea el borrador con el Markdown exacto que generó `render.py` — lo confirmamos leyendo el borrador recién creado vía la API, con la tabla de mercados intacta. Pero **abrir el borrador en el editor "fancy" (visual) de Buttondown y hacer clic dentro del cuerpo reconvierte el Markdown a HTML y pierde la fila de cabecera de las tablas** (comprobado: la fila "Instrumento / Valor / Variación semanal" desaparece por completo). Al revisar el borrador cada semana antes de enviarlo: evita entrar al editor de edición de texto si puedes revisarlo en una vista de solo lectura/preview; si necesitas editarlo, comprueba después que las tablas siguen teniendo su fila de cabecera antes de pulsar enviar. Esto hay que explicarlo en el README (sección 15.5).

## 14. Fuera de alcance por ahora (diseña sin cerrar estas puertas)

- Curso de conceptos para principiantes (el `concepto_semana.id` servirá para enlazarlo).
- Páginas de hilos de historia y "ponerme al día" a partir del archivo (el `hilo_id` lo prepara).
- Módulos elegidos por cada lector.
- Servidor MCP con el archivo.
- Redacción por API (Plan B de la sección 2).

## 15. Forma de trabajar

1. Haz la **Fase 0** y dame el informe. Espera mi confirmación.
2. Propón un **plan de implementación** por pasos, con lo que cambiarías de esta especificación y por qué. Espera mi confirmación.
3. Implementa por partes pequeñas, con tests, siguiendo las reglas de git de la sección 16.
4. Hazme una **ejecución de prueba completa en local**, creando un borrador real en Buttondown, antes de configurar la tarea programada.
5. Escribe en el `README.md` cómo crear la tarea programada, qué *secrets* configurar y cómo cambiar módulos, fuentes e instrumentos.
6. Si una instrucción de esta especificación es imposible, contradictoria o claramente mejorable, dímelo antes de implementarla.

## 16. Git y commits

Tengo poca experiencia con git. **Yo hago todos los commits, el push y los Pull Requests — tú nunca ejecutas `git commit`, `git push` ni `gh pr create`.** Tu trabajo es generar el código ya listo para commitear y explicármelo. Copia estas reglas en `CLAUDE.md` para que se apliquen en todas las sesiones.

**División del trabajo por funcionalidad**
- Divide la implementación en unidades pequeñas, cada una equivalente a un commit (p. ej. "cliente HTTP de Buttondown", "validación de cifras contra datos.json", "renderizado de la tabla de mercados"). Una unidad = un cambio lógico; si necesitarías un "y" para describirla, sepárala en dos.
- Para cada unidad: indícame en qué **rama** trabajar (`feat/fase-0-viabilidad`, `feat/fetch-data`, `fix/validacion-enlaces`...; `main` siempre debe quedar con tests en verde y sin código a medias), crea o deja los archivos listos con `Write`/`Edit`, corre los tests si existen, y **antes de que yo commitee** dame una explicación que cubra:
  - **Qué es:** qué archivo(s) cambian y qué hacen.
  - **Cómo funciona:** la lógica o el flujo clave, sin explicar lo obvio.
  - **Qué aporta:** a qué funcionalidad de la spec corresponde y cómo encaja en la arquitectura del repo (sección 4).
- Después de tu explicación, propónme el mensaje de commit (Conventional Commits, tipo en inglés y descripción en español, imperativo, menos de 72 caracteres) para que lo use tal cual o lo ajuste:
  - `feat: añade descarga del IPC del INE`
  - `fix: corrige el redondeo del EUR/USD en la tabla`
  - `test: cubre los enlaces caídos en validate.py`
  - `docs: explica cómo crear la tarea programada`
  - `refactor:`, `chore:` (dependencias, configuración)
  - `data(2026-S41): informe semanal` para los commits de la tarea programada
- Si el porqué de un cambio no es obvio, sugiéreme también un cuerpo para el commit explicando el motivo.
- Cuando termines una rama completa, dime que está lista para que yo abra el Pull Request, y propónme el resumen de qué cambia y cómo se ha probado para pegarlo en la descripción del PR. **Yo lo reviso y lo fusiono**; nunca fusiones a `main` por tu cuenta (de hecho, nunca deberías necesitar hacerlo, porque no ejecutas el merge).
- Los commits de datos semanales (de la tarea programada en la nube) son la única excepción: como se generan en una sesión en la que no estoy presente para commitear yo, esa sesión sí hace su propio commit/push siguiendo la estrategia de ramas acordada en la Fase 0; documenta esto explícitamente en `TAREA_SEMANAL.md`.

**Seguridad**
- Nunca generes ni dejes en el working tree claves ni `.env`. El `.gitignore` debe incluir `.env`, `__pycache__/`, entornos virtuales y archivos del sistema.
- Antes de decirme que algo está listo para commitear, revisa tú mismo el contenido de los archivos nuevos o modificados en busca de claves o datos personales. Si detectas algo sospechoso, para y avísame en vez de darme la explicación de commit.
- Si alguna vez se sube una clave por error, avísame de inmediato: hay que revocarla, no basta con borrarla del historial.

**Nunca sin mi permiso explícito**
- `git push --force`, `git reset --hard`, reescribir historial publicado o borrar ramas remotas (y, en general, no deberías ejecutar ningún comando de git que modifique el repositorio salvo lectura: `status`, `diff`, `log`).

## Valores pendientes

- `{NOMBRE}`: **"The Macrochip"**.
- Secrets necesarios: `BUTTONDOWN_API_KEY` y `FRED_API_KEY`. En el *environment* de la Routine (plan Pro/Max), guárdalos como **API credentials** en vez de variables de entorno planas, para que no sean visibles dentro de la sesión (ver Fase 0).
