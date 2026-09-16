"""Registro thread-safe de señales, operaciones y estadísticas del bot."""
import threading
from datetime import datetime

import config


class ContadorSenales:
    def __init__(self, max_operaciones_dia=None, max_perdida_diaria=None):
        self.max_operaciones_dia = max_operaciones_dia or config.MAX_OPERACIONES_POR_DIA
        self.max_perdida_diaria = max_perdida_diaria or config.MAX_PERDIDA_DIARIA

        self._lock = threading.Lock()
        self.total_senales = 0
        self.senales_call = 0
        self.senales_put = 0
        self.senales_esperar = 0
        self.operaciones_ejecutadas = 0
        self.operaciones_ganadas = 0
        self.operaciones_perdidas = 0
        self.ganancia_total = 0.0
        self.perdida_total = 0.0
        self.balance_inicial = 0.0
        self.balance_actual = 0.0
        self.historial_senales = []
        self.historial_operaciones = []

    def registrar_senal(self, activo, tipo, precio, hora, regimen, estrategia, confianza):
        with self._lock:
            self.total_senales += 1
            if tipo == "CALL":
                self.senales_call += 1
            elif tipo == "PUT":
                self.senales_put += 1
            else:
                self.senales_esperar += 1

            self.historial_senales.append({
                'fecha': hora,
                'activo': activo,
                'tipo': tipo,
                'precio': precio,
                'regimen': regimen,
                'estrategia': estrategia,
                'confianza': confianza
            })

            if len(self.historial_senales) > 200:
                self.historial_senales.pop(0)

            return self.total_senales

    def registrar_operacion_iniciada(self):
        """Reserva un slot de operación en el momento de lanzarla
        (no cuando termina), para que el límite diario se respete
        aunque haya varias operaciones en vuelo a la vez."""
        with self._lock:
            self.operaciones_ejecutadas += 1
            return self.operaciones_ejecutadas

    def registrar_resultado_operacion(self, activo, direccion, precio, orden_id, resultado, ganancia):
        with self._lock:
            if resultado == "ganada":
                self.operaciones_ganadas += 1
                self.ganancia_total += ganancia
            elif resultado == "perdida":
                self.operaciones_perdidas += 1
                self.perdida_total += abs(ganancia)

            self.historial_operaciones.append({
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'activo': activo,
                'direccion': direccion,
                'precio': precio,
                'orden_id': orden_id,
                'resultado': resultado,
                'ganancia': ganancia
            })

            if len(self.historial_operaciones) > 200:
                self.historial_operaciones.pop(0)

            return self.perdida_total

    def actualizar_balance(self, balance):
        with self._lock:
            if self.balance_inicial == 0:
                self.balance_inicial = balance
            self.balance_actual = balance

    def limite_operaciones_alcanzado(self):
        with self._lock:
            return self.operaciones_ejecutadas >= self.max_operaciones_dia

    def limite_perdida_alcanzado(self):
        with self._lock:
            return self.perdida_total >= self.max_perdida_diaria

    def mostrar_estadisticas(self):
        stats = self.obtener_estadisticas()
        print("\n" + "=" * 50)
        print("📊 ESTADÍSTICAS DEL BOT")
        print("=" * 50)
        print(f"🔹 SEÑALES TOTALES: {stats['total_senales']}")
        print(f"   • CALL: {stats['senales_call']} | PUT: {stats['senales_put']} | ESPERAR: {stats['senales_esperar']}")
        print("-" * 50)
        print(f"🔹 OPERACIONES: {stats['operaciones_ejecutadas']}")
        print(f"   • Ganadas: {stats['operaciones_ganadas']} | Perdidas: {stats['operaciones_perdidas']}")
        print(f"   • Tasa de aciertos: {stats['tasa_aciertos']}%")
        print("-" * 50)
        print(f"🔹 FINANZAS:")
        print(f"   • Ganancia total: +${stats['ganancia_total']}")
        print(f"   • Pérdida total: -${stats['perdida_total']}")
        print(f"   • Beneficio neto: ${stats['beneficio_neto']}")
        print(f"   • Beneficio %: {stats['beneficio_porcentaje']}%")
        print("-" * 50)
        print(f"🔹 BALANCE:")
        print(f"   • Inicial: ${stats['balance_inicial']} | Actual: ${stats['balance_actual']}")
        print("=" * 50 + "\n")

    def obtener_estadisticas(self):
        with self._lock:
            tasa = 0
            if self.operaciones_ejecutadas > 0:
                tasa = (self.operaciones_ganadas / self.operaciones_ejecutadas) * 100

            neto = self.ganancia_total - self.perdida_total
            pct = 0
            if self.balance_inicial > 0:
                pct = (neto / self.balance_inicial) * 100

            return {
                'total_senales': self.total_senales,
                'senales_call': self.senales_call,
                'senales_put': self.senales_put,
                'senales_esperar': self.senales_esperar,
                'operaciones_ejecutadas': self.operaciones_ejecutadas,
                'operaciones_ganadas': self.operaciones_ganadas,
                'operaciones_perdidas': self.operaciones_perdidas,
                'tasa_aciertos': round(tasa, 2),
                'ganancia_total': round(self.ganancia_total, 2),
                'perdida_total': round(self.perdida_total, 2),
                'beneficio_neto': round(neto, 2),
                'beneficio_porcentaje': round(pct, 2),
                'balance_inicial': round(self.balance_inicial, 2),
                'balance_actual': round(self.balance_actual, 2)
            }
