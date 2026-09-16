"""Calcula indicadores técnicos sin dependencias externas de TA-Lib."""
import pandas as pd


class Indicadores:
    """Calcula indicadores técnicos sin dependencias externas"""

    @staticmethod
    def ema(series, period):
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(series, period=14):
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = -delta.where(delta < 0, 0).rolling(period).mean()
        rs = gain / loss.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def atr(df, period=14):
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    @staticmethod
    def adx(df, period=14):
        high, low, close = df['high'], df['low'], df['close']
        plus_dm = high.diff().clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)

        tr = Indicadores.atr(df, period)
        plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / tr)
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-10)
        return dx.rolling(period).mean(), plus_di, minus_di

    @staticmethod
    def bollinger(series, period=20, std_dev=2):
        ma = series.rolling(period).mean()
        std = series.rolling(period).std()
        return ma + std * std_dev, ma, ma - std * std_dev

    @staticmethod
    def macd(series, fast=12, slow=26, signal=9):
        ema_fast = Indicadores.ema(series, fast)
        ema_slow = Indicadores.ema(series, slow)
        macd_line = ema_fast - ema_slow
        signal_line = Indicadores.ema(macd_line, signal)
        hist = macd_line - signal_line
        return macd_line, signal_line, hist

    @staticmethod
    def stochastic(df, k_period=14, d_period=3):
        low_min = df['low'].rolling(k_period).min()
        high_max = df['high'].rolling(k_period).max()
        k = 100 * (df['close'] - low_min) / (high_max - low_min).replace(0, 1e-10)
        d = k.rolling(d_period).mean()
        return k, d
