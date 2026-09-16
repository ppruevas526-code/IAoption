"""Conjunto de estrategias que devuelven (señal, confianza)."""
import pandas as pd

from core.indicators import Indicadores
from core.candle_analyzer import AnalizadorVelas


class Estrategias:
    """Conjunto de estrategias que devuelven (señal, confianza)"""

    @staticmethod
    def tendencia(df):
        """Seguimiento de tendencia con EMAs"""
        ema_fast = Indicadores.ema(df['close'], 10)
        ema_slow = Indicadores.ema(df['close'], 30)

        if len(ema_fast) < 3:
            return "ESPERAR", 0

        if ema_fast.iloc[-1] > ema_slow.iloc[-1] and ema_fast.iloc[-2] <= ema_slow.iloc[-2]:
            return "CALL", 0.80
        elif ema_fast.iloc[-1] < ema_slow.iloc[-1] and ema_fast.iloc[-2] >= ema_slow.iloc[-2]:
            return "PUT", 0.80
        return "ESPERAR", 0

    @staticmethod
    def reversion_media(df):
        """Reversión a la media con RSI + Bollinger"""
        rsi = Indicadores.rsi(df['close'])
        bb_up, bb_mid, bb_low = Indicadores.bollinger(df['close'])

        if len(rsi) < 2:
            return "ESPERAR", 0

        precio = df['close'].iloc[-1]
        rsi_v = rsi.iloc[-1]

        if rsi_v < 30 and precio < bb_low.iloc[-1]:
            return "CALL", 0.85
        elif rsi_v > 70 and precio > bb_up.iloc[-1]:
            return "PUT", 0.85
        return "ESPERAR", 0

    @staticmethod
    def ruptura(df, lookback=20):
        """Ruptura de máximos/mínimos"""
        if len(df) < lookback + 2:
            return "ESPERAR", 0

        high_n = df['high'].iloc[-lookback:-1].max()
        low_n = df['low'].iloc[-lookback:-1].min()
        precio = df['close'].iloc[-1]

        if precio > high_n:
            return "CALL", 0.75
        elif precio < low_n:
            return "PUT", 0.75
        return "ESPERAR", 0

    @staticmethod
    def momentum(df):
        """Momentum con MACD + Stochastic + RSI"""
        macd_line, signal_line, hist = Indicadores.macd(df['close'])
        k, d = Indicadores.stochastic(df)
        rsi = Indicadores.rsi(df['close'])
        adx, plus_di, minus_di = Indicadores.adx(df)

        if len(macd_line) < 2:
            return "ESPERAR", 0

        macd_v = macd_line.iloc[-1]
        sig_v = signal_line.iloc[-1]
        k_v = k.iloc[-1]
        d_v = d.iloc[-1]
        rsi_v = rsi.iloc[-1]
        adx_v = adx.iloc[-1]

        if pd.isna(adx_v) or pd.isna(rsi_v):
            return "ESPERAR", 0

        if (macd_v > sig_v and k_v > d_v and rsi_v > 50 and adx_v > 20):
            return "CALL", 0.85
        elif (macd_v < sig_v and k_v < d_v and rsi_v < 50 and adx_v > 20):
            return "PUT", 0.85
        return "ESPERAR", 0

    @staticmethod
    def patrones(df):
        """Estrategia basada en patrones de velas"""
        patron_triple = AnalizadorVelas.patron_triple_vela(df)
        patron_doble = AnalizadorVelas.patron_doble_vela(df)
        anatomia = AnalizadorVelas.anatomia_vela(df)

        if patron_triple in ["ESTRELLA_MANANA", "TRES_SOLDADOS"]:
            return "CALL", 0.85
        elif patron_triple in ["ESTRELLA_ATARDECER", "TRES_CUERVOS"]:
            return "PUT", 0.85

        if patron_doble == "ENVOLVENTE_ALCISTA":
            return "CALL", 0.80
        elif patron_doble == "ENVOLVENTE_BAJISTA":
            return "PUT", 0.80

        if anatomia['martillo']:
            return "CALL", 0.70
        elif anatomia['estrella_fugaz']:
            return "PUT", 0.70

        return "ESPERAR", 0

    @staticmethod
    def scalping(df):
        """Scalping con momentum corto"""
        roc = df['close'].pct_change(3) * 100
        rsi = Indicadores.rsi(df['close'], 7)

        if len(roc) < 1 or len(rsi) < 1:
            return "ESPERAR", 0

        roc_v = roc.iloc[-1]
        rsi_v = rsi.iloc[-1]

        if roc_v > 0.05 and 50 < rsi_v < 65:
            return "CALL", 0.70
        elif roc_v < -0.05 and 35 < rsi_v < 50:
            return "PUT", 0.70
        return "ESPERAR", 0
