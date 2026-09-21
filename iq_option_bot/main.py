"""
Bot de trading IA para IQ Option — punto de entrada.
"""
import sys
import time
import random

import config


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


def pedir_direccion(activo, senal_sugerida):
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


def analizar_y_elegir(api, selector_ia, disponibilidad):
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

    candidatos = [r for r in resultados if r['operable'] and r['señal'] != 'ESPERAR']
    candidatos.sort(key=lambda x: x['confianza'], reverse=True)

    print("\n" + "=" * 55)
    print("🎯 RANKING DE OPORTUNIDADES")
    print("=" * 55)

    if not candidatos:
        print("⏸️ Ningún activo muestra una señal clara en este momento.")
        if getattr(config, 'MODO_APRENDIZAJE', False):
            print("   ⚠️ MODO_APRENDIZAJE activo: se elegirá un activo al azar.\n")
            elegido = random.choice([r['activo'] for r in resultados if r['operable']] or config.ACTIVOS_DISPONIBLES)
            print(f"🤖 Activo elegido al azar: {elegido}\n")
            direccion_forzada = random.choice(['call', 'put'])
            print(f"🎲 Dirección aleatoria: {direccion_forzada.upper()}\n")
            return [elegido], direccion_forzada
        return config.ACTIVOS_DISPONIBLES, None

    for i, r in enumerate(candidatos, 1):
        print(
            f"  {i}. {r['activo']} → {r['señal']} "
            f"(confianza {r['confianza']*100:.0f}%) | {r['regimen']}"
        )

    print(f"  {len(candidatos)+1}. 🤖 Dejar que el bot elija automáticamente el mejor")
    print(f"  {len(candidatos)+2}. 👀 Vigilar todos los activos sin operar aún")

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
                print(f"🤖 El bot operará automáticamente: {elegido}\n")
                return [elegido], candidatos[0]['señal'].lower()

            elif idx == len(candidatos) + 1:
                print("👀 Modo vigilancia: se analizarán todos sin operar.\n")
                return config.ACTIVOS_DISPONIBLES, None

            else:
                print("❌ Número fuera de rango.")
        except ValueError:
            print("❌ Ingresa solo un número.")


def main():
    verificar_dependencias()

    if not config.EMAIL or not config.PASSWORD:
        print("\n❌ Faltan credenciales.")
        sys.exit(1)

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

    disponibilidad = DisponibilidadInstrumentos(
        api,
        config.ACTIVOS_DISPONIBLES,
        cache_segundos=config.CACHE_DISPONIBILIDAD_SEGUNDOS,
    )

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
    if getattr(config, 'MODO_APRENDIZAJE', False):
        print(f"🎓 MODO APRENDIZAJE ACTIVADO — la IA aprenderá rápido (solo DEMO)")
    if getattr(config, 'IGNORAR_DISPONIBILIDAD', False):
        print(f"⚡ IGNORAR_DISPONIBILIDAD activo — el bot intentará operar aunque la API no lo reporte")
    print(f"⏱️ Vela: {config.TIEMPO_VELA}s | Duración op: {config.DURACION} min")
    print(f"🧠 Estrategias IA: {list(selector_ia.estrategias.keys())}")
    print(f"🎯 Confianza mínima: {config.MIN_CONFIANZA_IA*100:.0f}%")
    print("⏳ Comenzando en 5 segundos... (Ctrl+C para detener)")
    time.sleep(5)

    detenido_por_limite = False
    ignorar_disp = getattr(config, 'IGNORAR_DISPONIBILIDAD', False)

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

            # =========================================================
            # FILTRO DE OPORTUNIDADES
            # =========================================================
            if getattr(config, 'MODO_APRENDIZAJE', False):
                oportunidades = [
                    a for a in analisis_activos
                    if not gestor_operaciones.esta_ocupado(a['activo'])
                    and (ignorar_disp or a['activo'] in activos_operables)
                ]
                for a in oportunidades:
                    if a['señal'] == 'ESPERAR':
                        a['señal'] = random.choice(['CALL', 'PUT'])
                        a['confianza'] = 1.0
            else:
                oportunidades = [
                    a for a in analisis_activos
                    if a['señal'] in ('CALL', 'PUT')
                    and a['confianza'] >= config.MIN_CONFIANZA_IA
                    and not gestor_operaciones.esta_ocupado(a['activo'])
                    and (ignorar_disp or a['activo'] in activos_operables)
                ]

            bloqueadas_por_mercado = [
                a for a in analisis_activos
                if a['señal'] in ('CALL', 'PUT')
                and a['confianza'] >= config.MIN_CONFIANZA_IA
                and not ignorar_disp
                and a['activo'] not in activos_operables
            ]
            for b in bloqueadas_por_mercado:
                print(
                    f"⏭️ {b['activo']}: señal {b['señal']} "
                    f"({b['confianza']*100:.0f}%) válida pero el mercado "
                    f"no está confirmado como operable. Se omite."
                )

            if oportunidades:
                oportunidades.sort(key=lambda x: x['confianza'], reverse=True)

                if contador.limite_perdida_alcanzado():
                    print("⚠️ Límite de pérdida diaria alcanzado.")
                    detenido_por_limite = True
                elif contador.limite_operaciones_alcanzado():
                    print("⚠️ Límite de operaciones diarias alcanzado.")
                    detenido_por_limite = True
                else:
                    for op in oportunidades:
                        if (contador.limite_operaciones_alcanzado()
                                or contador.limite_perdida_alcanzado()):
                            break

                        if direccion_forzada:
                            direccion = direccion_forzada
                            print(f"\n🎯 OPORTUNIDAD: {op['activo']} → {direccion.upper()} (forzada por ti)")
                        else:
                            direccion = "call" if op['señal'] == "CALL" else "put"
                            print(f"\n🎯 OPORTUNIDAD: {op['activo']} → {op['señal']} (confianza {op['confianza']*100:.0f}%)")

                        contador.registrar_operacion_iniciada()
                        print(f"📤 Lanzando operación: {op['activo']} {direccion.upper()}")

                        gestor_operaciones.lanzar_operacion(
                            op['activo'], direccion, op['precio'],
                            op['regimen'], op['estrategia']
                        )
            else:
                print(f"⏸️ Sin oportunidades nuevas (confianza mínima {config.MIN_CONFIANZA_IA*100:.0f}%)")

            if detenido_por_limite:
                print("🧭 Esperando a que cierren las operaciones abiertas...")
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
            print("🧭 Esperando a que cierren las operaciones en curso...")
            try:
                gestor_operaciones.esperar_pendientes()
            except KeyboardInterrupt:
                print("⚠️ Saliendo sin esperar.")
            print(f"\n🧠 IA aprendió {len(selector_ia.rendimiento)} combinaciones régimen/estrategia")
            break
        except Exception as e:
            print(f"❌ ERROR: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()