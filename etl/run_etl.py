import csv
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg

from simulador import generar_telemetria


ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "data" / "bronze" / "telemetria.csv"
SILVER = ROOT / "data" / "silver" / "lectura_5min.csv"
METRICAS = ROOT / "data" / "silver" / "metricas_calidad.json"
SCHEMA = ROOT / "sql" / "schema.sql"


def limpiar(ruta: Path):
    with ruta.open(encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))

    leidas = len(filas)
    faltantes = []
    completas = []
    for fila in filas:
        if any(fila[campo] == "" for campo in ("ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c")):
            faltantes.append(fila)
        else:
            completas.append(fila)

    unicas = []
    vistas = set()
    duplicadas = 0
    for fila in completas:
        clave = tuple(fila[campo] for campo in ("ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"))
        if clave in vistas:
            duplicadas += 1
        else:
            vistas.add(clave)
            unicas.append(fila)

    validas = []
    fuera_rango = 0
    for fila in unicas:
        potencia = Decimal(fila["p_ac_kw"])
        irradiancia = Decimal(fila["irradiancia_wm2"])
        temperatura = Decimal(fila["temp_modulo_c"])
        if not (Decimal("0") <= potencia <= Decimal("5.5") and Decimal("0") <= irradiancia <= Decimal("1200") and Decimal("-20") <= temperatura <= Decimal("90")):
            fuera_rango += 1
            continue
        validas.append(
            (
                datetime.fromisoformat(fila["ts"]),
                int(fila["dispositivo_id"]),
                potencia,
                irradiancia,
                temperatura,
            )
        )

    metricas = {
        "filas_leidas": leidas,
        "rechazadas_faltantes": len(faltantes),
        "rechazadas_duplicadas": duplicadas,
        "rechazadas_rango": fuera_rango,
        "filas_validas": len(validas),
        "pct_datos_validos": round(len(validas) * 100 / leidas, 2),
    }
    return filas, validas, metricas


def guardar_silver(filas, metricas):
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    with SILVER.open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(["ts", "dispositivo_key", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"])
        writer.writerows(filas)
    METRICAS.write_text(json.dumps(metricas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resumir(filas_crudas, filas_validas):
    totales = Counter(datetime.fromisoformat(fila["ts"]).date() for fila in filas_crudas if fila["ts"])
    validas_por_dia = defaultdict(list)
    for fila in filas_validas:
        validas_por_dia[fila[0].date()].append(fila)

    resumen = []
    for fecha, filas in sorted(validas_por_dia.items()):
        energia = sum((fila[2] * Decimal(5) / Decimal(60) for fila in filas), Decimal(0))
        cantidad = len(filas)
        resumen.append((fecha, filas[0][1], energia.quantize(Decimal("0.001")), Decimal(cantidad * 100 / totales[fecha]).quantize(Decimal("0.01")), cantidad, totales[fecha]))
    return resumen


def cargar(filas, resumen):
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Falta la variable de entorno DATABASE_URL")

    with psycopg.connect(database_url) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(SCHEMA.read_text(encoding="utf-8"))
            cursor.execute(
                """
                INSERT INTO dwh.dim_dispositivo (dispositivo_key, nombre, tipo, potencia_nominal_kwp)
                VALUES (1, 'Inversor 1', 'Inversor', 5.0)
                ON CONFLICT (dispositivo_key) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    tipo = EXCLUDED.tipo,
                    potencia_nominal_kwp = EXCLUDED.potencia_nominal_kwp
                """
            )
            inicio = min(fila[0] for fila in filas)
            fin = max(fila[0] for fila in filas)
            cursor.execute(
                "DELETE FROM silver.lectura_5min WHERE dispositivo_key = %s AND ts BETWEEN %s AND %s",
                (filas[0][1], inicio, fin),
            )
            cursor.executemany(
                """
                INSERT INTO silver.lectura_5min (ts, dispositivo_key, p_ac_kw, irradiancia_wm2, temp_modulo_c)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ts, dispositivo_key) DO UPDATE SET
                    p_ac_kw = EXCLUDED.p_ac_kw,
                    irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
                    temp_modulo_c = EXCLUDED.temp_modulo_c
                """,
                filas,
            )
            cursor.executemany(
                """
                INSERT INTO dwh.fact_energia_dia
                    (fecha_key, dispositivo_key, energia_kwh, pct_datos_validos, lecturas_validas, lecturas_totales)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (fecha_key, dispositivo_key) DO UPDATE SET
                    energia_kwh = EXCLUDED.energia_kwh,
                    pct_datos_validos = EXCLUDED.pct_datos_validos,
                    lecturas_validas = EXCLUDED.lecturas_validas,
                    lecturas_totales = EXCLUDED.lecturas_totales
                """,
                resumen,
            )
            cursor.execute("SELECT COUNT(*) FROM silver.lectura_5min")
            silver_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM dwh.fact_energia_dia")
            gold_count = cursor.fetchone()[0]
    return silver_count, gold_count


def main():
    if not BRONZE.exists():
        generar_telemetria(BRONZE)
    crudas, validas, metricas = limpiar(BRONZE)
    guardar_silver(validas, metricas)
    resumen = resumir(crudas, validas)
    silver_count, gold_count = cargar(validas, resumen)

    for nombre, valor in metricas.items():
        print(f"{nombre}: {valor}")
    print(f"silver.lectura_5min: {silver_count}")
    print(f"dwh.fact_energia_dia: {gold_count}")


if __name__ == "__main__":
    main()

