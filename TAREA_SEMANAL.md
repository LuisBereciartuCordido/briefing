# Tarea semanal

> Esto es lo que ejecuta la Routine de Claude Code cada domingo. El prompt de la Routine es solo: "Lee y ejecuta TAREA_SEMANAL.md" — todo lo demás vive aquí, no en `CLAUDE.md` (sección 8).

Se ejecuta el **domingo hacia mediodía (hora de Madrid)**, para que el dueño del proyecto revise el borrador y lo envíe por la tarde.

## 0. Calcula la semana

Antes de nada, calcula la semana ISO actual (formato `AAAA-Sww`) y su periodo (lunes a domingo). Todo lo que sigue usa esa `{semana}`, `{inicio}` y `{fin}`.

## 1. Datos duros

```
python scripts/fetch_data.py --semana {semana}
```

Si falla, **detente aquí**. No continúes con la redacción sin `datos.json`: léelo del error que imprime el comando y termina con un resumen explicando qué falló y por qué no hay borrador esta semana.

## 2. Redacción, un módulo cada vez

Para cada módulo de `config/modulos.yaml`, en orden:

1. Investiga con búsqueda web, respetando los niveles y dominios de `config/fuentes.yaml`.
2. Antes de asignar un `hilo_id`, revisa las carpetas `data/AAAA-Sww/` de las últimas 4 semanas y reutiliza el `hilo_id` si es la misma historia que continúa.
3. Escribe las noticias del módulo siguiendo `prompts/redactor.md` y `prompts/estilo.md`.
4. Guarda el resultado en `data/{semana}/borrador.json`, con la forma de `schema/informe.schema.json`.

Tratar cada módulo por separado (en vez de todos a la vez) garantiza una cobertura equilibrada entre módulos.

## 3. Unión

En el mismo `borrador.json`, redacta "Lo esencial", "Macro global", "Concepto de la semana", "Perspectiva de largo plazo" y "Agenda de la semana siguiente" — mirando el conjunto de lo que escribiste módulo a módulo. Elimina duplicados entre módulos (la misma noticia no debería aparecer dos veces).

## 4. Verificación en frío

Vuelve a leer `borrador.json` como un revisor escéptico, siguiendo `prompts/verificador.md`. **Abre de nuevo las fuentes** — no te fíes de lo que recuerdes de cuando redactaste. Escribe el resultado en `data/{semana}/informe.json`, con los cambios que hiciste registrados en `cambios_verificador`.

## 5. Validación (máximo 2 intentos)

```
python scripts/validate.py --semana {semana}
```

- Si termina en 0: sigue al paso 6.
- Si termina en error: lee `data/{semana}/log.json` (clave `"validacion"`), corrige `informe.json` según lo que diga, y repite este paso. **Como máximo 2 intentos en total.**
- Si sigue fallando tras 2 intentos: **detente sin publicar**. El error ya quedó en `log.json` (lo escribe `validate.py` siempre, falle o no). Termina con el resumen del paso 9, explicando qué bloqueó la publicación esta semana.

## 6. Renderizado

```
python scripts/render.py --semana {semana}
```

Produce `data/{semana}/informe.md`.

## 7. Borrador en Buttondown

```
python scripts/publish.py --semana {semana}
```

Crea el borrador — **nunca lo envía**. Si falla (clave inválida, red caída...), detente y repórtalo en el resumen; no sigas al commit si no hay borrador.

## 8. Commit de la semana

Esta es la única parte del proyecto donde tú (la sesión de la Routine) haces el commit y el push directamente — no hay nadie presente para hacerlo por ti. Es la excepción explícita a las reglas de git de `CLAUDE.md` (sección 16).

```
git checkout claude/archivo-semanal 2>/dev/null || git checkout -b claude/archivo-semanal
git add data/{semana}/
git commit -m "data({semana}): informe semanal"
git push -u origin claude/archivo-semanal
```

El dueño del proyecto fusiona esta rama a `main` periódicamente, a su ritmo — no abras un Pull Request ni intentes fusionarla tú.

## 9. Resumen final

Termina siempre (se haya publicado o no) con un resumen breve:

- Qué módulos tuvieron novedades y cuáles no.
- Número de fuentes usadas, por nivel.
- Avisos del validador (los que no bloquean: límite de palabras, concentración de medios, módulo sin fuentes fiables).
- Si se publicó: el enlace al borrador en Buttondown.
- Si no se publicó: en qué paso se detuvo y por qué.
