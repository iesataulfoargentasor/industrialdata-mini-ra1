from industrialdata.catalog import connection
from industrialdata.common import root
from industrialdata.run import current_snapshot
import pandas as pd
with connection() as conn:
    assert conn.execute('SELECT COUNT(*) FROM machines').fetchone()[0]==2
    assert conn.execute('SELECT COUNT(*) FROM sensors').fetchone()[0]==4
    assert conn.execute("SELECT COUNT(*) FROM runs WHERE status='success'").fetchone()[0]>0
snapshot=current_snapshot(root())
assert snapshot is not None
assert len(pd.read_parquet(snapshot/'silver/telemetry.parquet'))==40
print('PostgreSQL: 2 máquinas, 4 sensores y cargas correctas. Publicación: 40 observaciones.')
