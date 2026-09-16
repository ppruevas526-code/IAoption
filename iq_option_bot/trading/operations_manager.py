"""
Lleva el registro de qué activos tienen una operación en curso y
lanza/gestiona los hilos que esperan el resultado, sin bloquear
el bucle principal de análisis.
"""
import threading
import time

from utils.errors import formatear_error_orden


class GestorOperaciones:
    def __init__(self, api, contador, selector_ia, monto, duracion,
                 on_instrumento_invalido=None):
        """
        on_instrumento_invalido: callback opcional (activo) -> None,
        usado para forzar un refresco de disponibilidad cuando la API
        rechaza una orden por "invalid instrument".
        """
        self.api = api
        self.contador = contador
        self.selector_ia = selector_ia
        self.monto = monto
        self.duracion = duracion
        self.on_instrumento_invalido = on_instrumento_invalido

        self._lock = threading.Lock()
        self._activos_ocupados = set()
        self._hilos = []

    def esta_ocupado(self, activo):
        with self._lock:
            return activo in self._activos_ocupados

    def _marcar_ocupado(self, activo):
        with self._lock:
            self._activos_ocupados.add(activo)

    def _liberar(self, activo):
        with self._lock:
            self._activos_ocupados.discard(activo)

    def lanzar_operacion(self, activo, direccion, precio, regimen, estrategia):
        """Lanza la operación en un hilo aparte y retorna inmediatamente."""
        self._marcar_ocupado(activo)
        hilo = threading.Thread(
            target=self._ejecutar_y_esperar,
            args=(activo, direccion, precio, regimen, estrategia),
            daemon=True,
        )
        with self._lock:
            self._hilos.append(hilo)
        hilo.start()

    def _ejecutar_y_esperar(self, activo, direccion, precio, regimen, estrategia):
        """Corre en un hilo de fondo: abre la orden, espera su cierre
        y registra el resultado, sin bloquear el análisis de otros pares."""
        try:
            print(f"🚀 EJECUTANDO {direccion.upper()} en {activo} @ {precio:.5f}")
            print(f"   🧠 Régimen: {regimen} | Estrategia: {estrategia}")

            try:
                status, orden_id = self.api.buy_digital_spot_v2(activo, self.monto, direccion, self.duracion)
            except Exception as e:
                print(f"❌ Error al ejecutar en {activo}: {e}")
                return

            if not status:
                mensaje_legible = formatear_error_orden(orden_id)
                print(f"❌ No se pudo abrir la orden en {activo}: {mensaje_legible}")

                if isinstance(orden_id, dict) and \
                        str(orden_id.get('message', '')).strip().lower() == 'invalid instrument':
                    if self.on_instrumento_invalido:
                        try:
                            self.on_instrumento_invalido(activo)
                        except Exception:
                            pass
                return

            print(f"✅ Orden enviada en {activo} | ID: {orden_id}")
            time.sleep(self.duracion * 60 + 5)

            check_close, win_money = self.api.check_win_digital_v2(orden_id)
            if not check_close:
                print(f"⚠️ {activo}: no se pudo confirmar el cierre de la orden {orden_id}")
                return

            gano = float(win_money) > 0
            if gano:
                print(f"💰 ¡GANANCIA en {activo}! +{win_money:.2f} USD")
                self.contador.registrar_resultado_operacion(activo, direccion, precio, orden_id, "ganada", float(win_money))
            else:
                print(f"📉 Pérdida en {activo}: {self.monto:.2f} USD")
                self.contador.registrar_resultado_operacion(activo, direccion, precio, orden_id, "perdida", self.monto)

            self.selector_ia.registrar_resultado(regimen, estrategia, gano)

            nuevo_balance = self.api.get_balance()
            if nuevo_balance:
                self.contador.actualizar_balance(nuevo_balance)
                print(f"💰 Balance actual: {nuevo_balance:.2f} USD")

        except Exception as e:
            print(f"⚠️ Error en hilo de operación de {activo}: {e}")
        finally:
            self._liberar(activo)

    def esperar_pendientes(self, timeout=None):
        """Usado al apagar el bot: espera a que los hilos en vuelo terminen."""
        with self._lock:
            hilos = list(self._hilos)
        for h in hilos:
            h.join(timeout=timeout)
