"""
Disponibilidad de instrumentos.

Consulta a IQ Option qué activos están operables. Si la API falla o tarda
demasiado (problema conocido con activos digitales), se asume que TODOS
los activos configurados están disponibles para no bloquear el bot.
"""
import time
import threading


class DisponibilidadInstrumentos:
    def __init__(self, api, activos, cache_segundos=300):
        self.api = api
        self.activos = activos
        self.cache_segundos = cache_segundos
        self._ultima_consulta = 0
        self._cache = None
        self._lock = threading.Lock()

    def _consultar(self):
        """Consulta los activos disponibles con timeout de seguridad."""
        resultado = set()
        try:
            # Intentar la consulta normal con timeout usando un hilo
            contenedor = {"data": None, "error": None}

            def consulta():
                try:
                    contenedor["data"] = self.api.get_all_init_v2()
                except Exception as e:
                    contenedor["error"] = e

            hilo = threading.Thread(target=consulta, daemon=True)
            hilo.start()
            hilo.join(timeout=15)  # 15 segundos máximo

            if hilo.is_alive():
                # Timeout: asumimos que todos están disponibles
                print("⚠️ Timeout consultando disponibilidad. Usando activos configurados.")
                return set(self.activos)

            if contenedor["data"]:
                # Parsear estructura típica de IQ Option
                try:
                    activos_data = contenedor["data"].get("result", {}).get("actives", {})
                    for tipo, activos_tipo in activos_data.items():
                        if isinstance(activos_tipo, dict):
                            for nombre in activos_tipo.keys():
                                resultado.add(nombre.upper())
                except Exception:
                    pass

        except Exception as e:
            print(f"⚠️ Error consultando disponibilidad: {e}")

        # Si no obtuvimos nada útil, devolver los activos configurados
        if not resultado:
            print("ℹ️ Sin respuesta de disponibilidad. Asumiendo activos configurados como operables.")
            return set(self.activos)

        return resultado

    def obtener(self, forzar=False):
        """Devuelve un set de activos operables, usando caché."""
        with self._lock:
            ahora = time.time()
            if (not forzar and self._cache is not None
                    and (ahora - self._ultima_consulta) < self.cache_segundos):
                return self._cache

            self._cache = self._consultar()
            self._ultima_consulta = ahora
            return self._cache