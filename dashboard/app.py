"""Panel docente: distingue explícitamente energía parcial e indicador no evaluable."""
import json
import pandas as pd
import streamlit as st
from industrialdata.common import root
from industrialdata.run import current_snapshot

st.set_page_config(page_title='IndustrialData Mini · RA1', page_icon='🏭', layout='wide')
st.title('IndustrialData Mini')
st.caption('Sistemas de Big Data · RA1 · Dos máquinas, diez minutos · Datos sintéticos · UTC')
snapshot=current_snapshot(root())
if snapshot is None:
    st.info('Aún no hay resultados publicados. Sigue los cuadernos 00–04 o ejecuta: docker compose run --rm pipeline')
    st.stop()
report=json.loads((snapshot/'report.json').read_text())
metrics=pd.read_parquet(snapshot/'gold/metrics.parquet')
episodes=pd.read_parquet(snapshot/'gold/episodes.parquet')
quality=pd.read_parquet(snapshot/'gold/quality.parquet')
selected=st.multiselect('Máquinas',list(metrics.machine_id.unique()),default=list(metrics.machine_id.unique()))
st.caption(f"Periodo: 08:00–08:10 UTC · Última publicación: {report['finished_at']} · {report['run_id']}")
a,b,c=st.tabs(['Incidencias y evidencia','Producción y energía','Calidad y trazabilidad'])
with a:
    ep=episodes[episodes.machine_id.isin(selected)]
    st.metric('Episodios detectados',len(ep))
    st.dataframe(ep,hide_index=True)
    st.info('Cinco muestras de temperatura elevada producen un episodio. Las dos muestras ausentes de M02 afectan la cobertura, pero no alcanzan el umbral de diez muestras para un episodio de sensor ausente. Tampoco demuestran una parada.')
    if not ep.empty:
        chosen=st.selectbox('Inspeccionar episodio',ep.episode_id)
        row=ep[ep.episode_id==chosen].iloc[0]
        data=pd.read_parquet(snapshot/'silver/telemetry.parquet')
        evidence=data[(data.sensor_id==row.sensor_id)&(data.timestamp_utc>=row.start_utc)&(data.timestamp_utc<row.end_utc)]
        st.dataframe(evidence,hide_index=True)
with b:
    m=metrics[metrics.machine_id.isin(selected)].copy()
    display=m.copy()
    display['kwh_per_good_unit']=display.kwh_per_good_unit.map(lambda x:'No evaluable' if pd.isna(x) else f'{x:.3f} kWh/pieza')
    st.dataframe(display,hide_index=True)
    st.bar_chart(m.set_index('machine_id')[['energy_kwh']], y_label='kWh observados (pueden ser parciales)')
    st.warning('M02: 0,35 kWh cubren solo el 70 % del tiempo. No se puede concluir que sea más eficiente que M01. No compares barras sin mirar la cobertura.')
    st.caption('M01: 6 kW × 10/60 h = 1 kWh; 10 piezas → 0,1 kWh/pieza. M02: hueco 08:03–08:06 excluido; 3 kW × 7/60 h = 0,35 kWh.')
with c:
    st.dataframe(quality[quality.machine_id.isin(selected)],hide_index=True)
    st.caption('Cobertura de muestras de M02_power: 8/10 = 80 %. Cobertura de energía: 7/10 = 70 %. Son métricas distintas.')
    st.json(report)
    st.dataframe(pd.DataFrame(json.loads((snapshot/'quarantine/rejections.json').read_text())),hide_index=True)
    st.caption('Los recuentos corresponden a la última recepción completa. Tras repetir: 45 = 0 nuevas + 41 duplicadas + 4 rechazadas; siguen 40 observaciones consolidadas.')
    st.download_button('Descargar informe',json.dumps(report,indent=2),file_name='mini-informe.json')
