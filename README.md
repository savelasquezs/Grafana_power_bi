# SolarBI Pascual

Trabajo individual de Santiago Velásquez Serna para Inteligencia de Negocios, Grupo 50, semestre 2026-II. Docente: Ramiro Grisales Montoya.

El proyecto limpia telemetría simulada de una planta solar, carga los resultados en PostgreSQL y presenta los mismos datos en Grafana y Power BI.

## Ejecución

1. Crear y activar un entorno virtual de Python.
2. Instalar las dependencias con `pip install -r requirements.txt`.
3. Definir la variable de entorno `DATABASE_URL` con la conexión de PostgreSQL.
4. Ejecutar `python etl/run_etl.py`.
5. Repetir el comando y comprobar que los conteos finales no cambian.

La ejecución genera los archivos Bronze y Silver, aplica reglas para faltantes, duplicados y rangos físicos, y realiza cargas UPSERT en PostgreSQL.

## Automatización diaria

Expresión cron para ejecutar el proceso todos los días a medianoche:

```text
0 0 * * * cd /ruta/solarbi && /ruta/python etl/run_etl.py
```

## Contenido

- `data/bronze`: telemetría original sin modificaciones.
- `data/silver`: registros aprobados por las reglas de calidad.
- `etl`: simulador y punto único de ejecución.
- `sql`: estructura de tablas y consultas utilizadas en Grafana.
- `grafana`: dashboard exportado en JSON.
- `powerbi`: informe de Power BI Desktop (`SolarBI_Pascual.pbix`).
- `docs`: informe final en PDF.

No se incluyen contraseñas ni cadenas de conexión en el repositorio.

El dashboard de Grafana se importa desde `grafana/dashboard.json`. Tanto Grafana como Power BI consultan la base `solarbi` del mismo proyecto PostgreSQL en Neon. Las credenciales se configuran localmente y no se versionan.

Repositorio: https://github.com/savelasquezs/Grafana_power_bi

## Autor

| Integrante | Documento | Aporte |
|---|---:|---|
| Santiago Velásquez Serna | 1038414022 | ETL, PostgreSQL, Grafana, Power BI e informe |

La actividad se desarrolló individualmente, por lo que no aplica un segundo colaborador ni un segundo autor de commits.
