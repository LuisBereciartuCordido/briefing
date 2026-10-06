"""Aritmética de semanas ISO (sección 7 de CLAUDE.md: "semana": "AAAA-Sww").

Lo usan tanto fetch_data.py (para comparar con la semana anterior y decidir
si un dato mensual es nuevo) como render.py (para calcular la variación
semanal de la tabla de mercados): de ahí que viva en briefing/ en vez de
duplicarse en los dos scripts.
"""

from __future__ import annotations

import datetime


def semana_iso(fecha: datetime.date) -> str:
    """Semana ISO de una fecha, formato AAAA-Sww."""
    iso_year, iso_week, _ = fecha.isocalendar()
    return f"{iso_year}-S{iso_week:02d}"


def periodo_de_semana(semana: str) -> tuple[datetime.date, datetime.date]:
    """(lunes, domingo) de una semana ISO "AAAA-Sww"."""
    anio_str, semana_str = semana.split("-S")
    lunes = datetime.date.fromisocalendar(int(anio_str), int(semana_str), 1)
    return lunes, lunes + datetime.timedelta(days=6)


def semana_anterior(semana: str) -> str:
    """La semana ISO inmediatamente anterior a `semana`."""
    lunes, _ = periodo_de_semana(semana)
    return semana_iso(lunes - datetime.timedelta(days=7))
