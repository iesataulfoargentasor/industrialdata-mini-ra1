"""Solución docente del caso Mini. Correspondencia A1–A6 en el trabajo guiado.
Las funciones aplican contratos generales; nunca consultan resultados_esperados.json.
"""
import math
from .common import timestamp, iso


def normalizar(row, sensor, catalog):
    """A1: copiar, validar contra catálogo y normalizar UTC; conservar anomalías."""
    result = row.copy()
    for key in ('machine_id', 'variable', 'unit'):
        if result.get(key) != sensor[key]:
            raise ValueError('invalid_' + key)
    observed = timestamp(result['timestamp_utc'])
    received = timestamp(result['ingested_at_utc'])
    start, end = timestamp(catalog['start']), timestamp(catalog['end'])
    if not start <= observed <= end:
        raise ValueError('outside_window')
    value = result['value']
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('numeric_value_required')
    if not math.isfinite(value) or not sensor['physical_min'] <= value <= sensor['physical_max']:
        raise ValueError('physical_range')
    if (observed-start).total_seconds() % sensor['expected_period_s'] != 0:
        raise ValueError('off_grid')
    result.update(timestamp_utc=iso(observed), ingested_at_utc=iso(received))
    return result


def clasificar(row, previous, event_collision=False):
    """A2: primera observación aceptada prevalece; conflicto registrado, no sustituido."""
    if event_collision:
        raise ValueError('event_id_collision')
    if previous is None:
        return 'new'
    if any(row[k] != previous[k] for k in ('machine_id', 'variable', 'unit', 'value')):
        raise ValueError('conflicting_value')
    return 'duplicate'


def superaciones(values, limit):
    """A3: igualdad no es superación. La agrupación temporal se hace en analyze.py."""
    return [value > limit for value in values]


def estados(known_zero, values, planned, idle_kw):
    """A4: clasificar muestras. La duración mínima se comprueba después."""
    if len({len(known_zero), len(values), len(planned)}) != 1:
        raise ValueError('length_mismatch')
    return {
        'idle_consumption': [zero and value > idle_kw for zero, value in zip(known_zero, values)],
        'planned_stop': [zero and value <= idle_kw and plan for zero, value, plan in zip(known_zero, values, planned)],
        'unplanned_stop': [zero and value <= idle_kw and not plan for zero, value, plan in zip(known_zero, values, planned)],
    }


def energia(times, values, start, end, cadence=60):
    """A5: retención izquierda, sin extrapolación ni relleno de huecos largos."""
    if len(times) != len(values):
        raise ValueError('length_mismatch')
    kwh, covered = 0.0, 0.0
    for left, right, power in zip(times[:-1], times[1:], values[:-1]):
        gap = (right-left).total_seconds()
        if 0 < gap <= 1.5*cadence:
            seconds = max(0.0, (min(right, end)-max(left, start)).total_seconds())
            covered += seconds
            kwh += power * seconds / 3600
    return kwh, covered


def intensidad(kwh, units_ok, energy_coverage, production_coverage, crossing):
    """A6: no confundir desconocido con cero ni energía parcial con eficiencia."""
    if energy_coverage < .95 or production_coverage < .999999 or crossing or units_ok <= 0:
        return None
    return kwh / units_ok
