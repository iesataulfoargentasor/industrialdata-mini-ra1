# IndustrialData Mini · Sistemas de Big Data · RA1

**Solución docente para una demostración de 90 minutos.** Dos máquinas, cuatro fuentes y diez minutos de datos. La pregunta es: **¿qué podemos afirmar sobre temperatura y consumo por pieza, y qué impide concluir la calidad de los datos?**

- [Guía web](https://iesataulfoargentasor.github.io/industrialdata-mini-ra1/)
- [Guion del profesor: 90 minutos](https://iesataulfoargentasor.github.io/industrialdata-mini-ra1/guion90.html)
- [Trabajo original que prepara esta demostración](https://iesataulfoargentasor.github.io/industrialdata-ut1-guiado/enunciado.html)

Es un proyecto independiente. No sustituye el trabajo evaluable ni acredita por sí solo todo el RA1. **Incluye código resuelto**, no una plantilla con actividades pendientes. Los datos y límites son ficticios, sin valor de seguridad industrial.

## Preparación antes de clase

Docker Desktop con Docker Compose, aproximadamente 2 GB disponibles para estos servicios y espacio para construir imágenes. En Mac M4 se ha comprobado ejecución ARM64; no hace falta instalar Python, PostgreSQL ni Java en macOS. Evita ejecutar otras cargas pesadas durante la clase. No se necesitan Hadoop, Hive, Trino, Kafka, Spark ni servicios de pago para esta sesión.

```bash
git clone https://github.com/iesataulfoargentasor/industrialdata-mini-ra1.git
cd industrialdata-mini-ra1
bash preparar.sh
bash iniciar.sh
```

Si descargas ZIP, abre Terminal en la carpeta real descomprimida (normalmente acaba en `-main`). El primer build necesita Internet; hazlo antes de clase. `iniciar.sh` usa imágenes locales y genera los mismos datos sin sobrescribir originales distintos.

- **Cuadernos:** http://localhost:18889/tree — abre `00_Abrir_la_fabrica.ipynb`.
- **Panel:** http://localhost:18501 — hasta ejecutar el cuaderno 04 informa de que no hay resultados.
- **PostgreSQL:** solo en la red Docker como `db:5432`, sin puerto público.

Los puertos 18889 y 18501 evitan los utilizados por los otros laboratorios. Puedes cambiarlos en `.env` (copia inicial de `.env.example`). Jupyter no pide token: los puertos están limitados a 127.0.0.1, para uso local del profesor; no lo expongas a Internet o a la red del aula sin configurar autenticación.

## Seis cuadernos resueltos

Ejecuta las celdas con Shift+Enter, en orden 00 → 05. Cada cuaderno importa lo que necesita. No necesitas trasladar variables entre kernels. Los `assert` son comprobaciones que deben pasar, no huecos para completar.

| Cuaderno | Minutos | Contenido |
|---|---:|---|
| 00_Abrir_la_fabrica | 0–18 | Encargo, fuentes JSON/CSV/SQL, claves y conjuntos |
| 01_Calidad_y_trazabilidad | 18–35 | A1–A2, reconciliación y procedencia |
| 02_Relaciones_e_incidencias | 35–47 | Joins, episodio de temperatura y tabla de A4 |
| 03_Energia_y_cobertura | 47–62 | A5–A6, huecos y comparación no evaluable |
| 04_Publicar_y_mostrar | 62–72 | Pipeline, Parquet, publicación y panel |
| 05_Repetir_y_comprobar | 72–90 | Idempotencia, pruebas y puente al trabajo |

El guion web incluye preguntas, respuestas, acciones del profesor, pausas de predicción y un plan de contingencia. No hay que programar todo el sistema en directo.

## Datos y resultados esperados

`sample_data/` contiene la muestra completa que puede inspeccionarse sin Docker. `iniciar.sh` genera la copia de trabajo en `data/raw` y carga el catálogo en PostgreSQL. `catalog.json` es una instantánea y soporte para pruebas offline; en la clase se consulta PostgreSQL.

- 45 recepciones JSONL = **40 nuevas + 1 duplicado + 4 rechazos** en la primera carga.
- Rechazos: conflicto, unidad incorrecta, máquina desconocida y fecha ilegible.
- M01: un episodio de temperatura en **[08:02, 08:07) UTC**, cinco muestras.
- M01: **1 kWh**, cobertura energética **100 %**, diez piezas → **0,1 kWh/pieza**.
- M02: **0,35 kWh observados**, cobertura energética **70 %**, ocho piezas → **no evaluable**.
- M02_power: cobertura de muestras **80 %**; faltan 08:04 y 08:05. La integración excluye el salto completo 08:03–08:06, de ahí el 70 % energético.
- Segunda carga: **45 = 0 nuevas + 41 duplicadas + 4 rechazadas**; siguen 40 observaciones y un episodio. El duplicado original también se recibe otra vez.

Dos muestras ausentes no alcanzan el umbral original de diez para un episodio de sensor ausente; aparecen en la calidad. La intervención de mantenimiento coincidente no demuestra una parada. El detector no lee `sample_data/resultados_esperados.json`.

## Ejecución ordinaria sin notebook

```bash
docker compose run --rm pipeline
```

Guarda Silver y Gold en `data/snapshots/<run_id>/`, incluida la cuarentena. `data/current.json` apunta a la última publicación completa. PostgreSQL guarda catálogo y auditoría; **no almacena toda la telemetría**. Raw no se modifica. El panel usa el puntero, de modo que no ve escrituras a medias.

Para consultar el catálogo:

```bash
docker compose exec db psql -U mini -d mini -c 'SELECT * FROM machines;'
```

## Pruebas y ensayo previo

```bash
bash comprobar.sh
docker compose exec notebook python /app/scripts/ensayar_cuadernos.py
```

`comprobar.sh` ejecuta 21 casos, publica el pipeline y verifica PostgreSQL. El ensayo ejecuta copias de los seis cuadernos y conserva sus salidas en `data/ensayo_<id>/`; utiliza PostgreSQL real y un DATA_ROOT independiente. No modifica los cuadernos originales ni el puntero de la demostración.

**Si ensayas con `comprobar.sh`, la primera carga de la clase será una repetición.** Explica ese estado; el cuaderno 01 siempre enseña la reconciliación inicial en memoria. No borres datos para aparentar un primer arranque. Para que el panel siga inicialmente vacío, usa únicamente el ensayo de cuadernos aislado.

Para verificar persistencia, publica una carga y ejecuta:

```bash
docker compose restart db dashboard notebook
docker compose run --rm pipeline python scripts/comprobar_postgres.py
```

Para parar conservando los datos: `bash parar.sh`. Para reanudar: `bash iniciar.sh`. No uses `down -v`: elimina el catálogo persistente.

## Dónde está la solución

- `src/industrialdata/reglas.py`: A1–A6 resueltas y comentadas.
- `generate.py`: generador determinista Mini; 45 recepciones y cuatro fuentes.
- `ingest.py`: lectura, reconciliación y trazabilidad.
- `analyze.py`: agrupación temporal, integración de fuentes y métricas.
- `run.py`: instantáneas, publicación y auditoría.
- `tests/test_mini.py`: resultados independientes, límites y protección de originales.
- `dashboard/app.py`: panel con tres vistas.

Los notebooks muestran la solución, pero no copian implementaciones alternativas del pipeline: llaman al mismo código que lo ejecuta. Si quieres modificar una regla como ejercicio, hazlo sobre una copia de trabajo y conserva el resultado de referencia.

## Alcance docente

La mini práctica introduce A1–A6 y fundamentos relacionados con los criterios RA1 a–g según la rúbrica del trabajo original. **No demuestra el criterio de grandes volúmenes**, la implementación A7 pandas/Spark, benchmarks completos, todos los escenarios S01–S08, estimaciones de coste ni planificación prolongada. La tabla A4 ilustra decisiones de muestras; no genera paradas completas en el dataset. El Avro producido por el soporte no sustituye el experimento de formatos del alumno.

`VALIDACION.txt` registra las comprobaciones realizadas. Esta demostración usa un único ordenador y datos pequeños; no es un clúster Big Data distribuido.

## Procedencia

Adaptación docente del [proyecto IndustrialData guiado](https://github.com/iesataulfoargentasor/industrialdata-ut1-guiado), revisión `84d525744a6ea81b8d57439cda83029a6c165a25`, del I.E.S. Ataúlfo Argenta. Se conservan y adaptan módulos de soporte de ingesta, análisis, catálogo y publicación; se añaden generador Mini, reglas resueltas, cuadernos, pruebas, panel y guion específico. La ayuda de IA utilizada en la preparación se contrasta mediante pruebas y ejecución real; no supone validación pedagógica de la duración exacta, que debe ajustarse tras el ensayo del profesor.
