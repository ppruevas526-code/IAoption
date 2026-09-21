"""
Lleva el registro de qué activos tienen una operación en curso y
lanza/gestiona los hilos que esperan el resultado, sin bloquear
el bucle principal de análisis.
"""
import threading
import time
import traceback

from utils.errors import formatear_error_orden


class GestorOperaciones:
    def __init__(self, api, contador, selector_ia, monto, duracion,
                 on_instrumento_invalido=None):
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
            print(f"\n{'='*55}")
            print(f"🚀 INTENTANDO OPERAR: {direccion.upper()} en {activo}")
            print(f"   Precio: {precio:.5f}")
            print(f"   Monto: {self.monto} | Duración: {self.duracion} min")
            print(f"   Régimen: {regimen} | Estrategia: {estrategia}")
            print(f"{'='*55}")

            # --- Paso 1: Intentar abrir la orden ---
            try:
                print("📤 Enviando orden a IQ Option...")
                status, orden_id = self.api.buy(
                    self.monto, activo, direccion, self.duracion
                )
                print(f"📥 Respuesta de IQ Option: status={status}, id={orden_id}")
            except Exception as e:
                print(f"❌ EXCEPCIÓN al ejecutar: {type(e).__name__}: {e}")
                traceback.print_exc()
                return

            # --- Paso 2: Verificar si la orden se abrió ---
            if not status:
                mensaje_legible = formatear_error_orden(orden_id)
                print(f"❌ ORDEN RECHAZADA en {activo}: {mensaje_legible}")
                print(f"   Respuesta cruda: {orden_id}")

                if isinstance(orden_id, dict) and \
                        str(orden_id.get('message', '')).strip().lower() == 'invalid instrument':
                    if self.on_instrumento_invalido:
                        try:
                            self.on_instrumento_invalido(activo)
                        except Exception:
                            pass
                return

            print(f"✅ ORDEN ABIERTA en {activo} | ID: {orden_id}")
            print(f"⏳ Esperando {self.duracion} min para que cierre...")

            # --- Paso 3: Esperar cierre ---
            tiempo_espera = self.duracion * 60 + 5
            time.sleep(tiempo_espera)
            print(f"⏰ Tiempo de espera terminado. Consultando resultado...")

            # --- Paso 4: Consultar resultado ---
            try:
                check_close, win_money = self.api.check_win_v2(orden_id)
                print(f"📥 Resultado: check_close={check_close}, win_money={win_money}")
            except Exception as e:
                print(f"❌ EXCEPCIÓN al consultar resultado: {type(e).__name__}: {e}")
                traceback.print_exc()
                return

            if not check_close:
                print(f"⚠️ No se pudo confirmar el cierre de la orden {orden_id}")
                return

            # --- Paso 5: Registrar resultado ---
            gano = float(win_money) > 0
            if gano:
                print(f"💰 ¡GANANCIA en {activo}! +{win_money:.2f} USD")
                self.contador.registrar_resultado_operacion(
                    activo, direccion, precio, orden_id, "ganada", float(win_money)
                )
            else:
                print(f"📉 Pérdida en {activo}: {self.monto:.2f} USD")
                self.contador.registrar_resultado_operacion(
                    activo, direccion, precio, orden_id, "perdida", self.monto
                )

            print(f"🧠 Registrando resultado en la IA...")
            self.selector_ia.registrar_resultado(regimen, estrategia, gano)
            print(f"✅ Resultado registrado en la IA")

            nuevo_balance = self.api.get_balance()
            if nuevo_balance:
                self.contador.actualizar_balance(nuevo_balance)
                print(f"💰 Balance actual: {nuevo_balance:.2f} USD")

        except Exception as e:
            print(f"⚠️ ERROR GENERAL en hilo de operación de {activo}:")
            print(f"   {type(e).__name__}: {e}")
            traceback.print_exc()
        finally:
            self._liberar(activo)
            print(f"🔓 Activo {activo} liberado\n")

    def esperar_pendientes(self, timeout=None):
        """Usado al apagar el bot: espera a que los hilos en vuelo terminen."""
        with self._lock:
            hilos = list(self._hilos)
        for h in hilos:
            h.join(timeout=timeout)