#!/usr/bin/env bash
# Encadena los 4 scripts deterministas para una prueba completa en local
# (sección 15.4 de CLAUDE.md). Se detiene en el primer fallo (set -e).
#
# Uso:
#   scripts/run_week.sh AAAA-Sww [--sin-comprobar-enlaces] [--sin-publicar]
#
# No lo usa la tarea programada semanal: la Routine llama a fetch_data.py,
# hace la redacción y verificación (requieren criterio, no se pueden
# scriptar) y luego llama a validate.py/render.py/publish.py por separado
# — ver TAREA_SEMANAL.md. Este script asume que informe.json ya existe
# (escrito a mano o de una ejecución anterior) y sirve para comprobar el
# resto del pipeline de punta a punta sin depender de Claude.

set -euo pipefail

semana=""
sin_comprobar_enlaces=""
sin_publicar=""

for arg in "$@"; do
  case "$arg" in
    --sin-comprobar-enlaces) sin_comprobar_enlaces="--sin-comprobar-enlaces" ;;
    --sin-publicar) sin_publicar="1" ;;
    -*) echo "Opción desconocida: $arg" >&2; exit 1 ;;
    *) semana="$arg" ;;
  esac
done

if [[ -z "$semana" ]]; then
  echo "Uso: $0 AAAA-Sww [--sin-comprobar-enlaces] [--sin-publicar]" >&2
  exit 1
fi

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$raiz"

echo "== fetch_data.py =="
python scripts/fetch_data.py --semana "$semana"

echo "== validate.py =="
python scripts/validate.py --semana "$semana" $sin_comprobar_enlaces

echo "== render.py =="
python scripts/render.py --semana "$semana"

if [[ -n "$sin_publicar" ]]; then
  echo "Omitido publish.py (--sin-publicar). informe.md listo en data/$semana/."
  exit 0
fi

echo "== publish.py =="
python scripts/publish.py --semana "$semana"

echo "Listo: borrador de la semana $semana creado en Buttondown."
