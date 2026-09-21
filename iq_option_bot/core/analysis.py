"""Análisis integrado de un par: une régimen, IA y contexto de velas."""
import pandas as pd

from core.regime_detector import DetectorRegimen
from core.candle_analyzer import AnalizadorVelas


def analizar_activo(activo, velas, selector_ia):
    """Analiza un activo con IA y devuelve señal + contexto"""
    df = preparar_dataframe(velas) 
    df = df.sort_values('timestamp').reset_index(drop=True)

    if len(df) < 30:
        return {
            'activo': activo,
            'señal': 'ESPERAR',
            'confianza': 0,
            'regimen': 'DESCONOCIDO',
            'estrategia': None,
            'precio': df['close'].iloc[-1] if len(df) else 0,
            'detalles': {}
        }

    regimen = DetectorRegimen.detectar(df)
    señal, confianza, estrategia, detalles = selector_ia.analizar_con_ia(df, regimen)

    anatomia = AnalizadorVelas.anatomia_vela(df)
    estructura = AnalizadorVelas.estructura_mercado(df)

    return {
        'activo': activo,
        'señal': señal,
        'confianza': confianza,
        'regimen': regimen,
        'estrategia': estrategia,
        'precio': df['close'].iloc[-1],
        'estructura': estructura,
        'anatomia': anatomia,
        'detalles': detalles
    }
def preparar_dataframe(velas):
    if not velas:
        raise ValueError("No se recibieron velas")

    filas = []

    for vela in velas:
        if not isinstance(vela, dict):
            continue

        filas.append({
            "timestamp": vela.get("from"),
            "open": vela.get("open"),
            "close": vela.get("close"),
            "high": vela.get("max"),
            "low": vela.get("min"),
            "volume": vela.get("volume", 0),
        })

    df = pd.DataFrame(filas)

    columnas = ["timestamp", "open", "close", "high", "low", "volume"]

    for columna in columnas:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    df = df.dropna(
        subset=["timestamp", "open", "close", "high", "low"]
    )

    df = df.sort_values("timestamp").reset_index(drop=True)

    if len(df) < 30:
        raise ValueError(
            f"Solo hay {len(df)} velas válidas; se necesitan al menos 30"
        )

    return df