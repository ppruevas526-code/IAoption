"""
Bot de trading IA para IQ Option — punto de entrada.

Flujo:
1. Verifica dependencias y credenciales
2. Conecta con IQ Option
3. Analiza TODOS los activos disponibles
4. Muestra un ranking con señal y confianza
5. Te pregunta: qué activo operar y en qué dirección (CALL/PUT)
6. Comienza el bucle principal respetando tu elección
"""
import sys
import time

import config


# =============================================
# VERIFICAR DEPENDENCIAS
# =============================================
def verificar_dependencias():
    try:
        import pandas  # noqa: F401
        import numpy  # noqa: F401
        print("✅ Pandas y Numpy instalados correctamente")
    except ImportError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    try:
        from iqoptionapi.stable_api import IQ_Option  # noqa: F401
        print("✅ IQ Option API instalada correctamente")
    except ImportError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    try:
        from sklearn.ensemble import RandomForestClassifier  # noqa: F401
        print("✅ Scikit-learn disponible (IA activada)")
    except ImportError:
        print("⚠️ Scikit-learn no instalado. Usando IA interna simplificada.")
        print("   Instala con: pip install scikit-learn")


# =============================================
# PREGUNTAR DIRECCIÓN (CALL / PUT)
# =============================================
def pedir_direccion(activo, senal_sugerida):
    """
    Pregunta al usuario si quiere operar CALL (subida) o PUT (bajada).
    Muestra la sugerencia de la IA como referencia.
    """
    sugerida = "CALL" if senal_sugerida == "CALL" else "PUT"
    print("=" * 55)
    print(f"🎯 DIRECCIÓN DE LA OPERACIÓN PARA {activo}")
    print("=" * 55)
    print(f"  🤖 Sugerencia de la IA: {sugerida}")
    print()
    print("  1. 📈 CALL  (subida / compra)")
    print("  2. 📉 PUT   (bajada / venta)")
    print(f"  3. 🤖 Usar la sugerencia de la IA ({sugerida})")

    while True:
        opcion = input("\n👉 Elige la dirección (1/2/3): ").strip()
        if opcion == "1":
            print("✅ Dirección: CALL (subida)\n")
            return "call"
        elif opcion == "2":
            print("✅ Dirección: PUT (bajada)\n")
            return "put"
        elif opcion == "3":
            print(f"✅ Dirección: {sugerida} (sugerencia IA)\n")
            return sugerida.lower()
        else:
            print("❌ Opción inválida. Ingresa 1, 2 o 3.")


# =============================================
# ANALIZAR Y ELEGIR ACTIVO + DIRECCIÓN
# =============================================
def analizar_y_elegir(api, selector_ia, disponibilidad):
    """
    Analiza TODOS los activos disponibles, muestra un ranking con
    señal y confianza, y pregunta al usuario:
      1. En qué activo entrar
      2. Si quiere operar en CALL (subida) o PUT (bajada)
    Devuelve: (lista_de_activos, direccion_forzada_o_None)
    """
    from core.analysis import analizar_activo

    print("\n" + "=" * 55)
    print("🔎 ANALIZANDO ACTIVOS DISPONIBLES...")
    print("=" * 55)

    activos_operables = disponibilidad.obtener()
    if activos_operables:
        print(f"✅ Operables ahora: {sorted(activos_operables)}")
    else:
        print("🚫 Ningún activo configurado está operable en este momento.")

    resultados = []
    for activo in config.ACTIVOS_DISPONIBLES:
        try:
            velas = api.get_candles(
                activo, config.TIEMPO_VELA, config.CANTIDAD_VELAS, time.time()
            )
            if not velas or len(velas) < 30:
                print(f"⚠️ {activo}: pocas velas, saltando")
                continue

            resultado = analizar_activo(activo, velas, selector_ia)
            resultado['operable'] = activo in activos_operables
            resultados.append(resultado)

            estado = "✅ operable" if resultado['operable'] else "🚫 mercado cerrado"
            print(
                f"📊 {activo} | {resultado['señal']} "
                f"({resultado['confianza']*100:.0f}%) | {resultado['regimen']} | {estado}"
            )
        except Exception as e:
            print(f"❌ Error analizando {activo}: {e}")

    if not resultados:
        print("❌ No se pudo analizar ningún activo. Saliendo.")
        sys.exit(1)

    # Ranking: solo operables y con señal distinta de ESPERAR
    candidatos = [r for r in resultados if r['operable'] and r['señal'] != 'ESPERAR']
    candidatos.sort(key=lambda x: x['confianza'], reverse=True)

    print("\n" + "=" * 55)
    print("🎯 RANKING DE OPORTUNIDADES")
    print("=" * 55)

    if not candidatos:
        print("⏸️ Ningún activo muestra una señal clara en este momento.")
        print("   Se usarán todos los activos en modo vigilancia.\n")
        return config.ACTIVOS_DISPONIBLES, None

    for i, r in enumerate(candidatos, 1):
        print(
            f"  {i}. {r['activo']} → {r['señal']} "
            f"(confianza {r['confianza']*100:.0f}%) | {r['regimen']}"
        )

    print(f"  {len(candidatos)+1}. 🤖 Dejar que el bot elija automáticamente el mejor")
    print(f"  {len(candidatos)+2}. 👀 Vigilar todos los activos sin operar aún")

    # --- Elegir activo ---
    while True:
        try:
            opcion = input("\n👉 Elige el número de la opción a operar: ").strip()
            idx = int(opcion) - 1

            if 0 <= idx < len(candidatos):
                elegido = candidatos[idx]['activo']
                print(f"✅ Has elegido operar: {elegido}\n")
                direccion_forzada = pedir_direccion(elegido, candidatos[idx]['señal'])
                return [elegido], direccion_forzada

            elif idx == len(candidatos):
                elegido = candidatos[0]['activo']
                print(
                    f"🤖 El bot operará automáticamente: {elegido} "
                    f"({candidatos[0]['señal']})\n"
                )
                return [elegido], candidatos[0]['señal'].lower()

            elif idx == len(candidatos) + 1:
                print("👀 Modo vigilancia: se analizarán todos sin operar.\n")
                return config.ACTIVOS_DISPONIBLES, None

            else:
                print("❌ Número fuera de rango.")
        except ValueError:
            print("❌ Ingresa solo un número.")


