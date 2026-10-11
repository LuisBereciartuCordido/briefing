# The Macrochip

Newsletter semanal en español que explica el contexto económico y geopolítico global que mueve los mercados — para alguien sin formación económica, sin dar nunca consejos de inversión.

Cada domingo, una tarea programada de Claude Code descarga datos duros de fuentes oficiales, investiga y redacta el informe de la semana, lo verifica contra sus propias fuentes releyéndolas (no de memoria), lo valida con reglas deterministas y crea un **borrador** — nunca lo envía — en Buttondown. Un humano lo revisa y lo envía.

## El pipeline

```
fetch_data.py → datos.json
      ↓
[redacción + verificación — requieren criterio, las hace Claude]
      ↓
validate.py → informe.json válido, o se detiene sin publicar
      ↓
render.py → informe.md (email) + transparencia.md (uso interno)
      ↓
publish.py → borrador en Buttondown
```

La frontera es deliberada: todo lo que se puede decidir con una regla fija es código Python con tests (descarga, validación, renderizado, publicación). Todo lo que requiere criterio real — qué es noticia, si una fuente dice lo que parece decir, si una cifra cuadra — lo hace Claude dentro de la tarea programada, siguiendo instrucciones versionadas en el repo, no código que intente simular juicio.

Un único `informe.schema.json` es la fuente de verdad: el email, el paquete de contexto para IA que lleva cada número, y el resumen de transparencia salen todos del mismo JSON, nunca se redactan por separado.

## Decisiones de ingeniería

**Dónde no hay fuente oficial, se documenta el riesgo en vez de fingir que no existe.** BCE, Eurostat, INE y FRED cubren tipos de interés e inflación sin fricción. Para Nikkei 225, oro y los índices MSCI no hay ninguna API oficial gratuita; se usa el endpoint no oficial de Yahoo Finance, con el riesgo anotado explícitamente en vez de ignorado, y sin una fuente de respaldo especulativa para un fallo que no ha ocurrido — si pasa, el pipeline se detiene sin publicar, igual que cualquier otro fallo.

**La verificación es una segunda pasada real, no una formalidad.** Después de redactar, una sesión distinta relee cada fuente desde cero — sin fiarse de lo que recordaba la redacción — y compara cada cifra contra los datos duros antes de dar el informe por bueno.

**La transparencia se genera, pero no se envía.** El informe registra qué fuentes se usaron, cuáles se descartaron y qué corrigió el verificador. Pero mostrarle esa lista de correcciones a cada suscriptor transmite "esto tiene fallos" en vez de fiabilidad, así que esa sección se escribe aparte, de uso interno, nunca en el email.

**Tests unitarios + una ejecución real de punta a punta.** Además de tests unitarios (lógica de validación, parseo de datos, llamadas HTTP mockeadas), el pipeline se probó completo con datos reales y un borrador real creado en Buttondown — eso es lo que saca a la luz los fallos de integración que un test aislado no ve.

**`CLAUDE.md` se mantiene en español, no en inglés.** La redacción corre en una Routine de la suscripción Pro/Max (coste fijo, no facturado por token), así que el ahorro de tokens que da la tokenización BPE del inglés frente a otros idiomas no se traduce aquí en ahorro real — y sí tiene un coste: es el documento que más releo y mantengo. Si el flujo usara la API de Anthropic facturada por uso, sería la decisión correcta.

## Arquitectura

```
config/        # Todo lo editable sin tocar código: módulos, fuentes, mercados, estilo
prompts/        # Redactor, verificador, estilo — el criterio versionado
schema/          # informe.schema.json, el contrato de datos central
scripts/          # CLIs delgadas
src/briefing/      # La lógica real, con tests
data/AAAA-Sww/      # Una carpeta por semana: datos, borrador, informe, email, log
```

Las convenciones completas del proyecto — por qué cada decisión, qué se descartó y por qué — están en [`CLAUDE.md`](./CLAUDE.md).

## Stack

Python 3.11+, dependencias mínimas (`requests`, `PyYAML`, `jsonschema`), sin frameworks, con tests unitarios.

## Aviso

Contenido informativo. No es asesoramiento financiero.
