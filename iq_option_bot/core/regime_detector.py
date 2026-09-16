"""Detecta el régimen actual del mercado (tendencia, rango, volátil...)."""
import pandas as pd

from core.indicators import Indicadores


class DetectorRegimen:
    """Detecta el régimen actual del mercado"""

    @staticmethod
    def detectar(df):
        adx, plus_di, minus_di = Indicadores.adx(df)
        atr = Indicadores.atr(df)
        bb_up, bb_mid, bb_low = Indicadores.bollinger(df['close'])

        if len(adx) < 1 or pd.isna(adx.iloc[-1]):
            return "DESCONOCIDO"

        adx_v = adx.iloc[-1]
        precio = df['close'].iloc[-1]
        atr_pct = (atr.iloc[-1] / precio * 100) if precio > 0 else 0
        bb_width = ((bb_up.iloc[-1] - bb_low.iloc[-1]) / bb_mid.iloc[-1]) if bb_mid.iloc[-1] > 0 else 0

        if adx_v > 25:
            if plus_di.iloc[-1] > minus_di.iloc[-1]:
                return "TENDENCIA_ALCISTA"
            else:
                return "TENDENCIA_BAJISTA"

        if adx_v < 20 and bb_width < 0.02:
            return "RANGO"

        if atr_pct > 0.15:
            return "VOLATIL"

        return "NORMAL"