# =============================================
# MAIN
# =============================================
def main():
    verificar_dependencias()

    if not config.EMAIL or not config.PASSWORD:
        print("\n❌ Faltan credenciales.")
        print("👉 Crea un archivo '.env' en la carpeta del bot con:")
        print("   IQ_EMAIL=tu_correo@gmail.com")
        print("   IQ_PASSWORD=tu_contraseña")
        sys.exit(1)

    # Imports que dependen de librerías ya verificadas
    from trading import broker
    from trading.signal_counter import ContadorSenales
    from trading.availability import DisponibilidadInstrumentos
    from trading.operations_manager import GestorOperaciones
    from core.ai_selector import SelectorEstrategiaIA
    from core.analysis import analizar_activo  # noqa: F401

    api, balance = broker.conectar(config.EMAIL, config.PASSWORD, config.MODO_REAL)
    broker.aplicar_parche_underlying_seguro(api)
    broker.instalar_excepthook_amigable()

    contador = ContadorSenales()
    contador.actualizar_balance(balance)

    selector_ia = SelectorEstrategiaIA()
    print(f"🧠 IA cargada con {len(selector_ia.rendimiento)} patrones aprendidos")

    disponibilidad = DisponibilidadInstrumentos(api, config.ACTIVOS_DISPONIBLES)

    # 🔥 Primero analiza todos los activos, luego te deja elegir
    config.ACTIVOS, direccion_forzada = analizar_y_elegir(
        api, selector_ia, disponibilidad
    )

    gestor_operaciones = GestorOperaciones(
        api, contador, selector_ia,
        monto=config.MONTO, duracion=config.DURACION,
        on_instrumento_invalido=lambda activo: disponibilidad.obtener(forzar=True),
    )

    print(f"\n🚀 BOT IA INICIADO")
    print(f"📊 Activos en seguimiento: {', '.join(config.ACTIVOS)}")
    if direccion_forzada:
        print(f"🎯 Dirección forzada: {direccion_forzada.upper()}")
    print(f"⏱️ Vela: {config.TIEMPO_VELA}s | Duración op: {config.DURACION} min")
    print(f"🧠 Estrategias IA: {list(selector_ia.estrategias.keys())}")
    print(f"🎯 Confianza mínima: {config.MIN_CONFIANZA_IA*100:.0f}%")
    print("⏳ Comenzando en 5 segundos... (Ctrl+C para detener)")
    time.sleep(5)

    detenido_por_limite = False

    # =============================================
    # BUCLE PRINCIPAL
    # =============================================
    while True:
        try:
            if not broker.verificar_reconectar(api):
                time.sleep(5)
                continue

            activos_operables = disponibilidad.obtener()
            if activos_operables:
                print(f"✅ Operables ahora: {sorted(activos_operables)}")
            else:
                print("🚫 Ningún activo configurado está operable en este momento.")

            analisis_activos = []

            for activo in config.ACTIVOS:
                try:
                    velas = api.get_candles(
                        activo, config.TIEMPO_VELA, config.CANTIDAD_VELAS, time.time()
                    )
                    if not velas or len(velas) < 30:
                        print(f"⚠️ {activo}: pocas velas, saltando")
                        continue

                    resultado = analizar_activo(activo, velas, selector_ia)
                    analisis_activos.append(resultado)

                    hora = time.strftime('%H:%M:%S')
                    ocupado = (
                        " (operación en curso)"
                        if gestor_operaciones.esta_ocupado(activo)
                        else ""
                    )
                    print(
                        f"📊 {hora} | {activo} | {resultado['precio']:.5f} | "
                        f"{resultado['señal']} ({resultado['confianza']*100:.0f}%) | "
                        f"Régimen: {resultado['regimen']} | "
                        f"Estrategia: {resultado['estrategia']}{ocupado}"
                    )

                    contador.registrar_senal(
                        activo, resultado['señal'], resultado['precio'],
                        hora, resultado['regimen'], resultado['estrategia'],
                        resultado['confianza']
                    )
                except Exception as e:
                    print(f"❌ Error analizando {activo}: {e}")

            stats = contador.obtener_estadisticas()
            if stats['total_senales'] % 5 == 0 and stats['total_senales'] > 0:
                contador.mostrar_estadisticas()

            # oportunidades = [
            #     a for a in analisis_activos
            #     if a['señal'] != 'ESPERAR'
            #     and a['confianza'] >= config.MIN_CONFIANZA_IA
            #     and not gestor_operaciones.esta_ocupado(a['activo'])
            #     and a['activo'] in activos_operables
            # ]

            oportunidades = [
                    a for a in analisis_activos
                    if not gestor_operaciones.esta_ocupado(a['activo'])
                    and a['activo'] in activos_operables
                    ]

            bloqueadas_por_mercado = [
                a for a in analisis_activos
                if a['señal'] != 'ESPERAR'
                and a['confianza'] >= config.MIN_CONFIANZA_IA
                and a['activo'] not in activos_operables
            ]
            for b in bloqueadas_por_mercado:
                print(
                    f"⏭️ {b['activo']}: señal {b['señal']} "
                    f"({b['confianza']*100:.0f}%) válida pero el mercado "
                    f"está cerrado para este instrumento, se omite."
                )

            if oportunidades:
                oportunidades.sort(key=lambda x: x['confianza'], reverse=True)

                if contador.limite_perdida_alcanzado():
                    print("⚠️ Límite de pérdida diaria alcanzado. "
                          "No se abren nuevas operaciones.")
                    detenido_por_limite = True
                elif contador.limite_operaciones_alcanzado():
                    print("⚠️ Límite de operaciones diarias alcanzado. "
                          "No se abren nuevas operaciones.")
                    detenido_por_limite = True
                else:
                    for op in oportunidades:
                        if (contador.limite_operaciones_alcanzado()
                                or contador.limite_perdida_alcanzado()):
                            break

                        # 👇 Si el usuario forzó dirección, se respeta
                        if direccion_forzada:
                            direccion = direccion_forzada
                            print(
                                f"\n🎯 OPORTUNIDAD: {op['activo']} → "
                                f"{direccion.upper()} (forzada por ti)"
                            )
                        else:
                            direccion = "call" if op['señal'] == "CALL" else "put"
                            print(
                                f"\n🎯 OPORTUNIDAD: {op['activo']} → {op['señal']} "
                                f"(confianza {op['confianza']*100:.0f}%)"
                            )

                        contador.registrar_operacion_iniciada()
                        gestor_operaciones.lanzar_operacion(
                            op['activo'], direccion, op['precio'],
                            op['regimen'], op['estrategia']
                        )
            else:
                print(
                    f"⏸️ Sin oportunidades nuevas "
                    f"(confianza mínima {config.MIN_CONFIANZA_IA*100:.0f}%)"
                )

            if detenido_por_limite:
                print("🧭 Esperando a que cierren las operaciones abiertas "
                      "antes de detener el bot...")
                gestor_operaciones.esperar_pendientes()
                break

            ahora = time.time()
            siguiente_cierre = ((ahora // config.TIEMPO_VELA) + 1) * config.TIEMPO_VELA
            espera = siguiente_cierre - ahora
            if espera > 0:
                print(f"⏳ Esperando {espera:.1f} segundos...\n")
                time.sleep(espera + 0.5)

        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario")
            contador.mostrar_estadisticas()
            print("🧭 Esperando a que cierren las operaciones en curso "
                  "(Ctrl+C de nuevo para forzar salida)...")
            try:
                gestor_operaciones.esperar_pendientes()
            except KeyboardInterrupt:
                print("⚠️ Saliendo sin esperar el cierre de operaciones abiertas.")
            print(f"\n🧠 IA aprendió {len(selector_ia.rendimiento)} "
                  f"combinaciones régimen/estrategia")
            break
        except Exception as e:
            print(f"❌ ERROR: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()