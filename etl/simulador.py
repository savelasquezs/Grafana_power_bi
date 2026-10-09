import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "bronze" / "telemetria.csv"


def generar_telemetria(ruta: Path = OUTPUT) -> Path:
    random.seed(50)
    inicio = datetime(2026, 10, 5)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"])

        for i in range(3 * 288):
            ts = inicio + timedelta(minutes=5 * i)
            sol = max(0.0, math.sin(math.pi * (ts.hour + ts.minute / 60 - 6) / 12))
            irradiancia = round(1000 * sol * random.uniform(0.7, 1.0), 1)
            potencia = round(5.0 * irradiancia / 1000 * random.uniform(0.80, 0.90), 3)
            fila = [ts.isoformat(sep=" "), 1, potencia, irradiancia, round(22 + 30 * sol, 1)]
            evento = random.random()

            if evento < 0.02:
                fila[2] = -1
            elif evento < 0.04:
                fila[3] = ""

            writer.writerow(fila)
            if evento > 0.98:
                writer.writerow(fila)

    return ruta


if __name__ == "__main__":
    print(generar_telemetria())

