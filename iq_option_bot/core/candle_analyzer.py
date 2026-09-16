"""Analiza patrones, anatomía y estructura de velas japonesas."""


class AnalizadorVelas:
    """Analiza patrones, anatomía y estructura de velas"""

    @staticmethod
    def anatomia_vela(df):
        """Analiza la forma de la última vela"""
        v = df.iloc[-1]
        cuerpo = abs(v['close'] - v['open'])
        rango = v['high'] - v['low']
        mecha_sup = v['high'] - max(v['close'], v['open'])
        mecha_inf = min(v['close'], v['open']) - v['low']

        return {
            'cuerpo_pct': (cuerpo / rango * 100) if rango > 0 else 0,
            'mecha_sup_pct': (mecha_sup / rango * 100) if rango > 0 else 0,
            'mecha_inf_pct': (mecha_inf / rango * 100) if rango > 0 else 0,
            'alcista': v['close'] > v['open'],
            'cuerpo_grande': cuerpo > (rango * 0.6),
            'cuerpo_pequeno': cuerpo < (rango * 0.2),
            'doji': cuerpo < (rango * 0.1) if rango > 0 else False,
            'martillo': (mecha_inf > cuerpo * 2) and (mecha_sup < cuerpo * 0.5),
            'estrella_fugaz': (mecha_sup > cuerpo * 2) and (mecha_inf < cuerpo * 0.5),
        }

    @staticmethod
    def patron_doble_vela(df):
        """Detecta patrones de 2 velas (envolvente, harami, etc.)"""
        if len(df) < 3:
            return None

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        prev_cuerpo = abs(prev['close'] - prev['open'])
        curr_cuerpo = abs(curr['close'] - curr['open'])

        if (prev['close'] < prev['open'] and curr['close'] > curr['open'] and
                curr['close'] > prev['open'] and curr['open'] < prev['close']):
            return "ENVOLVENTE_ALCISTA"

        if (prev['close'] > prev['open'] and curr['close'] < curr['open'] and
                curr['close'] < prev['open'] and curr['open'] > prev['close']):
            return "ENVOLVENTE_BAJISTA"

        if curr['high'] < prev['high'] and curr['low'] > prev['low']:
            if curr_cuerpo < prev_cuerpo * 0.5:
                return "HARAMI"

        return None

    @staticmethod
    def patron_triple_vela(df):
        """Detecta patrones de 3 velas (estrella mañana/tarde, 3 soldados)"""
        if len(df) < 4:
            return None

        v1, v2, v3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]

        if (v1['close'] < v1['open'] and
                abs(v2['close'] - v2['open']) < abs(v1['close'] - v1['open']) * 0.5 and
                v3['close'] > v3['open'] and v3['close'] > (v1['open'] + v1['close']) / 2):
            return "ESTRELLA_MANANA"

        if (v1['close'] > v1['open'] and
                abs(v2['close'] - v2['open']) < abs(v1['close'] - v1['open']) * 0.5 and
                v3['close'] < v3['open'] and v3['close'] < (v1['open'] + v1['close']) / 2):
            return "ESTRELLA_ATARDECER"

        if all(v['close'] > v['open'] for v in [v1, v2, v3]):
            if v2['close'] > v1['close'] and v3['close'] > v2['close']:
                return "TRES_SOLDADOS"

        if all(v['close'] < v['open'] for v in [v1, v2, v3]):
            if v2['close'] < v1['close'] and v3['close'] < v2['close']:
                return "TRES_CUERVOS"

        return None

    @staticmethod
    def estructura_mercado(df, lookback=20):
        """Detecta si hay tendencia o rango"""
        highs = df['high'].iloc[-lookback:].values
        lows = df['low'].iloc[-lookback:].values

        swing_highs, swing_lows = [], []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and \
                    highs[i] > highs[i + 1] and highs[i] > highs[i + 2]:
                swing_highs.append(highs[i])
            if lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and \
                    lows[i] < lows[i + 1] and lows[i] < lows[i + 2]:
                swing_lows.append(lows[i])

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            hh = swing_highs[-1] > swing_highs[-2]
            hl = swing_lows[-1] > swing_lows[-2]
            lh = swing_highs[-1] < swing_highs[-2]
            ll = swing_lows[-1] < swing_lows[-2]

            if hh and hl:
                return "TENDENCIA_ALCISTA"
            elif lh and ll:
                return "TENDENCIA_BAJISTA"

        return "RANGO"
