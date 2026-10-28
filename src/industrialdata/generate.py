"""Datos de diez minutos, deterministas. Nunca sobrescribe originales distintos."""
import argparse
import csv
import io
import json
from datetime import timedelta
from pathlib import Path
from .common import root, timestamp, iso, sha, dump
from .catalog import save_catalog


def artifacts():
    start = timestamp('2026-01-12T08:00:00Z')
    at = lambda minute: iso(start + timedelta(minutes=minute))
    machines = [dict(machine_id='M01', machine_type='motor', location='Linea 1'),
                dict(machine_id='M02', machine_type='bomba', location='Linea 2')]
    sensors = []
    for machine in machines:
        for variable, unit, maximum, physical_min, physical_max in [('temperature', '°C', 80, -40, 200), ('power', 'kW', 10, 0, 100)]:
            sensors.append(dict(sensor_id=f"{machine['machine_id']}_{variable}", machine_id=machine['machine_id'],
                variable=variable, unit=unit, expected_period_s=60, operational_min=0,
                operational_max=maximum, physical_min=physical_min, physical_max=physical_max))
    catalog = dict(machines=machines, sensors=sensors, version='mini-1.0', start=at(0), end=at(10), idle_kw=.1,
        windows=[dict(machine_id=m['machine_id'], start_utc=at(0), end_utc=at(10)) for m in machines])
    rows = []
    temperatures = [70, 72, 85, 86, 87, 88, 89, 73, 72, 71]
    for s in sensors:
        for minute in range(11 if s['variable']=='power' else 10):
            if s['sensor_id']=='M02_power' and minute in (4, 5):
                continue
            value = (6 if s['machine_id']=='M01' else 3) if s['variable']=='power' else (temperatures[minute] if s['machine_id']=='M01' else 65)
            rows.append(dict(event_id=f"{s['sensor_id']}_{minute:02}", sensor_id=s['sensor_id'], machine_id=s['machine_id'],
                timestamp_utc=at(minute), variable=s['variable'], value=value, unit=s['unit'], ingested_at_utc=at(minute+1)))
    first = rows[0]
    rows += [first.copy(), first | dict(event_id='conflicto', value=71),
        first | dict(event_id='unidad', unit='F'), first | dict(event_id='maquina', machine_id='M999'),
        first | dict(event_id='fecha', timestamp_utc='fecha ilegible')]
    def csv_text(columns, data):
        stream=io.StringIO(newline=''); writer=csv.writer(stream, lineterminator='\n');writer.writerow(columns);writer.writerows(data);return stream.getvalue()
    files = {
        'raw/telemetry_001.jsonl': ''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),
        'raw/production.csv': csv_text(['production_id','machine_id','start_utc','end_utc','product_id','units_ok','units_rejected'],
            [['P01','M01',at(0),at(10),'A',10,0],['P02','M02',at(0),at(10),'B',8,0]]),
        'raw/maintenance.csv': csv_text(['maintenance_id','machine_id','start_utc','end_utc','planned','intervention_type'],
            [['MT01','M02',at(4),at(6),'true','inspeccion_programada']]),
    }
    return catalog, files


def generate(folder, offline=False):
    folder=Path(folder);catalog, files=artifacts()
    # Primero comprobar todos los originales antes de escribir o sincronizar SQL.
    for name, text in files.items():
        path=folder/name
        if path.exists() and path.read_text(encoding='utf-8') != text:
            raise ValueError(f'Original diferente: {name}. Conserva tus datos y usa otro DATA_ROOT.')
    folder.mkdir(parents=True,exist_ok=True)
    save_catalog(catalog,folder,offline)
    for name,text in files.items():
        path=folder/name;path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():path.write_text(text,encoding='utf-8')
    manifest=dict(scenario='mini-1.0', deterministic=True, machines=2, minutes=10,
        start=catalog['start'],end=catalog['end'],schema_version='1.0',
        files=[dict(path=name,sha256=sha(folder/name),physical_lines=len(text.splitlines())) for name,text in files.items()])
    dump(folder/'manifest.json',manifest)
    return manifest


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args();print(json.dumps(generate(args.output or root(),args.offline),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
