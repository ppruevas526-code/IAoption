"""
Disponibilidad de instrumentos.

Consulta a IQ Option qué activos están realmente disponibles
para operar.

IMPORTANTE:
Si IQ Option no responde o no se puede comprobar la disponibilidad,
NO se asume que el activo está disponible.
"""

import time
import threading


class DisponibilidadInstrumentos:

    def __init__(self, api, activos, cache_segundos=60):
        self.api = api
        self.activos = activos
        self.cache_segundos = cache_segundos

        self._ultima_consulta = 0
        self._cache = None
        self._lock = threading.Lock()

    def _consultar(self):
        """Consulta los activos disponibles en IQ Option."""

        resultado = set()

        try:
            contenedor = {
                "data": None,
                "error": None
            }

            def consulta():
                try:
                    contenedor["data"] = self.api.get_all_init_v2()
                except Exception as e:
                    contenedor["error"] = e

            hilo = threading.Thread(
                target=consulta,
                daemon=True
            )

            hilo.start()
            hilo.join(timeout=15)

            # ---------------------------------------------------------
            # TIMEOUT
            # ---------------------------------------------------------

            if hilo.is_alive():
                print(
                    "⚠️ Timeout consultando disponibilidad "
                    "de IQ Option."
                )

                # NO asumir que los activos están disponibles.
                return set()

            # ---------------------------------------------------------
            # ERROR DE API
            # ---------------------------------------------------------

            if contenedor["error"] is not None:
                print(
                    f"⚠️ Error consultando disponibilidad: "
                    f"{contenedor['error']}"
                )
                return set()

            data = contenedor["data"]

            # ---------------------------------------------------------
            # DEBUG
            # ---------------------------------------------------------

            print("\n🔍 DEBUG IQ OPTION")

            print(
                f"Tipo de respuesta: {type(data)}"
            )

            if isinstance(data, dict):
                print(
                    f"Claves principales: {list(data.keys())}"
                )

            # ---------------------------------------------------------
            # VALIDAR RESPUESTA
            # ---------------------------------------------------------

            if not isinstance(data, dict):
                print(
                    "⚠️ IQ Option no devolvió datos válidos "
                    "de disponibilidad."
                )
                return set()

            # ---------------------------------------------------------
            # REVISAR TIPOS DE OPCIONES
            # ---------------------------------------------------------

            for tipo in ("binary", "turbo"):

                print(
                    f"\n🔍 Revisando tipo: {tipo}"
                )

                bloque = data.get(tipo, {})

                if not isinstance(bloque, dict):
                    print(
                        f"   ⚠️ {tipo} no contiene un bloque válido."
                    )
                    continue

                actives = bloque.get("actives", {})

                if not isinstance(actives, dict):
                    print(
                        f"   ⚠️ {tipo}.actives no es válido."
                    )
                    continue

                print(
                    f"   Activos encontrados: {len(actives)}"
                )

                # -----------------------------------------------------
                # RECORRER ACTIVOS
                # -----------------------------------------------------

                for _, activo in actives.items():

                    if not isinstance(activo, dict):
                        continue

                    nombre = activo.get("name")

                    if not nombre:
                        continue

                    nombre = str(nombre).split(".")[-1].upper()

                    enabled = activo.get(
                        "enabled",
                        False
                    )

                    suspended = activo.get(
                        "is_suspended",
                        True
                    )

                    # -------------------------------------------------
                    # DEBUG SOLO PARA LOS ACTIVOS CONFIGURADOS
                    # -------------------------------------------------

                    if nombre in self.activos:

                        print(
                            f"🔎 {nombre}: "
                            f"enabled={enabled}, "
                            f"suspended={suspended}"
                        )

                    # -------------------------------------------------
                    # ACTIVO OPERABLE
                    # -------------------------------------------------

                    if (
                        nombre in self.activos
                        and bool(enabled)
                        and not bool(suspended)
                    ):
                        resultado.add(nombre)

            # ---------------------------------------------------------
            # RESULTADO
            # ---------------------------------------------------------

            if resultado:

                print(
                    "\n✅ ACTIVOS REALMENTE OPERABLES:"
                )

                print(
                    "   " + ", ".join(sorted(resultado))
                )

            else:

                print(
                    "\n⚠️ IQ Option no reportó ningún "
                    "activo configurado como operable."
                )

            return resultado

        except Exception as e:

            print(
                f"⚠️ Error inesperado consultando "
                f"disponibilidad: {type(e).__name__}: {e}"
            )

            return set()

    def obtener(self, forzar=False):
        """
        Devuelve los activos operables utilizando caché.
        """

        with self._lock:

            ahora = time.time()

            # ---------------------------------------------------------
            # UTILIZAR CACHÉ
            # ---------------------------------------------------------

            if (
                not forzar
                and self._cache is not None
                and (
                    ahora - self._ultima_consulta
                ) < self.cache_segundos
            ):

                return self._cache

            # ---------------------------------------------------------
            # NUEVA CONSULTA
            # ---------------------------------------------------------

            self._cache = self._consultar()

            self._ultima_consulta = ahora

            return self._cache