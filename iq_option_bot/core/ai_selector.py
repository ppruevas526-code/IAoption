"""
Selector inteligente que aprende qué estrategia funciona mejor
según el régimen de mercado, guardando el historial en un JSON.
"""
import json
import os
import threading

from core.strategies import Estrategias
import config


class SelectorEstrategiaIA:
    """
    Selector inteligente que aprende qué estrategia funciona
    mejor según el régimen de mercado.
    """

    def __init__(self, archivo_memoria=None):
        self.archivo = archivo_memoria or config.ARCHIVO_MEMORIA_IA
        os.makedirs(os.path.dirname(self.archivo) or ".", exist_ok=True)
        self.memoria = self._cargar_memoria()
        self.rendimiento = self.memoria.get('rendimiento', {})
        self._lock = threading.Lock()

        self.estrategias = {
            'tendencia': Estrategias.tendencia,
            'reversion': Estrategias.reversion_media,
            'ruptura': Estrategias.ruptura,
            'momentum': Estrategias.momentum,
            'patrones': Estrategias.patrones,
            'scalping': Estrategias.scalping,
        }

    def _cargar_memoria(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ No se pudo leer memoria IA existente: {e}")
        return {'rendimiento': {}, 'operaciones': []}

    def _guardar_memoria(self):
        tmp = f"{self.archivo}.tmp"
        try:
            with open(tmp, 'w') as f:
                json.dump(self.memoria, f, indent=2)
            os.replace(tmp, self.archivo)
        except Exception as e:
            print(f"⚠️ No se pudo guardar memoria IA: {e}")

    def seleccionar(self, regimen):
        recomendadas = {
            "TENDENCIA_ALCISTA": ['tendencia', 'momentum', 'ruptura'],
            "TENDENCIA_BAJISTA": ['tendencia', 'momentum', 'ruptura'],
            "RANGO": ['reversion', 'patrones', 'scalping'],
            "VOLATIL": ['ruptura', 'momentum', 'patrones'],
            "NORMAL": ['tendencia', 'patrones', 'momentum'],
            "DESCONOCIDO": ['tendencia', 'patrones', 'momentum'],
        }

        candidatas = recomendadas.get(regimen, list(self.estrategias.keys()))
        mejor_estrategia = candidatas[0]
        mejor_score = -1

        with self._lock:
            for nombre in candidatas:
                clave = f"{regimen}::{nombre}"
                stats = self.rendimiento.get(clave, {'wins': 0, 'total': 0})
                if stats['total'] >= 3:
                    win_rate = stats['wins'] / stats['total']
                    score = win_rate
                else:
                    score = 0.5 - (candidatas.index(nombre) * 0.05)
                if score > mejor_score:
                    mejor_score = score
                    mejor_estrategia = nombre

        return mejor_estrategia, mejor_score

    def analizar_con_ia(self, df, regimen):
        mejor_nombre, _ = self.seleccionar(regimen)
        señales = {}
        for nombre, func in self.estrategias.items():
            try:
                señal, conf = func(df)
                señales[nombre] = {'señal': señal, 'conf': conf}
            except Exception:
                señales[nombre] = {'señal': 'ESPERAR', 'conf': 0}

        votos_call = 0
        votos_put = 0
        total_peso = 0

        with self._lock:
            for nombre, data in señales.items():
                if data['señal'] == 'ESPERAR':
                    continue
                clave = f"{regimen}::{nombre}"
                stats = self.rendimiento.get(clave, {'wins': 0, 'total': 0})
                if stats['total'] >= 3:
                    peso = stats['wins'] / stats['total']
                else:
                    peso = 0.5
                if nombre == mejor_nombre:
                    peso *= 1.3
                peso *= data['conf']
                total_peso += peso
                if data['señal'] == 'CALL':
                    votos_call += peso
                else:
                    votos_put += peso

        if total_peso == 0:
            return "ESPERAR", 0, mejor_nombre, señales
        if votos_call > votos_put:
            return "CALL", votos_call / total_peso, mejor_nombre, señales
        elif votos_put > votos_call:
            return "PUT", votos_put / total_peso, mejor_nombre, señales
        return "ESPERAR", 0, mejor_nombre, señales

    def registrar_resultado(self, regimen, estrategia, gano):
        clave = f"{regimen}::{estrategia}"
        with self._lock:
            if clave not in self.rendimiento:
                self.rendimiento[clave] = {'wins': 0, 'total': 0}
            self.rendimiento[clave]['total'] += 1
            if gano:
                self.rendimiento[clave]['wins'] += 1
            self.memoria['rendimiento'] = self.rendimiento
            wins = self.rendimiento[clave]['wins']
            total = self.rendimiento[clave]['total']
            self._guardar_memoria()
        win_rate = wins / total
        print(f"🧠 IA aprendió: {clave} → {win_rate*100:.0f}% éxito ({wins}/{total})")