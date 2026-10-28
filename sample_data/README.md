# Muestra completa Mini

Los archivos son originales de ejemplo reproducibles: 45 líneas JSON, dos filas de producción y una de mantenimiento (más cabeceras CSV). Se puede inspeccionar esta carpeta sin Docker.

El generador produce esos mismos originales en `data/raw` y carga el catálogo en PostgreSQL. `catalog.json` aquí es la representación exportada del catálogo. `manifest.json` contiene hashes de los originales. `resultados_esperados.json` es exclusivamente material del profesor y las pruebas, no entrada de las reglas.

Los datos simulados no representan una planta real. M01 tiene temperatura alta de 08:02 a 08:06 inclusive; el episodio se expresa como [08:02,08:07). M02 carece de potencia en 08:04 y 08:05. Los cinco registros adicionales están al final: duplicado (línea 41), conflicto (42), unidad (43), máquina (44) y fecha (45).
