"""Ensayo de todos los cuadernos con PostgreSQL; resultados fuera de los originales."""
import os
import shutil
from pathlib import Path
from uuid import uuid4
import nbformat
from nbclient import NotebookClient
from industrialdata.generate import generate

folder=Path('/data')/('ensayo_'+uuid4().hex[:8]);folder.mkdir()
os.environ['DATA_ROOT']=str(folder)
generate(folder)
copy=folder/'cuadernos';shutil.copytree('/app/notebooks',copy,ignore=shutil.ignore_patterns('.ipynb_checkpoints','__pycache__'))
for path in sorted(copy.glob('*.ipynb')):
    book=nbformat.read(path,as_version=4)
    NotebookClient(book,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(copy)}}).execute()
    nbformat.write(book,path)
    print('OK',path.name,flush=True)
print('Evidencias:',folder,flush=True)
