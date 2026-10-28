"""Expectativas independientes del detector: números calculados a mano."""
import json
from datetime import timedelta
import pandas as pd
import pytest
from industrialdata.common import timestamp, sha
from industrialdata.generate import generate, artifacts
from industrialdata.ingest import ingest, business_tables
from industrialdata.analyze import analyze, episodes_from_flags
from industrialdata.run import execute, current_snapshot
from industrialdata import reglas as r

@pytest.fixture
def caso(tmp_path):
    generate(tmp_path, offline=True)
    catalog=json.loads((tmp_path/'catalog.json').read_text())
    return tmp_path,catalog

def test_45_recepciones_40_observaciones(caso):
    folder,catalog=caso
    t,stats,rejects,_=ingest(folder/'raw',catalog,'prueba')
    assert stats==dict(input=45,accepted_new=40,duplicates=1,rejected=4)
    assert len(t)==40
    assert not t.duplicated(['sensor_id','timestamp_utc']).any()
    assert {'conflicting_value','invalid_unit','invalid_machine_id'} <= {row['reason'] for row in rejects}
    assert all(row['source_line']>0 and len(row['source_sha256'])==64 for row in rejects)

def test_repeticion_y_publicacion(caso):
    folder,_=caso
    first=execute(folder,offline=True);before=pd.read_parquet(current_snapshot(folder)/'gold/metrics.parquet')
    second=execute(folder,offline=True);after=pd.read_parquet(current_snapshot(folder)/'gold/metrics.parquet')
    assert first['accepted_new']==40
    assert second['accepted_new']==0 and second['duplicates']==41 and second['rejected']==4
    assert second['canonical_rows']==40 and second['episodes']==1
    pd.testing.assert_frame_equal(before,after)

def test_metricas_y_episodio(caso):
    folder,catalog=caso;t,_,_,_=ingest(folder/'raw',catalog,'prueba');p,m=business_tables(folder/'raw',catalog)
    episodes,quality,metrics=analyze(t,p,m,catalog)
    assert len(episodes)==1
    episode=episodes.iloc[0]
    assert (episode.machine_id,episode.rule,episode.start_utc,episode.end_utc)==('M01','temperature_high','2026-01-12T08:02:00Z','2026-01-12T08:07:00Z')
    assert episode.samples==5 and episode.duration_s==300
    a,b=metrics.set_index('machine_id').loc[['M01','M02']].to_dict('records')
    assert a['energy_kwh']==pytest.approx(1) and a['energy_coverage']==1
    assert a['kwh_per_good_unit']==pytest.approx(.1)
    assert b['energy_kwh']==pytest.approx(.35) and b['energy_coverage']==pytest.approx(.7)
    assert not b['evaluable'] and pd.isna(b['kwh_per_good_unit'])
    assert quality.set_index('sensor_id').loc['M02_power','coverage']==.8

def test_fuentes_inmutables_y_fallo_controlado(caso):
    folder,_=caso;execute(folder,offline=True);pointer=(folder/'current.json').read_bytes()
    path=folder/'raw/production.csv';path.write_text(path.read_text().replace(',10,0',',999,0'))
    with pytest.raises(ValueError,match='Fuente original modificada'):execute(folder,offline=True)
    assert (folder/'current.json').read_bytes()==pointer

def test_generacion_reproducible_y_protegida(caso):
    folder,_=caso;path=folder/'raw/telemetry_001.jsonl';before=sha(path);generate(folder,offline=True);assert sha(path)==before
    path.write_text(path.read_text()+'{}\n')
    with pytest.raises(ValueError,match='Original diferente'):generate(folder,offline=True)

def test_union_no_multiplica(caso):
    folder,catalog=caso;t,_,_,_=ingest(folder/'raw',catalog,'prueba');p,_=business_tables(folder/'raw',catalog)
    enriched=t.merge(pd.DataFrame(catalog['machines']),on='machine_id',validate='many_to_one')
    assert len(enriched)==len(t)==40
    assert p.units_ok.sum()==18  # No sumar piezas tras repetir cada fila por cada muestra.

def test_a1_copia_y_anomalia_valida():
    catalog,files=artifacts();row=json.loads(files['raw/telemetry_001.jsonl'].splitlines()[2]);sensor=catalog['sensors'][0]
    result=r.normalizar(row,sensor,catalog)
    assert result==row and result is not row and result['value']==85

@pytest.mark.parametrize('change,motivo',[(dict(value=True),'numeric_value_required'),(dict(value=float('nan')),'physical_range'),(dict(value=201),'physical_range'),(dict(timestamp_utc='2026-01-12T08:00:30Z'),'off_grid'),(dict(timestamp_utc='2026-01-12T08:00:00'),'timezone_required')])
def test_a1_rechazos(change,motivo):
    catalog,files=artifacts();row=json.loads(files['raw/telemetry_001.jsonl'].splitlines()[0])
    with pytest.raises(ValueError,match=motivo):r.normalizar(row|change,catalog['sensors'][0],catalog)

def test_colision_evento():
    with pytest.raises(ValueError,match='event_id_collision'):r.clasificar({},None,True)

def test_limite_y_secuencia_interrumpida():
    assert r.superaciones([79,80,81],80)==[False,False,True]
    base=timestamp('2026-01-12T08:00:00Z');times=[base+timedelta(minutes=i) for i in [0,1,2,5,6]]
    assert episodes_from_flags(times,[True]*5,60,'M01','s','temperature_high',5)==[]

def test_estados_y_desconocidos():
    assert r.estados([True,True,True,False],[6,0,0,0],[False,True,False,True],.1)==dict(idle_consumption=[True,False,False,False],planned_stop=[False,True,False,False],unplanned_stop=[False,False,True,False])

def test_energia_segmentos_y_extremos():
    a=timestamp('2026-01-12T08:00:00Z');times=[a+timedelta(minutes=i) for i in range(6)]
    kwh,seconds=r.energia(times,[6]*6,a,a+timedelta(minutes=5))
    assert kwh==pytest.approx(.5) and seconds==300
    assert r.energia([a],[6],a,a+timedelta(minutes=5))==(0,0)
    kwh,seconds=r.energia([a,a+timedelta(minutes=1)],[6,6],a+timedelta(seconds=30),a+timedelta(minutes=1))
    assert kwh==pytest.approx(.05) and seconds==30

@pytest.mark.parametrize('units,ec,pc,crossing',[(0,1,1,False),(10,.94,1,False),(10,1,.9,False),(10,1,1,True)])
def test_intensidad_no_evaluable(units,ec,pc,crossing):
    assert r.intensidad(1,units,ec,pc,crossing) is None

def test_parquet_y_avro(caso):
    from fastavro import reader
    folder,_=caso;execute(folder,offline=True);snap=current_snapshot(folder)
    with (snap/'gold/episodes.avro').open('rb') as f:records=list(reader(f))
    assert len(records)==1 and records[0]['note'] is None
    assert len(pd.read_parquet(snap/'silver/telemetry.parquet'))==40
